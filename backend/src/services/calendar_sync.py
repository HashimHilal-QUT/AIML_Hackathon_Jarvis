"""Calendar sync service.

Fetches the user's saved QUT Timetable + Canvas ICS feeds, parses each via the
existing `routes/calendar_parser.py` helpers, and replaces the user's events
for that source in Supabase.

Strategy: delete-then-insert per source. Simpler than upserting on a unique
index (which the `events` table does not have) and safe because manual events
use source='manual' and are never touched here.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from src.routes.calendar_parser import (
    fetch_ics_from_url,
    parse_ics,
    validate_ics_url,
)
from src.supabase_client import get_supabase


# Map profile column -> (source label, event_type)
FEED_SOURCES: dict[str, tuple[str, str]] = {
    "qut_timetable_ics_url": ("qut_timetable", "class"),
    "qut_canvas_ics_url": ("qut_canvas", "assignment"),
    "outlook_ics_url": ("outlook", "event"),
    "google_ics_url": ("google", "event"),
}


def _event_row(
    user_id: str,
    parsed: dict[str, Any],
    source: str,
    source_url: str,
    event_type: str,
) -> dict[str, Any]:
    """Map a parsed ICS event dict to an `events` table row."""
    color_map = {
        "class": "#00d4ff",
        "assignment": "#ff9500",
        "event": "#534AB7",
    }
    return {
        "user_id": user_id,
        "title": parsed.get("title") or "Untitled",
        "description": parsed.get("description") or None,
        "location": parsed.get("location") or None,
        "start_date": parsed.get("start"),
        "end_date": parsed.get("end"),
        "is_all_day": bool(parsed.get("all_day")),
        "event_type": event_type,
        "color": color_map.get(event_type, "#534AB7"),
        "source": source,
        "source_url": source_url,
        "ics_uid": parsed.get("id") or None,
    }


def ensure_profile_row(user_id: str) -> None:
    """Make sure a `profiles` row exists for the given user.

    New Supabase Auth signups get a row in `auth.users` but NOT in `public.profiles`.
    Every write to `events` needs a matching profiles.id (FK), so we lazily
    upsert an empty profile on the first admin call.
    """
    sb = get_supabase()
    sb.table("profiles").upsert({"id": user_id}, on_conflict="id").execute()


def sync_one_feed(user_id: str, ics_url: str, source: str, event_type: str) -> int:
    """Fetch, parse, and replace events from a single ICS URL.

    Returns number of rows inserted.
    """
    validate_ics_url(ics_url)
    content = fetch_ics_from_url(ics_url)
    parsed_envelope = parse_ics(content, filename=f"{source}.ics")
    parsed_events = parsed_envelope["jarvis_calendar_data"]["events"]

    sb = get_supabase()

    # Clear out the previous sync for this user+source (but never manual events).
    sb.table("events").delete().eq("user_id", user_id).eq("source", source).execute()

    if not parsed_events:
        return 0

    rows: list[dict[str, Any]] = []
    seen_uids: set[str] = set()
    for ev in parsed_events:
        if not ev.get("start"):
            # Skip events with no start date — can't render on calendar
            continue
        row = _event_row(user_id, ev, source, ics_url, event_type)
        # Dedupe inside this single feed (rare, but ICS files sometimes repeat)
        uid_key = row["ics_uid"] or f'{row["title"]}-{row["start_date"]}'
        if uid_key in seen_uids:
            continue
        seen_uids.add(uid_key)
        rows.append(row)

    if not rows:
        return 0

    sb.table("events").insert(rows).execute()
    return len(rows)


def sync_user_feeds(user_id: str) -> dict[str, Any]:
    """Read the user's saved feed URLs from profiles and sync each non-empty one.

    Returns a dict like:
        {
            "synced": {"qut_timetable": 12, "qut_canvas": 5},
            "errors": [{"source": "outlook", "error": "..."}],
            "last_calendar_sync_at": "2026-04-11T..."
        }
    """
    ensure_profile_row(user_id)
    sb = get_supabase()

    profile_resp = (
        sb.table("profiles")
        .select(
            "qut_timetable_ics_url,qut_canvas_ics_url,outlook_ics_url,google_ics_url"
        )
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    profile = (profile_resp.data if profile_resp else {}) or {}

    synced: dict[str, int] = {}
    errors: list[dict[str, str]] = []

    for column, (source, event_type) in FEED_SOURCES.items():
        ics_url = profile.get(column)
        if not ics_url:
            continue
        try:
            count = sync_one_feed(user_id, ics_url, source, event_type)
            synced[source] = count
        except HTTPException as exc:
            errors.append({"source": source, "error": str(exc.detail)})
        except Exception as exc:  # pragma: no cover — defensive
            errors.append({"source": source, "error": f"{type(exc).__name__}: {exc}"})

    now_iso = datetime.now(timezone.utc).isoformat()
    sb.table("profiles").update({"last_calendar_sync_at": now_iso}).eq(
        "id", user_id
    ).execute()

    return {
        "synced": synced,
        "errors": errors,
        "last_calendar_sync_at": now_iso,
    }
