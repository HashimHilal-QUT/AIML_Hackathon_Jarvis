"""Chat API with Claude and calendar tools.

Implements the full two-turn (N-turn) Claude tool-use loop:
    user → Claude → tool_use blocks → backend runs tools → tool_result blocks
    → Claude → final text

Calendar tools are wired to the same Supabase data the /event page reads and
writes, scoped to the authenticated user. If the caller does not send a
Bearer token, calendar tools return a "not signed in" result instead of
fabricating data, so Claude can tell the user to sign in rather than
hallucinating events.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.auth import get_current_user_id
from src.routes.meal_buddy import build_meal_buddy_context
from src.routes.subjects import (
    build_subject_context,
    build_subjects_summary,
    resolve_subject_id,
    search_subject_materials,
)
from src.services.calendar_sync import ensure_profile_row, sync_user_feeds
from src.supabase_client import get_supabase

load_dotenv()

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    history: list = []
    subject_id: str | None = None


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in environment")

ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
MAX_TOOL_TURNS = 5

# Claude tool definitions
TOOLS = [
    {
        "name": "sync_calendar_feed",
        "description": (
            "Re-sync the user's saved QUT Timetable and Canvas calendar feeds "
            "into the events table. Call this when the user explicitly asks to "
            "refresh, resync, or update their calendar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "get_upcoming_events",
        "description": (
            "Get the user's upcoming calendar events from their real synced "
            "calendar (QUT classes, Canvas assignments, and any manual events). "
            "Use this for ANY question about the user's schedule, classes, "
            "assignments, free time, or 'what do I have'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "How many days ahead to look (default 7, max 60).",
                },
                "event_type": {
                    "type": "string",
                    "enum": ["class", "assignment", "event", "any"],
                    "description": "Filter by event type. Default 'any'.",
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "create_event",
        "description": "Create a new manual calendar event for the user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "start": {
                    "type": "string",
                    "description": "ISO 8601 datetime with timezone, e.g. 2026-04-13T15:00:00+10:00",
                },
                "end": {"type": "string", "description": "ISO 8601 end datetime (optional)"},
                "description": {"type": "string"},
                "location": {"type": "string"},
            },
            "required": ["title", "start"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cancel_event",
        "description": "Delete an event from the user's calendar by id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
            },
            "required": ["event_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "set_reminder",
        "description": "Set a reminder for an event (not yet wired to DB — returns a stub).",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "minutes_before": {"type": "integer"},
            },
            "required": ["event_id", "minutes_before"],
        },
    },
    {
        "name": "get_campus_directions",
        "description": "Get rough directions to a QUT campus location (stub).",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
            },
            "required": ["location"],
        },
    },
    {
        "name": "get_cafeteria_menu",
        "description": "Get today's cafeteria menu (stub).",
        "input_schema": {"type": "object", "properties": {}},
    },
    # -------- Meal & Friends tools --------
    {
        "name": "list_eateries",
        "description": (
            "Browse the restaurant catalogue. Use this when the user asks for "
            "food recommendations, trending places, or restaurants by cuisine."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cuisine": {
                    "type": "string",
                    "description": "Filter by cuisine e.g. italian, thai, korean",
                },
                "trending_only": {
                    "type": "boolean",
                    "description": "If true, return only the hot list.",
                },
                "limit": {"type": "integer"},
            },
        },
    },
    {
        "name": "get_meal_preferences",
        "description": (
            "Fetch the user's dining preferences (cuisines, budget, dietary flags). "
            "Use this for any food-related personalization."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "update_meal_preferences",
        "description": (
            "Update the user's dining preferences. Call when the user says "
            "things like 'I'm vegetarian' or 'I prefer cheap eats'."
        ),
        "input_schema": {
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
        "name": "get_meal_picks",
        "description": "Get the user's top 3 curated restaurant picks.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "add_meal_pick",
        "description": (
            "Add a restaurant to the user's top picks (max 3). Accepts either "
            "an eatery_id OR an eatery_name (we'll resolve the name to an id)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "eatery_id": {"type": "string"},
                "eatery_name": {"type": "string"},
            },
        },
    },
    {
        "name": "remove_meal_pick",
        "description": "Remove a restaurant from the user's top picks.",
        "input_schema": {
            "type": "object",
            "properties": {"eatery_id": {"type": "string"}},
            "required": ["eatery_id"],
        },
    },
    {
        "name": "set_dining_availability",
        "description": (
            "Mark the user as available for lunch or dinner on a specific date "
            "and time slot (e.g. '1230' for 12:30 PM). Use this when the user "
            "says things like 'I'm free for lunch on Wednesday'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "slot_date": {"type": "string", "description": "YYYY-MM-DD"},
                "slot_time": {
                    "type": "string",
                    "description": "4-digit slot, e.g. 1130, 1230, 1800, 1900",
                },
                "meal_type": {
                    "type": "string",
                    "enum": ["breakfast", "lunch", "dinner"],
                },
            },
            "required": ["slot_date", "slot_time", "meal_type"],
        },
    },
    {
        "name": "list_meal_matches",
        "description": (
            "List the user's dining matches. Filter by status if needed "
            "(proposed / accepted / declined / completed)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["proposed", "accepted", "declined", "completed", "cancelled"],
                }
            },
        },
    },
    {
        "name": "respond_to_meal_match",
        "description": "Accept or decline a pending meal match by id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "match_id": {"type": "string"},
                "response": {"type": "string", "enum": ["accepted", "declined"]},
            },
            "required": ["match_id", "response"],
        },
    },
    # -------- Subjects / course helper tools --------
    {
        "name": "list_subjects",
        "description": (
            "List every subject/course the student has in Jarvis with their "
            "material counts. Use this when the user asks about their courses "
            "in general, or when you need the id of a subject before calling "
            "get_subject_context."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_subject_context",
        "description": (
            "Return the full dossier for one subject — its syllabus, modules, "
            "assignments, rubrics, notes, and extracted file text. Accepts "
            "either the subject_id (UUID) OR a human string like 'IFN680' or "
            "'Machine Learning'. Call this when the student asks detailed "
            "questions about a specific course."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "subject_id": {"type": "string"},
                "subject_name": {
                    "type": "string",
                    "description": "Fuzzy match on name or code when subject_id is unknown.",
                },
            },
        },
    },
    {
        "name": "search_subject_materials",
        "description": (
            "Keyword search across all the student's uploaded course materials "
            "(syllabi, modules, rubrics, assignments, notes, and extracted "
            "PDF/image text). Returns up to 5 snippets with context. Use this "
            "for questions like 'where does my syllabus mention attendance?' "
            "or 'what does the rubric say about references?'"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "subject_name": {
                    "type": "string",
                    "description": "Optional: scope the search to one subject by name or code.",
                },
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "create_subject",
        "description": (
            "Create a new subject/course for the student. Use this when the "
            "user says something like 'I'm enrolled in a new course called X' "
            "or 'add IFN711 to my subjects'."
        ),
        "input_schema": {
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
        "name": "add_subject_material_text",
        "description": (
            "Add a text material to a subject — syllabus text, module notes, "
            "rubric, assignment brief, or personal note. Use this when the "
            "user dictates or pastes content. Accepts subject_id OR subject_name."
        ),
        "input_schema": {
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

SYSTEM_PROMPT = (
    "You are JARVIS, a helpful calendar-aware assistant for a QUT university "
    "student. Be concise and natural — two or three sentences is ideal for "
    "spoken responses. Use Brisbane timezone (AEST/AEDT) for all times. When "
    "the user asks ANYTHING about their schedule, classes, assignments, or "
    "free time, call the get_upcoming_events tool first and base your answer "
    "on the real data it returns. Never invent events. If the tool returns "
    "{\"error\": \"not_signed_in\"}, tell the user they need to sign in on "
    "the admin panel first."
)


# ---------------------------------------------------------------------------
# Tool implementations (wired to real Supabase, scoped to user_id)
# ---------------------------------------------------------------------------


async def _get_upcoming_events(user_id: str | None, tool_input: dict) -> dict:
    if not user_id:
        return {
            "error": "not_signed_in",
            "message": "User must sign in on the admin panel before calendar data is available.",
        }
    days = int(tool_input.get("days") or 7)
    days = max(1, min(days, 60))
    event_type = tool_input.get("event_type") or "any"

    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)

    sb = get_supabase()
    query = (
        sb.table("events")
        .select(
            "id,title,description,start_date,end_date,location,event_type,source"
        )
        .eq("user_id", user_id)
        .gte("start_date", now.isoformat())
        .lte("start_date", end.isoformat())
        .order("start_date")
        .limit(100)
    )
    if event_type != "any":
        query = query.eq("event_type", event_type)
    resp = query.execute()
    rows = resp.data or []

    # Claude does better with compact, human-readable shapes.
    return {
        "count": len(rows),
        "window_days": days,
        "events": [
            {
                "id": r["id"],
                "title": r["title"],
                "start": r["start_date"],
                "end": r.get("end_date"),
                "location": r.get("location"),
                "event_type": r.get("event_type"),
                "source": r.get("source"),
            }
            for r in rows
        ],
    }


async def _create_event(user_id: str | None, tool_input: dict) -> dict:
    if not user_id:
        return {"error": "not_signed_in"}
    title = (tool_input.get("title") or "").strip()
    start = tool_input.get("start")
    if not title or not start:
        return {"error": "invalid_input", "detail": "title and start are required"}

    ensure_profile_row(user_id)
    sb = get_supabase()
    row = {
        "user_id": user_id,
        "title": title,
        "description": tool_input.get("description"),
        "location": tool_input.get("location"),
        "start_date": start,
        "end_date": tool_input.get("end"),
        "source": "manual",
        "event_type": "event",
    }
    resp = sb.table("events").insert(row).execute()
    created = (resp.data or [None])[0]
    return {"status": "created", "event": created}


async def _cancel_event(user_id: str | None, tool_input: dict) -> dict:
    if not user_id:
        return {"error": "not_signed_in"}
    event_id = tool_input.get("event_id")
    if not event_id:
        return {"error": "invalid_input", "detail": "event_id is required"}
    sb = get_supabase()
    sb.table("events").delete().eq("id", event_id).eq("user_id", user_id).execute()
    return {"status": "deleted", "event_id": event_id}


async def _sync_calendar(user_id: str | None, tool_input: dict) -> dict:
    if not user_id:
        return {"error": "not_signed_in"}
    try:
        result = sync_user_feeds(user_id)
    except Exception as exc:  # pragma: no cover
        return {"error": "sync_failed", "detail": f"{type(exc).__name__}: {exc}"}
    return {"status": "synced", **result}


async def _set_reminder(user_id: str | None, tool_input: dict) -> dict:
    return {
        "status": "stubbed",
        "message": (
            f"Reminder requested for event {tool_input.get('event_id')} "
            f"{tool_input.get('minutes_before')} minutes before (not yet persisted)."
        ),
    }


async def _get_directions(user_id: str | None, tool_input: dict) -> dict:
    return {
        "status": "stubbed",
        "location": tool_input.get("location"),
        "directions": "Head to the main entrance and follow the signage.",
    }


async def _get_cafeteria_menu(user_id: str | None, tool_input: dict) -> dict:
    return {
        "status": "stubbed",
        "menu": ["Chicken Burrito", "Vegetarian Wrap", "Pasta", "Sushi"],
    }


# -------- Meal & Friends tool handlers --------


def _resolve_eatery_id(sb, eatery_id: str | None, eatery_name: str | None) -> str | None:
    if eatery_id:
        return eatery_id
    if not eatery_name:
        return None
    try:
        resp = (
            sb.table("eateries")
            .select("id")
            .ilike("name", f"%{eatery_name}%")
            .limit(1)
            .execute()
        )
        data = resp.data or []
        return data[0]["id"] if data else None
    except Exception:
        return None


async def _list_eateries_tool(user_id: str | None, tool_input: dict) -> dict:
    sb = get_supabase()
    try:
        query = sb.table("eateries").select("id,name,cuisine,blurb,price_tier,rating,tags,is_trending,trending_rank")
        if tool_input.get("cuisine"):
            query = query.eq("cuisine", tool_input["cuisine"])
        if tool_input.get("trending_only"):
            query = query.eq("is_trending", True).order("trending_rank")
        else:
            query = query.order("rating", desc=True)
        query = query.limit(int(tool_input.get("limit") or 15))
        resp = query.execute()
        return {"count": len(resp.data or []), "eateries": resp.data or []}
    except Exception as exc:
        return {"error": "list_failed", "detail": str(exc)[:200]}


async def _get_meal_prefs(user_id: str | None, tool_input: dict) -> dict:
    if not user_id:
        return {"error": "not_signed_in"}
    sb = get_supabase()
    try:
        resp = (
            sb.table("dining_preferences")
            .select("*")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        return (resp.data if resp else None) or {
            "cuisines": [],
            "budget_amount": 35,
            "budget_tier": "$$",
            "dietary_flags": [],
        }
    except Exception as exc:
        return {"error": "fetch_failed", "detail": str(exc)[:200]}


async def _update_meal_prefs(user_id: str | None, tool_input: dict) -> dict:
    if not user_id:
        return {"error": "not_signed_in"}
    sb = get_supabase()
    payload: dict[str, Any] = {"user_id": user_id}
    for field in ("cuisines", "budget_amount", "budget_tier", "dietary_flags"):
        if field in tool_input and tool_input[field] is not None:
            payload[field] = tool_input[field]
    try:
        sb.table("dining_preferences").upsert(payload, on_conflict="user_id").execute()
        return await _get_meal_prefs(user_id, {})
    except Exception as exc:
        return {"error": "update_failed", "detail": str(exc)[:200]}


async def _get_meal_picks(user_id: str | None, tool_input: dict) -> dict:
    if not user_id:
        return {"error": "not_signed_in"}
    sb = get_supabase()
    try:
        resp = (
            sb.table("dining_picks")
            .select("id,priority,eateries(name,cuisine,price_tier,rating)")
            .eq("user_id", user_id)
            .execute()
        )
        return {"picks": resp.data or []}
    except Exception as exc:
        return {"error": "fetch_failed", "detail": str(exc)[:200]}


async def _add_meal_pick(user_id: str | None, tool_input: dict) -> dict:
    if not user_id:
        return {"error": "not_signed_in"}
    sb = get_supabase()
    eatery_id = _resolve_eatery_id(sb, tool_input.get("eatery_id"), tool_input.get("eatery_name"))
    if not eatery_id:
        return {"error": "eatery_not_found"}
    try:
        existing = sb.table("dining_picks").select("id").eq("user_id", user_id).execute()
        if len(existing.data or []) >= 3:
            return {"error": "limit_reached", "message": "You already have 3 picks. Remove one first."}
        sb.table("dining_picks").insert({"user_id": user_id, "eatery_id": eatery_id}).execute()
        return {"status": "added", "eatery_id": eatery_id}
    except Exception as exc:
        return {"error": "add_failed", "detail": str(exc)[:200]}


async def _remove_meal_pick(user_id: str | None, tool_input: dict) -> dict:
    if not user_id:
        return {"error": "not_signed_in"}
    sb = get_supabase()
    try:
        sb.table("dining_picks").delete().eq("user_id", user_id).eq(
            "eatery_id", tool_input["eatery_id"]
        ).execute()
        return {"status": "removed"}
    except Exception as exc:
        return {"error": "remove_failed", "detail": str(exc)[:200]}


async def _set_dining_availability(user_id: str | None, tool_input: dict) -> dict:
    if not user_id:
        return {"error": "not_signed_in"}
    sb = get_supabase()
    try:
        sb.table("dining_availability").upsert(
            {
                "user_id": user_id,
                "slot_date": tool_input["slot_date"],
                "slot_time": tool_input["slot_time"],
                "meal_type": tool_input["meal_type"],
            },
            on_conflict="user_id,slot_date,slot_time",
        ).execute()
        return {"status": "set", **tool_input}
    except Exception as exc:
        return {"error": "set_failed", "detail": str(exc)[:200]}


async def _list_meal_matches(user_id: str | None, tool_input: dict) -> dict:
    if not user_id:
        return {"error": "not_signed_in"}
    sb = get_supabase()
    try:
        query = (
            sb.table("meal_matches")
            .select("id,scheduled_at,status,compatibility_score,eateries(name,cuisine)")
            .or_(f"user_a_id.eq.{user_id},user_b_id.eq.{user_id}")
            .order("scheduled_at")
        )
        if tool_input.get("status"):
            query = query.eq("status", tool_input["status"])
        resp = query.execute()
        return {"count": len(resp.data or []), "matches": resp.data or []}
    except Exception as exc:
        return {"error": "fetch_failed", "detail": str(exc)[:200]}


# -------- Subject tool handlers --------


async def _list_subjects_tool(user_id: str | None, tool_input: dict) -> dict:
    if not user_id:
        return {"error": "not_signed_in"}
    sb = get_supabase()
    try:
        resp = (
            sb.table("subjects")
            .select("id,name,code,term,description")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return {"count": len(resp.data or []), "subjects": resp.data or []}
    except Exception as exc:
        return {"error": "fetch_failed", "detail": str(exc)[:200]}


async def _get_subject_context_tool(user_id: str | None, tool_input: dict) -> dict:
    if not user_id:
        return {"error": "not_signed_in"}
    subject_id = tool_input.get("subject_id")
    if not subject_id and tool_input.get("subject_name"):
        subject_id = resolve_subject_id(user_id, tool_input["subject_name"])
    if not subject_id:
        return {"error": "subject_not_found"}
    dossier = build_subject_context(subject_id, user_id)
    if not dossier:
        return {"error": "subject_not_found_or_empty", "subject_id": subject_id}
    return {"subject_id": subject_id, "dossier": dossier}


async def _search_subject_materials_tool(user_id: str | None, tool_input: dict) -> dict:
    if not user_id:
        return {"error": "not_signed_in"}
    query = tool_input.get("query") or ""
    limit = int(tool_input.get("limit") or 5)
    limit = max(1, min(limit, 15))
    subject_id = None
    if tool_input.get("subject_name"):
        subject_id = resolve_subject_id(user_id, tool_input["subject_name"])
    results = search_subject_materials(user_id, query, subject_id=subject_id, limit=limit)
    return {"count": len(results), "matches": results}


async def _create_subject_tool(user_id: str | None, tool_input: dict) -> dict:
    if not user_id:
        return {"error": "not_signed_in"}
    name = (tool_input.get("name") or "").strip()
    if not name:
        return {"error": "missing_name"}
    ensure_profile_row(user_id)
    sb = get_supabase()
    row = {
        "user_id": user_id,
        "name": name,
        "code": tool_input.get("code"),
        "term": tool_input.get("term"),
        "description": tool_input.get("description"),
    }
    # Drop None values so defaults apply
    row = {k: v for k, v in row.items() if v is not None}
    try:
        resp = sb.table("subjects").insert(row).execute()
    except Exception as exc:
        return {"error": "create_failed", "detail": str(exc)[:200]}
    created = (resp.data or [None])[0]
    if not created:
        return {"error": "insert_returned_nothing"}
    return {"status": "created", "subject": created}


async def _add_subject_material_text_tool(user_id: str | None, tool_input: dict) -> dict:
    if not user_id:
        return {"error": "not_signed_in"}
    content = (tool_input.get("content_text") or "").strip()
    kind = tool_input.get("kind")
    if not content:
        return {"error": "empty_content"}
    if kind not in {"syllabus", "module", "rubric", "assignment", "file", "note"}:
        return {"error": "bad_kind", "allowed": ["syllabus", "module", "rubric", "assignment", "file", "note"]}

    subject_id = tool_input.get("subject_id")
    if not subject_id and tool_input.get("subject_name"):
        subject_id = resolve_subject_id(user_id, tool_input["subject_name"])
    if not subject_id:
        return {"error": "subject_not_found"}

    sb = get_supabase()
    row = {
        "subject_id": subject_id,
        "user_id": user_id,
        "kind": kind,
        "title": tool_input.get("title") or kind.capitalize(),
        "content_text": content,
        "metadata": {"added_via": "jarvis_chat"},
    }
    try:
        resp = sb.table("subject_materials").insert(row).execute()
    except Exception as exc:
        return {"error": "insert_failed", "detail": str(exc)[:200]}
    created = (resp.data or [None])[0]
    if not created:
        return {"error": "insert_returned_nothing"}
    return {"status": "added", "material_id": created.get("id"), "subject_id": subject_id, "kind": kind}


async def _respond_to_match(user_id: str | None, tool_input: dict) -> dict:
    if not user_id:
        return {"error": "not_signed_in"}
    sb = get_supabase()
    match_id = tool_input["match_id"]
    response = tool_input["response"]
    try:
        match_resp = (
            sb.table("meal_matches")
            .select("*")
            .eq("id", match_id)
            .maybe_single()
            .execute()
        )
        match = match_resp.data if match_resp else None
        if not match:
            return {"error": "not_found"}
        if user_id not in (match["user_a_id"], match["user_b_id"]):
            return {"error": "not_your_match"}
        field = "a_response" if match["user_a_id"] == user_id else "b_response"
        other = match.get("b_response" if field == "a_response" else "a_response")
        update: dict[str, Any] = {field: response}
        if response == "declined":
            update["status"] = "declined"
        elif response == "accepted" and other == "accepted":
            update["status"] = "accepted"
        sb.table("meal_matches").update(update).eq("id", match_id).execute()
        return {"status": "updated", **update}
    except Exception as exc:
        return {"error": "update_failed", "detail": str(exc)[:200]}


TOOL_HANDLERS = {
    "get_upcoming_events": _get_upcoming_events,
    "create_event": _create_event,
    "cancel_event": _cancel_event,
    "sync_calendar_feed": _sync_calendar,
    "set_reminder": _set_reminder,
    "get_campus_directions": _get_directions,
    "get_cafeteria_menu": _get_cafeteria_menu,
    # Meal & Friends
    "list_eateries": _list_eateries_tool,
    "get_meal_preferences": _get_meal_prefs,
    "update_meal_preferences": _update_meal_prefs,
    "get_meal_picks": _get_meal_picks,
    "add_meal_pick": _add_meal_pick,
    "remove_meal_pick": _remove_meal_pick,
    "set_dining_availability": _set_dining_availability,
    "list_meal_matches": _list_meal_matches,
    "respond_to_meal_match": _respond_to_match,
    # Subjects / course helper
    "list_subjects": _list_subjects_tool,
    "get_subject_context": _get_subject_context_tool,
    "search_subject_materials": _search_subject_materials_tool,
    "create_subject": _create_subject_tool,
    "add_subject_material_text": _add_subject_material_text_tool,
}


async def process_tool_call(user_id: str | None, tool_name: str, tool_input: dict) -> Any:
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {"error": "unknown_tool", "detail": tool_name}
    try:
        return await handler(user_id, tool_input)
    except Exception as exc:  # pragma: no cover
        return {"error": "tool_exception", "detail": f"{type(exc).__name__}: {exc}"}


# ---------------------------------------------------------------------------
# Auth (optional) — non-fatal if Bearer token is absent
# ---------------------------------------------------------------------------


async def _optional_user_id(authorization: str | None) -> str | None:
    if not authorization:
        return None
    try:
        return await get_current_user_id(authorization)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Chat endpoint — full multi-turn tool-use loop
# ---------------------------------------------------------------------------


@router.post("")
async def chat(
    request: ChatRequest,
    authorization: str | None = Header(default=None),
):
    user_id = await _optional_user_id(authorization)

    # Build the system prompt. Start with the global JARVIS prompt. Then:
    #  * Always append the user's meal buddy dossier (cheap + useful for
    #    any food / schedule question).
    #  * If the caller scoped the conversation to a subject, append that
    #    dossier too.
    # Claude treats these dossiers as ground truth for the questions they
    # cover and still calls tools for anything outside them.
    system_prompt = SYSTEM_PROMPT
    dossier_blocks: list[str] = []

    if user_id:
        try:
            meal_dossier = build_meal_buddy_context(user_id)
            if meal_dossier:
                dossier_blocks.append(meal_dossier)
        except Exception:
            pass

        # Always give Claude the short subject list so it knows what courses
        # the student has even when `subject_id` is not passed. For details,
        # it calls the get_subject_context tool.
        try:
            subjects_summary = build_subjects_summary(user_id)
            if subjects_summary:
                dossier_blocks.append(subjects_summary)
        except Exception:
            pass

    if request.subject_id and user_id:
        try:
            subject_dossier = build_subject_context(request.subject_id, user_id)
            if subject_dossier:
                dossier_blocks.append(
                    "The student is currently asking about a specific subject. "
                    "Treat the following dossier as the authoritative source of "
                    "truth for this course.\n\n" + subject_dossier
                )
        except Exception:
            pass

    if dossier_blocks:
        system_prompt = (
            SYSTEM_PROMPT + "\n\n---\n\n" + "\n\n---\n\n".join(dossier_blocks)
        )

    history = request.history or []
    # Accept "string" content from the frontend; normalise to Claude shape.
    messages: list[dict[str, Any]] = []
    for item in history:
        role = item.get("role")
        content = item.get("content")
        if role and content is not None:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": request.message})

    async def stream_response():
        accumulated_events: list[dict] = []
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                for turn in range(MAX_TOOL_TURNS):
                    response = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": ANTHROPIC_API_KEY,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json",
                        },
                        json={
                            "model": ANTHROPIC_MODEL,
                            "max_tokens": 1024,
                            "system": system_prompt,
                            "tools": TOOLS,
                            "messages": messages,
                        },
                    )

                    if response.status_code != 200:
                        try:
                            error_data = response.json()
                            error_msg = (
                                error_data.get("error", {}).get("message")
                                or str(error_data)
                            )
                        except Exception:
                            error_msg = response.text or "Anthropic API error"
                        yield f"data: {json.dumps({'type': 'error', 'text': error_msg})}\n\n"
                        return

                    result = response.json()
                    content_blocks = result.get("content", [])
                    stop_reason = result.get("stop_reason")

                    # Stream any text blocks from this turn immediately.
                    turn_text = ""
                    for block in content_blocks:
                        if block.get("type") == "text":
                            text = block.get("text", "") or ""
                            turn_text += text
                            if text:
                                yield f"data: {json.dumps({'type': 'delta', 'text': text})}\n\n"

                    # Collect tool_use blocks.
                    tool_uses = [b for b in content_blocks if b.get("type") == "tool_use"]

                    if not tool_uses or stop_reason != "tool_use":
                        # Final turn — no more tool calls. Done.
                        yield (
                            "data: "
                            + json.dumps(
                                {
                                    "type": "done",
                                    "fullText": turn_text,
                                    "events": accumulated_events,
                                }
                            )
                            + "\n\n"
                        )
                        return

                    # Add the assistant message (with text + tool_use blocks) to history.
                    messages.append({"role": "assistant", "content": content_blocks})

                    # Run each tool and build a single user message with tool_result blocks.
                    tool_result_blocks: list[dict] = []
                    for use in tool_uses:
                        tool_name = use.get("name") or ""
                        tool_input = use.get("input") or {}
                        tool_result = await process_tool_call(user_id, tool_name, tool_input)

                        # Capture events so the UI can render them side-by-side.
                        if tool_name == "get_upcoming_events" and isinstance(tool_result, dict):
                            evs = tool_result.get("events")
                            if isinstance(evs, list):
                                accumulated_events = evs

                        tool_result_blocks.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": use.get("id"),
                                "content": json.dumps(tool_result, default=str),
                            }
                        )

                    messages.append({"role": "user", "content": tool_result_blocks})
                    # Loop back for Claude's next turn.

                # Hit the safety cap.
                yield (
                    "data: "
                    + json.dumps(
                        {
                            "type": "done",
                            "fullText": "",
                            "events": accumulated_events,
                            "note": f"Hit MAX_TOOL_TURNS={MAX_TOOL_TURNS}.",
                        }
                    )
                    + "\n\n"
                )
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'text': str(exc)})}\n\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")
