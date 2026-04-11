"""Realtime voice service — creates OpenAI Realtime API client secrets.

The browser uses the returned short-lived client secret to open a WebRTC
(or WebSocket) connection DIRECTLY to OpenAI, so audio never passes through
our backend. That's the ~200ms round-trip vs 2-5s of the existing request/
response `/api/voice/stt` + `/api/voice` pipeline.

This module is deliberately dependency-light: it reads env vars ad-hoc with
os.getenv() (matching the rest of jarvis-recovered) and does not depend on
the `src.models` / `src.config` infrastructure that the upstream plan
assumed. That scaffolding can be added later without changing this file.

Tools: we attach a `tools` array to the session config so the model can call
`create_event` / `get_upcoming_events`. The browser handles the function-call
events on the data channel and executes them against our `/api/admin/events`
endpoints (see frontend/src/hooks/useRealtime.js). Arguments use the same
field names as `backend/src/routes/admin.py::EventCreate` so the frontend
can forward them with no translation.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from fastapi import HTTPException

# Project-root + backend paths
BACKEND_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = BACKEND_DIR / "config" / "openai_speech_to_speech.json"

DEFAULT_MODEL = "gpt-realtime"
DEFAULT_VOICE = "sage"
DEFAULT_INSTRUCTIONS = (
    "You are JARVIS, a calm and concise AI assistant for a QUT university student. "
    "Respond in short, natural sentences. Use Brisbane timezone (AEST/AEDT)."
)

REALTIME_CLIENT_SECRET_URL = "https://api.openai.com/v1/realtime/client_secrets"

# ---------------------------------------------------------------------------
# Tools attached to every Realtime session.
# Field names mirror backend/src/routes/admin.py::EventCreate so the browser
# can POST the function arguments directly to /api/admin/events.
# ---------------------------------------------------------------------------
REALTIME_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "create_event",
        "description": (
            "Add an event to the user's calendar. Use this whenever the user "
            "asks to add, schedule, book, create, plan, or put something on "
            "their calendar. Always compute a concrete ISO 8601 datetime with "
            "Brisbane offset (+10:00) from the user's relative phrasing "
            "('tomorrow', 'next Monday', 'tonight at 8'). If the user does "
            "not specify an end time, default to 1 hour after the start."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short event title. Required.",
                },
                "start_date": {
                    "type": "string",
                    "description": (
                        "ISO 8601 start datetime WITH Brisbane offset, e.g. "
                        "2026-04-13T17:00:00+10:00. Required."
                    ),
                },
                "end_date": {
                    "type": "string",
                    "description": (
                        "ISO 8601 end datetime with Brisbane offset. Optional — "
                        "defaults to start + 1 hour if omitted."
                    ),
                },
                "description": {
                    "type": "string",
                    "description": "Optional longer description.",
                },
                "location": {
                    "type": "string",
                    "description": "Optional location / room.",
                },
            },
            "required": ["title", "start_date"],
        },
    },
    {
        "type": "function",
        "name": "get_upcoming_events",
        "description": (
            "List the user's upcoming calendar events. Call this when the user "
            "asks about their schedule, what they have on, what's next, or any "
            "question that requires knowing their real events."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "How many days ahead to look. Default 7, max 30.",
                },
            },
        },
    },
    {
        "type": "function",
        "name": "cancel_event",
        "description": (
            "Delete an event from the user's calendar by id. You should first "
            "call get_upcoming_events to find the correct event id, unless the "
            "user provided one explicitly."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
            },
            "required": ["event_id"],
        },
    },
    # -------- Meal & Friends tools --------
    {
        "type": "function",
        "name": "list_eateries",
        "description": (
            "Browse the restaurant catalogue for the Meal & Friends feature. "
            "Use this when the user asks for food recommendations, trending "
            "places, or restaurants by cuisine."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "cuisine": {"type": "string"},
                "trending_only": {"type": "boolean"},
                "limit": {"type": "integer"},
            },
        },
    },
    {
        "type": "function",
        "name": "get_meal_preferences",
        "description": "Fetch the user's dining preferences (cuisines, budget, dietary flags).",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "update_meal_preferences",
        "description": (
            "Update the user's dining preferences. Use when the user says "
            "'I'm vegan', 'I prefer cheap eats', etc."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "cuisines": {"type": "array", "items": {"type": "string"}},
                "budget_amount": {"type": "integer"},
                "budget_tier": {"type": "string", "enum": ["$", "$$", "$$$"]},
                "dietary_flags": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
    {
        "type": "function",
        "name": "add_meal_pick",
        "description": (
            "Add a restaurant to the user's top 3 Meal & Friends picks. "
            "Accepts either eatery_id or eatery_name (name will be fuzzy matched)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "eatery_id": {"type": "string"},
                "eatery_name": {"type": "string"},
            },
        },
    },
    {
        "type": "function",
        "name": "set_dining_availability",
        "description": (
            "Mark the user as free for lunch or dinner on a given date and time slot. "
            "Use when the user says 'I'm free Wednesday lunch'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "slot_date": {"type": "string"},
                "slot_time": {"type": "string"},
                "meal_type": {"type": "string", "enum": ["breakfast", "lunch", "dinner"]},
            },
            "required": ["slot_date", "slot_time", "meal_type"],
        },
    },
    {
        "type": "function",
        "name": "list_meal_matches",
        "description": "List the user's proposed / accepted / completed dining matches.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["proposed", "accepted", "declined", "completed", "cancelled"],
                },
            },
        },
    },
    {
        "type": "function",
        "name": "get_meal_picks",
        "description": "Get the user's current restaurant picks (up to 3). Use before add/remove.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "remove_meal_pick",
        "description": (
            "Remove a restaurant from the user's Meal & Friends picks. "
            "Accepts eatery_id OR eatery_name (we'll fuzzy match the name)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "eatery_id": {"type": "string"},
                "eatery_name": {"type": "string"},
            },
        },
    },
    {
        "type": "function",
        "name": "clear_dining_availability",
        "description": (
            "Clear a specific dining availability slot. Use this to undo a "
            "lunch or dinner slot the user previously marked."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "slot_date": {"type": "string", "description": "YYYY-MM-DD"},
                "slot_time": {"type": "string", "description": "4-digit slot, e.g. 1230, 1800"},
            },
            "required": ["slot_date", "slot_time"],
        },
    },
    {
        "type": "function",
        "name": "propose_meal_match",
        "description": (
            "Propose a dining match between the user and another profile. "
            "Requires the other user's id (from list_other_users_for_match) "
            "and an eatery_id. Scheduled datetime must be ISO 8601 with Brisbane offset."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "other_user_id": {"type": "string"},
                "eatery_id": {"type": "string"},
                "scheduled_at": {
                    "type": "string",
                    "description": "ISO 8601 with Brisbane offset, e.g. 2026-04-13T12:30:00+10:00",
                },
                "meal_type": {"type": "string", "enum": ["breakfast", "lunch", "dinner"]},
            },
            "required": ["other_user_id", "eatery_id", "scheduled_at", "meal_type"],
        },
    },
    {
        "type": "function",
        "name": "respond_to_meal_match",
        "description": "Accept or decline a pending meal match by id.",
        "parameters": {
            "type": "object",
            "properties": {
                "match_id": {"type": "string"},
                "response": {"type": "string", "enum": ["accepted", "declined"]},
            },
            "required": ["match_id", "response"],
        },
    },
    {
        "type": "function",
        "name": "list_other_users_for_match",
        "description": (
            "List other signed-up users that the current user can propose a "
            "meal match with. Use this before propose_meal_match when the "
            "user doesn't specify who by name."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
    # -------- Subjects / course helper tools --------
    {
        "type": "function",
        "name": "list_subjects",
        "description": (
            "List every subject/course the student has in Jarvis. Returns "
            "name, code, term, id, and material counts. Use this whenever "
            "the user asks about their courses in general."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "get_subject_context",
        "description": (
            "Return the full dossier for one subject (syllabus + modules + "
            "rubrics + assignments + extracted file text). Accepts either "
            "the subject_id UUID or a name/code string like 'IFN680' or "
            "'Machine Learning'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "subject_id": {"type": "string"},
                "subject_name": {"type": "string"},
            },
        },
    },
    {
        "type": "function",
        "name": "search_subject_materials",
        "description": (
            "Keyword search across all uploaded course materials. Use for "
            "questions like 'where does my syllabus mention attendance?'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "subject_name": {
                    "type": "string",
                    "description": "Optional: scope search to one subject.",
                },
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "create_subject",
        "description": (
            "Create a new subject/course. Use when the user says 'I'm "
            "taking a new class' or 'add IFN711 to my subjects'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "code": {"type": "string"},
                "term": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["name"],
        },
    },
    {
        "type": "function",
        "name": "add_subject_material_text",
        "description": (
            "Add a text material (syllabus / module / rubric / assignment / "
            "note) to a subject. Use when the user dictates or pastes "
            "content and wants Jarvis to remember it. Accepts subject_id "
            "or subject_name."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "subject_id": {"type": "string"},
                "subject_name": {"type": "string"},
                "kind": {
                    "type": "string",
                    "enum": ["syllabus", "module", "rubric", "assignment", "file", "note"],
                },
                "title": {"type": "string"},
                "content_text": {"type": "string"},
            },
            "required": ["kind", "content_text"],
        },
    },
]


def _brisbane_time_hint() -> str:
    """Return a one-line reference so the model can resolve 'tomorrow', etc.

    Brisbane (Australia/Brisbane) has NO DST, so the offset is always +10:00.
    Injected into the session instructions at mint time because OpenAI
    Realtime has no built-in concept of 'now' unless we tell it.
    """
    try:
        now = datetime.now(ZoneInfo("Australia/Brisbane"))
    except Exception:  # pragma: no cover — zoneinfo should always work on py 3.11
        return ""
    return (
        f"Current reference time: {now.strftime('%A, %d %B %Y at %I:%M %p')} "
        f"in Brisbane (AEST, {now.strftime('%z')}). "
        "When the user says 'today', 'tomorrow', 'tonight', 'next Monday', "
        "or any relative time, resolve against this exact moment. Always emit "
        "event datetimes as ISO 8601 with the Brisbane offset, for example "
        "2026-04-13T17:00:00+10:00."
    )


@lru_cache(maxsize=1)
def _load_template() -> dict[str, Any]:
    """Load the session template from disk once per process."""
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover — defensive
            raise HTTPException(
                500,
                f"openai_speech_to_speech.json is not valid JSON: {exc}",
            )
    return {}


def _meal_buddy_dossier_for_session(user_id: str | None) -> str:
    """Fetch a compact meal buddy dossier for session instructions.

    Defined as a late import so importing realtime_voice.py during module
    load doesn't create a circular dependency with routes/meal_buddy.py
    (which imports supabase_client, which reads env — all of which must
    already be initialised by the time main.py runs).
    """
    if not user_id:
        return ""
    try:
        from src.routes.meal_buddy import build_meal_buddy_context

        return build_meal_buddy_context(user_id, max_chars=6_000)
    except Exception:
        return ""


def _subjects_summary_for_session(user_id: str | None) -> str:
    """Fetch a lightweight subjects list for the Realtime session instructions.

    Late-imported for the same circular-import reason as the meal buddy helper.
    """
    if not user_id:
        return ""
    try:
        from src.routes.subjects import build_subjects_summary

        return build_subjects_summary(user_id, max_chars=2_500)
    except Exception:
        return ""


def build_session_config(
    model: str | None = None,
    voice: str | None = None,
    instructions: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Merge caller overrides > JSON template > env vars > defaults.

    Injects three context blocks into the session instructions at mint time:
      1. Current Brisbane time (so "tomorrow" resolves correctly).
      2. The user's Meal & Friends dossier (prefs / picks / availability /
         upcoming matches) when `user_id` is provided.
    Attaches our function-calling tool set so Sage can also mutate the state
    mid-conversation.
    """
    template = _load_template().get("session", {})
    merged_model = (
        model
        or template.get("model")
        or os.getenv("OPENAI_REALTIME_MODEL")
        or DEFAULT_MODEL
    )
    merged_voice = (
        voice
        or template.get("voice")
        or os.getenv("OPENAI_REALTIME_VOICE")
        or DEFAULT_VOICE
    )
    base_instructions = (
        instructions
        or template.get("instructions")
        or os.getenv("OPENAI_REALTIME_INSTRUCTIONS")
        or DEFAULT_INSTRUCTIONS
    )

    parts: list[str] = []
    time_hint = _brisbane_time_hint()
    if time_hint:
        parts.append(time_hint)
    parts.append(base_instructions)

    dossier = _meal_buddy_dossier_for_session(user_id)
    if dossier:
        parts.append(
            "Below is a live snapshot of the user's Meal & Friends state. "
            "Treat it as ground truth for food questions — but remember you "
            "can also call the meal-buddy tools to fetch fresh data or "
            "update it mid-conversation.\n\n" + dossier
        )

    subjects_summary = _subjects_summary_for_session(user_id)
    if subjects_summary:
        parts.append(
            "Below is the user's list of subjects/courses. When they ask "
            "anything course-related, use get_subject_context with the "
            "matching id for a full dossier, or search_subject_materials "
            "for keyword lookups. You can also add new materials with "
            "add_subject_material_text.\n\n" + subjects_summary
        )

    merged_instructions = "\n\n---\n\n".join(parts)

    return {
        "session": {
            "type": "realtime",
            "model": merged_model,
            "instructions": merged_instructions,
            "tools": REALTIME_TOOLS,
            "tool_choice": "auto",
            "audio": {
                "output": {
                    "voice": merged_voice,
                },
            },
        }
    }


def _safe_body(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text


def _extract_secret(data: dict[str, Any]) -> tuple[str, Any]:
    """Pull {client_secret.value, expires_at} out of the response.

    Handles both the nested shape {"client_secret": {"value": "...", ...}}
    and the flat shape some beta responses return.
    """
    client_secret = data.get("client_secret")
    if isinstance(client_secret, dict) and client_secret.get("value"):
        return client_secret["value"], client_secret.get("expires_at")
    if isinstance(client_secret, str):
        return client_secret, data.get("expires_at")
    if data.get("value"):
        return data["value"], data.get("expires_at")
    raise HTTPException(
        502,
        "OpenAI Realtime response did not include a client_secret value.",
    )


async def create_client_secret(
    model: str | None = None,
    voice: str | None = None,
    instructions: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Ask OpenAI for a short-lived Realtime client secret.

    When `user_id` is supplied, the user's Meal & Friends dossier is
    baked into the session instructions so Sage has immediate personal
    context without having to call tools for the first answer.

    Returns a dict ready to be serialised to the frontend:
        {
            "session_id": str | None,
            "client_secret": str,
            "expires_at": int | str | None,
            "model": str,
            "voice": str,
            "instructions": str,
        }
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(500, "OPENAI_API_KEY not configured in .env")

    session_payload = build_session_config(
        model=model, voice=voice, instructions=instructions, user_id=user_id
    )
    session_cfg = session_payload["session"]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                REALTIME_CLIENT_SECRET_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=session_payload,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Could not reach OpenAI Realtime API: {exc}")

    if response.is_error:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "OpenAI Realtime client secret request failed.",
                "status_code": response.status_code,
                "response": _safe_body(response),
                "request_payload": session_payload,
            },
        )

    data = response.json()
    secret_value, expires_at = _extract_secret(data)

    return {
        "session_id": data.get("id"),
        "client_secret": secret_value,
        "expires_at": expires_at,
        "model": session_cfg["model"],
        "voice": session_cfg["audio"]["output"]["voice"],
        "instructions": session_cfg["instructions"],
    }
