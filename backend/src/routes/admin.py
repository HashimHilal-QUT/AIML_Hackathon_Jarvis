"""Admin router — backs the Event admin page.

Router prefix is `/api/admin`. The Vite dev proxy in frontend/vite.config.js
forwards `/api/*` to the backend WITHOUT rewriting the prefix, so frontend
fetches `/api/admin/feeds` → backend receives `/api/admin/feeds` → matches
this router's `/feeds` endpoint.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.auth import get_current_user_id
from src.routes.calendar_parser import validate_ics_url
from src.services.calendar_sync import ensure_profile_row, sync_user_feeds
from src.supabase_client import get_supabase

router = APIRouter(prefix="/api/admin", tags=["admin"])


# -------- Schemas --------


class FeedsResponse(BaseModel):
    qut_timetable_ics_url: str | None = None
    qut_canvas_ics_url: str | None = None
    outlook_ics_url: str | None = None
    google_ics_url: str | None = None
    last_calendar_sync_at: str | None = None


class FeedsUpdate(BaseModel):
    qut_timetable_ics_url: str | None = None
    qut_canvas_ics_url: str | None = None
    outlook_ics_url: str | None = None
    google_ics_url: str | None = None


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    start_date: str
    end_date: str | None = None
    description: str | None = None
    location: str | None = None
    is_all_day: bool = False
    color: str | None = None
    event_type: str = "event"


# -------- Helpers --------


def _validate_url_or_null(url: str | None, label: str) -> None:
    if url is None or url == "":
        return
    try:
        validate_ics_url(url)
    except HTTPException as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{label}: {exc.detail}",
        )


# -------- Endpoints --------


@router.get("/feeds", response_model=FeedsResponse)
async def get_feeds(user_id: str = Depends(get_current_user_id)) -> FeedsResponse:
    """Return the user's saved ICS URLs + last sync timestamp.

    Lazily ensures a profiles row exists — this is the first call the Event
    page makes after login, so it's the right place to bootstrap.
    """
    ensure_profile_row(user_id)
    sb = get_supabase()
    resp = (
        sb.table("profiles")
        .select(
            "qut_timetable_ics_url,qut_canvas_ics_url,outlook_ics_url,"
            "google_ics_url,last_calendar_sync_at"
        )
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    data = (resp.data if resp else {}) or {}
    return FeedsResponse(**{k: data.get(k) for k in FeedsResponse.model_fields})


@router.put("/feeds", response_model=FeedsResponse)
async def put_feeds(
    body: FeedsUpdate,
    user_id: str = Depends(get_current_user_id),
) -> FeedsResponse:
    """Save or clear the user's ICS URLs. Validates each URL against the allowlist."""
    _validate_url_or_null(body.qut_timetable_ics_url, "QUT Timetable URL")
    _validate_url_or_null(body.qut_canvas_ics_url, "QUT Canvas URL")
    _validate_url_or_null(body.outlook_ics_url, "Outlook URL")
    _validate_url_or_null(body.google_ics_url, "Google URL")

    ensure_profile_row(user_id)
    update_payload: dict[str, Any] = {
        k: v for k, v in body.model_dump().items() if v is not None
    }
    # Allow clearing by sending empty string
    for k, v in body.model_dump().items():
        if v == "":
            update_payload[k] = None

    if update_payload:
        sb = get_supabase()
        sb.table("profiles").update(update_payload).eq("id", user_id).execute()

    return await get_feeds(user_id)


@router.post("/sync")
async def post_sync(user_id: str = Depends(get_current_user_id)) -> dict[str, Any]:
    """Fetch each saved ICS feed, parse it, and replace the user's events from that source."""
    result = sync_user_feeds(user_id)
    return result


@router.get("/events")
async def get_events(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=2000),
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Return events in [from, to) for the authenticated user, ordered by start."""
    now = datetime.now(timezone.utc)
    if from_ is None:
        from_ = (now - timedelta(days=7)).isoformat()
    if to is None:
        to = (now + timedelta(days=60)).isoformat()

    sb = get_supabase()
    resp = (
        sb.table("events")
        .select("*")
        .eq("user_id", user_id)
        .gte("start_date", from_)
        .lte("start_date", to)
        .order("start_date")
        .limit(limit)
        .execute()
    )
    return {"events": resp.data or [], "from": from_, "to": to}


@router.post("/events")
async def post_event(
    body: EventCreate,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Create a manual event for the user."""
    ensure_profile_row(user_id)
    sb = get_supabase()

    row = {
        "user_id": user_id,
        "title": body.title,
        "description": body.description,
        "location": body.location,
        "start_date": body.start_date,
        "end_date": body.end_date,
        "is_all_day": body.is_all_day,
        "event_type": body.event_type,
        "color": body.color or "#534AB7",
        "source": "manual",
    }
    resp = sb.table("events").insert(row).execute()
    created = (resp.data or [None])[0]
    if not created:
        raise HTTPException(500, "Failed to create event.")
    return created


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, str]:
    """Delete an event, scoped to the caller. Returns {'deleted': event_id}."""
    sb = get_supabase()
    sb.table("events").delete().eq("id", event_id).eq("user_id", user_id).execute()
    return {"deleted": event_id}


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "jarvis-admin"}
