"""Meal & Friends router — CRUD + matching primitives for the dining feature.

Router prefix is `/api/meal-buddy`. All endpoints require a signed-in user
via `get_current_user_id`. Queries that touch the new tables are wrapped in
try/except so the page can render a 412 `schema_not_ready` banner (same
pattern as subjects.py) when the user hasn't run the migration yet.

Tables:
  dining_preferences   — 1 row per user
  eateries             — shared catalogue, seeded from HTML mockups
  dining_picks         — user's top restaurant picks
  dining_availability  — weekly schedule slots
  meal_matches         — proposed/accepted/declined matches
  dining_stats         — cached aggregates

The matching primitives are intentionally simple for the hackathon:
  * `propose_match` creates a row with status='proposed' and auto-fills
    match_factors based on cuisine/dietary/schedule overlap.
  * `respond_to_match` sets a_response / b_response and promotes status
    to 'accepted' when both sides have accepted.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from src.auth import get_current_user_id
from src.services.calendar_sync import ensure_profile_row
from src.supabase_client import get_supabase

router = APIRouter(prefix="/api/meal-buddy", tags=["meal-buddy"])

SETUP_SQL_PATH = Path(__file__).resolve().parents[2] / "sql" / "002_meal_buddy.sql"

MealType = Literal["breakfast", "lunch", "dinner"]
BudgetTier = Literal["$", "$$", "$$$"]


def _is_missing_table_error(exc: Exception) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    return (
        "pgrst205" in text
        or "schema cache" in text
        or "does not exist" in text
        or "not find the table" in text
    )


def _schema_not_ready() -> HTTPException:
    return HTTPException(
        status_code=412,
        detail={
            "error": "schema_not_ready",
            "message": (
                "The Meal & Friends feature needs a one-time database "
                "migration. Run backend/sql/002_meal_buddy.sql in the "
                "Supabase SQL editor."
            ),
            "sql_path": "backend/sql/002_meal_buddy.sql",
            "setup_endpoint": "/api/meal-buddy/setup-sql",
            "dashboard_url": (
                "https://supabase.com/dashboard/project/"
                "eredinmxmdlgeqfmgtsm/sql/new"
            ),
        },
    )


@router.get("/setup-sql", response_class=PlainTextResponse)
async def get_setup_sql() -> str:
    try:
        return SETUP_SQL_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise HTTPException(500, "setup SQL file missing on server")


# ============================================================================
# Eateries seed data (from the HTML mockups)
# ============================================================================

SEED_EATERIES: list[dict[str, Any]] = [
    {
        "name": "Grill & Chill",
        "blurb": "Best Artisanal Burgers in Town",
        "cuisine": "american",
        "price_low": 14,
        "price_high": 24,
        "price_tier": "$$",
        "rating": 4.9,
        "location": "Downtown",
        "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuDrXXjD4yYo8nwSjGnnAaZS_CJCBaHxEmDhp1Q8xhXiW05UwSw1r7fZsK7Ow7iMkx4RSk2agaQ23zmVdBLiF8ntUQsGuoxu1WxGJ_qGSC1vsaudq7GbBWsQcjUp-qTaKRsvAUClygYvzeNZTiReoWA4ZTldnjzDZRT7FlFKlt2DKlkyMlCbY5K91RZbDEW5DZ67sw5UraDDJRR4OgijNl02_x0tcxrG9g1KqzbhHOOXKbyyIHt4snp4AzOAO7pl1YPZbFTyDxRHsiTd",
        "tags": ["burgers", "social_favorite"],
        "is_trending": True,
        "trending_rank": 1,
    },
    {
        "name": "Sushi Zen",
        "blurb": "Authentic Japanese Experience",
        "cuisine": "japanese",
        "price_low": 22,
        "price_high": 45,
        "price_tier": "$$",
        "rating": 4.8,
        "location": "South Bank",
        "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuDn2wqkNCBmJ622nfkSZE2u_SRvbCx9oB6mzdroSdw427_T8LU-R6KNYenoG_xWFrU83dMoqrCJGwK6CFi6248Gz629213_EFnFSU1T-q8L7MDfek4c1b8u4vj9s7oBKD92FfeN3_emO-xa7OSFxFYor8wgJ_jQLwMx1bFX7UcTAdXrQT0pRb-8GZ4pKfWY5si51939AZnS_ufva8sy8z_7gLXmpalTwywzfglUzEw_rRTYz2FdsTsM6tsDwxa4l-OyPelNMnyvT9NR",
        "tags": ["sushi", "most_shared"],
        "is_trending": True,
        "trending_rank": 2,
    },
    {
        "name": "Rustic Pizza",
        "blurb": "Traditional Wood-Fired Slices",
        "cuisine": "italian",
        "price_low": 15,
        "price_high": 28,
        "price_tier": "$$",
        "rating": 4.7,
        "location": "Fortitude Valley",
        "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuAyrsWZI8z8iRwLraxnhL97PPaInk3S52stol6sxEchNuEi5WpkZ5arCmoFd9LOkYLUNuNFU6YCLlEIU58zgw5uSSpPZVH4IQ6FxIGgwbZDGtrfV8bcX0G1xjmxA8hu5s-b-fvlVujg1eXeEP0Td1SDEyw8_4gGefi25-BwSUz4N1AmbtaKpzBiUr_-JxQbvK2xdctJ-1INgcEpg3cnJ1WpPUcMGNTTyDFeHb71cZutZP9BL7AVnyZL2pEuYOxGufX2jpvXCVnJvCni",
        "tags": ["pizza", "top_rated"],
        "is_trending": True,
        "trending_rank": 3,
    },
    {
        "name": "Pancake Palace",
        "blurb": "The best breakfast in the city",
        "cuisine": "american",
        "price_low": 12,
        "price_high": 20,
        "price_tier": "$",
        "rating": 4.5,
        "location": "West End",
        "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuAbS85he-vL6qoaMjlZsqPGJ56NI1vKBbIf8ij-Xj2x-LFfGNPGw0lnwWV2peDzAiKUrGmVZ7Ae8_y62LE3dvtiYvGOi0YJs_MozS2cLgaScqYVGZmJJUmnCO9P-pSdVsMX6rF6aT0Fj3ulnkeg0x302rX1oGLeadSC8YObF1mqSzj3Z19TMs0xNsgcAliya87abjm6fbA-pK8w3BvJjDDpaLPxkyR4RFthvpVSnFtH2ywaJRHUCimKfH_y_lOwkaicCJSsCeTKj_vv",
        "tags": ["breakfast", "brunch"],
        "is_trending": False,
    },
    {
        "name": "The Glass House",
        "blurb": "Elegant dining, refined taste",
        "cuisine": "french",
        "price_low": 40,
        "price_high": 80,
        "price_tier": "$$$",
        "rating": 4.6,
        "location": "CBD Tower",
        "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuDfrPCbLUljQrPrXybPlgSn3w-Ioqy8YoXqau1POeemL6ZNOy3XaZpHcbezemlMDP7wc7Z8a7dVzbLmJ9K5dR-itpyiy1elCHCo0n2rtfcCo15NSIW_HApY2jQezZrXC-w0mMXtfI970utxIIugIxZpDnPs0evhDTc0o6wmG5cg-QjO7GpfJ8VJNZJI0OjlruWvk2fSxHKI2883LulQEW3lcgJb3M9W6Ey_mkSpujEm7-J8f_projHDWjrr39MidHLgHlnxuC_P5dOT",
        "tags": ["fine_dining", "date_night"],
        "is_trending": False,
    },
    {
        "name": "Taco Fiesta",
        "blurb": "Fresh street-style tacos daily",
        "cuisine": "mexican",
        "price_low": 8,
        "price_high": 16,
        "price_tier": "$",
        "rating": 4.4,
        "location": "New Farm",
        "image_url": "https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
        "tags": ["casual", "quick_bite"],
        "is_trending": False,
    },
    {
        "name": "Seoul BBQ House",
        "blurb": "Korean BBQ done right",
        "cuisine": "korean",
        "price_low": 22,
        "price_high": 38,
        "price_tier": "$$",
        "rating": 4.7,
        "location": "South Bank",
        "image_url": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
        "tags": ["bbq", "group_friendly"],
        "is_trending": False,
    },
    {
        "name": "Bangkok Bowl",
        "blurb": "Bold Thai flavors, fast lunch",
        "cuisine": "thai",
        "price_low": 11,
        "price_high": 18,
        "price_tier": "$",
        "rating": 4.5,
        "location": "QUT Gardens Point",
        "image_url": "https://images.unsplash.com/photo-1559314809-0d155014e29e?auto=format&fit=crop&w=800&q=80",
        "tags": ["thai", "student_favorite"],
        "is_trending": False,
    },
    {
        "name": "Little Saigon Pho",
        "blurb": "Steam rising, broth for days",
        "cuisine": "vietnamese",
        "price_low": 10,
        "price_high": 17,
        "price_tier": "$",
        "rating": 4.6,
        "location": "Inala",
        "image_url": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?auto=format&fit=crop&w=800&q=80",
        "tags": ["pho", "authentic"],
        "is_trending": False,
    },
    {
        "name": "The Terrace Bistro",
        "blurb": "Italian terrace with a view",
        "cuisine": "italian",
        "price_low": 28,
        "price_high": 55,
        "price_tier": "$$",
        "rating": 4.8,
        "location": "Central Plaza, Level 3",
        "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuASvAHABzC2ho9oRy1hlBuyt0Qq-4eqhKddhiFkMfUHfGxzLPJVN7xcS4yTJ1YJxTOeCd7Gm2FUzljHn9g3SFAXSjJ4d-dueJ-GpCL7I_A4OqRqJbPUAqpCkQqhwJNkbl9najj0kzc2SG94xJ0wBeLvkK3Ki6T5l_3qFDXOGRiYosxryv6bHCe1p8Z8z-oNhIHsIKNFdKr5ipON-ycUoPJmnVI4jKNm0qieIBKaNA2-i79-K7ciWekNKLCp4fyEx0_cZKiK8",
        "tags": ["italian", "romantic"],
        "is_trending": False,
    },
]

_seeded_ref = {"done": False}


def _ensure_seed_eateries(sb) -> None:
    """Insert seed rows once per process if the eateries table is empty."""
    if _seeded_ref["done"]:
        return
    resp = sb.table("eateries").select("id").limit(1).execute()
    if not resp.data:
        sb.table("eateries").insert(SEED_EATERIES).execute()
    _seeded_ref["done"] = True


# ============================================================================
# Schemas
# ============================================================================


class DiningPrefs(BaseModel):
    cuisines: list[str] | None = None
    budget_amount: int | None = Field(default=None, ge=5, le=500)
    budget_tier: BudgetTier | None = None
    dietary_flags: list[str] | None = None
    custom_dietary: list[str] | None = None


class AvailabilityUpsert(BaseModel):
    slot_date: str  # YYYY-MM-DD
    slot_time: str = Field(min_length=1, max_length=10)
    meal_type: MealType


class PickAdd(BaseModel):
    eatery_id: str
    priority: int | None = 1


class MatchProposal(BaseModel):
    other_user_id: str
    eatery_id: str
    scheduled_at: str  # ISO 8601
    meal_type: MealType
    compatibility_score: int | None = None
    match_factors: dict[str, Any] | None = None


class MatchResponse(BaseModel):
    response: Literal["accepted", "declined"]


# ============================================================================
# dining_preferences
# ============================================================================


@router.get("/preferences")
async def get_preferences(
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    ensure_profile_row(user_id)
    sb = get_supabase()
    try:
        resp = (
            sb.table("dining_preferences")
            .select("*")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
    except Exception as exc:
        if _is_missing_table_error(exc):
            raise _schema_not_ready()
        raise
    if not resp or not resp.data:
        # Return defaults so the UI can render without an error
        return {
            "user_id": user_id,
            "cuisines": [],
            "budget_amount": 35,
            "budget_tier": "$$",
            "dietary_flags": [],
            "custom_dietary": [],
        }
    return resp.data


@router.put("/preferences")
async def put_preferences(
    body: DiningPrefs,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    ensure_profile_row(user_id)
    sb = get_supabase()
    payload: dict[str, Any] = {"user_id": user_id}
    for field in ("cuisines", "budget_amount", "budget_tier", "dietary_flags", "custom_dietary"):
        value = getattr(body, field)
        if value is not None:
            payload[field] = value
    try:
        sb.table("dining_preferences").upsert(payload, on_conflict="user_id").execute()
    except Exception as exc:
        if _is_missing_table_error(exc):
            raise _schema_not_ready()
        raise
    return await get_preferences(user_id)


# ============================================================================
# eateries
# ============================================================================


@router.get("/eateries")
async def list_eateries(
    cuisine: str | None = None,
    trending_only: bool = False,
    limit: int = Query(default=100, ge=1, le=500),
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    sb = get_supabase()
    try:
        _ensure_seed_eateries(sb)
        query = sb.table("eateries").select("*")
        if cuisine:
            query = query.eq("cuisine", cuisine)
        if trending_only:
            query = query.eq("is_trending", True).order("trending_rank")
        else:
            query = query.order("rating", desc=True)
        query = query.limit(limit)
        resp = query.execute()
    except Exception as exc:
        if _is_missing_table_error(exc):
            raise _schema_not_ready()
        raise
    return {"eateries": resp.data or []}


@router.get("/eateries/{eatery_id}")
async def get_eatery(
    eatery_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    sb = get_supabase()
    try:
        resp = sb.table("eateries").select("*").eq("id", eatery_id).maybe_single().execute()
    except Exception as exc:
        if _is_missing_table_error(exc):
            raise _schema_not_ready()
        raise
    if not resp or not resp.data:
        raise HTTPException(404, "Eatery not found")
    return resp.data


# ============================================================================
# dining_picks
# ============================================================================


@router.get("/picks")
async def list_picks(
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    sb = get_supabase()
    try:
        resp = (
            sb.table("dining_picks")
            .select("*, eateries(*)")
            .eq("user_id", user_id)
            .order("priority")
            .execute()
        )
    except Exception as exc:
        if _is_missing_table_error(exc):
            raise _schema_not_ready()
        raise
    return {"picks": resp.data or []}


@router.post("/picks")
async def add_pick(
    body: PickAdd,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    sb = get_supabase()
    try:
        existing = (
            sb.table("dining_picks")
            .select("id")
            .eq("user_id", user_id)
            .execute()
        )
        if len(existing.data or []) >= 3:
            raise HTTPException(400, "Pick limit reached (3). Remove one first.")
        sb.table("dining_picks").insert(
            {"user_id": user_id, "eatery_id": body.eatery_id, "priority": body.priority or 1}
        ).execute()
    except HTTPException:
        raise
    except Exception as exc:
        if _is_missing_table_error(exc):
            raise _schema_not_ready()
        raise
    return await list_picks(user_id)


@router.delete("/picks/{eatery_id}")
async def remove_pick(
    eatery_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    sb = get_supabase()
    try:
        sb.table("dining_picks").delete().eq("user_id", user_id).eq(
            "eatery_id", eatery_id
        ).execute()
    except Exception as exc:
        if _is_missing_table_error(exc):
            raise _schema_not_ready()
        raise
    return await list_picks(user_id)


# ============================================================================
# dining_availability
# ============================================================================


@router.get("/availability")
async def list_availability(
    from_date: str | None = Query(default=None, alias="from"),
    to_date: str | None = Query(default=None, alias="to"),
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    sb = get_supabase()
    try:
        query = (
            sb.table("dining_availability")
            .select("*")
            .eq("user_id", user_id)
            .order("slot_date")
            .order("slot_time")
        )
        if from_date:
            query = query.gte("slot_date", from_date)
        if to_date:
            query = query.lte("slot_date", to_date)
        resp = query.execute()
    except Exception as exc:
        if _is_missing_table_error(exc):
            raise _schema_not_ready()
        raise
    return {"availability": resp.data or []}


@router.put("/availability")
async def set_availability(
    body: AvailabilityUpsert,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    sb = get_supabase()
    try:
        sb.table("dining_availability").upsert(
            {
                "user_id": user_id,
                "slot_date": body.slot_date,
                "slot_time": body.slot_time,
                "meal_type": body.meal_type,
            },
            on_conflict="user_id,slot_date,slot_time",
        ).execute()
    except Exception as exc:
        if _is_missing_table_error(exc):
            raise _schema_not_ready()
        raise
    return {"status": "upserted"}


@router.delete("/availability")
async def clear_availability(
    slot_date: str,
    slot_time: str,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, str]:
    sb = get_supabase()
    try:
        sb.table("dining_availability").delete().eq("user_id", user_id).eq(
            "slot_date", slot_date
        ).eq("slot_time", slot_time).execute()
    except Exception as exc:
        if _is_missing_table_error(exc):
            raise _schema_not_ready()
        raise
    return {"status": "deleted"}


# ============================================================================
# meal_matches
# ============================================================================


@router.get("/matches")
async def list_matches(
    status: str | None = None,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Return every match where the current user is either side of the pair.

    PostgREST or-filter lets us express `user_a_id = X OR user_b_id = X` in
    one query — ergonomic and indexed.
    """
    sb = get_supabase()
    try:
        query = (
            sb.table("meal_matches")
            .select("*, eateries(*)")
            .or_(f"user_a_id.eq.{user_id},user_b_id.eq.{user_id}")
            .order("scheduled_at", desc=False)
        )
        if status:
            query = query.eq("status", status)
        resp = query.execute()
    except Exception as exc:
        if _is_missing_table_error(exc):
            raise _schema_not_ready()
        raise
    return {"matches": resp.data or []}


@router.post("/matches")
async def propose_match(
    body: MatchProposal,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    if body.other_user_id == user_id:
        raise HTTPException(400, "Cannot propose a match with yourself")
    sb = get_supabase()
    try:
        # Compute a naive compatibility score if the caller didn't supply one
        score = body.compatibility_score
        factors = body.match_factors or {}
        if score is None:
            score, factors = _compute_compatibility(sb, user_id, body.other_user_id, body.eatery_id)

        row = {
            "user_a_id": user_id,
            "user_b_id": body.other_user_id,
            "eatery_id": body.eatery_id,
            "scheduled_at": body.scheduled_at,
            "meal_type": body.meal_type,
            "status": "proposed",
            "a_response": "accepted",  # proposing implies acceptance from the proposer
            "compatibility_score": score,
            "match_factors": factors,
            "proposed_by": user_id,
        }
        resp = sb.table("meal_matches").insert(row).execute()
    except HTTPException:
        raise
    except Exception as exc:
        if _is_missing_table_error(exc):
            raise _schema_not_ready()
        raise
    created = (resp.data or [None])[0]
    if not created:
        raise HTTPException(500, "Failed to propose match")
    return created


@router.post("/matches/{match_id}/respond")
async def respond_to_match(
    match_id: str,
    body: MatchResponse,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    sb = get_supabase()
    try:
        match_resp = (
            sb.table("meal_matches")
            .select("*")
            .eq("id", match_id)
            .maybe_single()
            .execute()
        )
    except Exception as exc:
        if _is_missing_table_error(exc):
            raise _schema_not_ready()
        raise
    match = match_resp.data if match_resp else None
    if not match:
        raise HTTPException(404, "Match not found")

    if user_id not in (match["user_a_id"], match["user_b_id"]):
        raise HTTPException(403, "Not your match")

    field = "a_response" if match["user_a_id"] == user_id else "b_response"
    update: dict[str, Any] = {field: body.response}

    other_field = "b_response" if field == "a_response" else "a_response"
    other_value = match.get(other_field)

    if body.response == "declined":
        update["status"] = "declined"
    elif body.response == "accepted" and other_value == "accepted":
        update["status"] = "accepted"

    sb.table("meal_matches").update(update).eq("id", match_id).execute()
    updated = (
        sb.table("meal_matches")
        .select("*, eateries(*)")
        .eq("id", match_id)
        .maybe_single()
        .execute()
    )
    return updated.data if updated else {"id": match_id, **update}


# ============================================================================
# dining_stats
# ============================================================================


@router.get("/stats")
async def get_stats(
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    sb = get_supabase()
    try:
        resp = (
            sb.table("dining_stats")
            .select("*")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
    except Exception as exc:
        if _is_missing_table_error(exc):
            raise _schema_not_ready()
        raise
    if not resp or not resp.data:
        return {
            "user_id": user_id,
            "matches_made": 0,
            "points_earned": 0,
            "eateries_visited": 0,
            "social_rank_pct": None,
        }
    return resp.data


# ============================================================================
# users directory (for picking a match partner)
# ============================================================================


@router.get("/users")
async def list_other_users(
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Return every profile row except the caller's.

    Used by the "Propose match with…" dropdown. In a production app this
    would be gated by a friend list or opt-in flag; for the hackathon the
    dataset is small enough to just list all opted-in profiles.
    """
    sb = get_supabase()
    resp = (
        sb.table("profiles")
        .select("id,name,character")
        .neq("id", user_id)
        .limit(200)
        .execute()
    )
    return {"users": resp.data or []}


# ============================================================================
# Context helper (used by chat.py so Claude can query meal buddy data)
# ============================================================================


def build_meal_buddy_context(user_id: str, max_chars: int = 12_000) -> str:
    """Assemble a compact dossier about the user's meal buddy state."""
    sb = get_supabase()
    try:
        prefs_resp = (
            sb.table("dining_preferences")
            .select("*")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        picks_resp = (
            sb.table("dining_picks")
            .select("*, eateries(name, cuisine, price_tier)")
            .eq("user_id", user_id)
            .execute()
        )
        matches_resp = (
            sb.table("meal_matches")
            .select("*, eateries(name, cuisine)")
            .or_(f"user_a_id.eq.{user_id},user_b_id.eq.{user_id}")
            .order("scheduled_at")
            .limit(10)
            .execute()
        )
        avail_resp = (
            sb.table("dining_availability")
            .select("*")
            .eq("user_id", user_id)
            .gte("slot_date", datetime.now(timezone.utc).date().isoformat())
            .order("slot_date")
            .limit(20)
            .execute()
        )
    except Exception:
        return ""

    prefs = prefs_resp.data if prefs_resp else None
    picks = picks_resp.data if picks_resp else []
    matches = matches_resp.data if matches_resp else []
    avail = avail_resp.data if avail_resp else []

    lines: list[str] = ["# MEAL & FRIENDS CONTEXT"]
    if prefs:
        lines.append("## PREFERENCES")
        lines.append(f"Cuisines: {', '.join(prefs.get('cuisines') or []) or '(none set)'}")
        lines.append(f"Budget: ${prefs.get('budget_amount')} ({prefs.get('budget_tier')})")
        dietary = (prefs.get('dietary_flags') or []) + (prefs.get('custom_dietary') or [])
        lines.append(f"Dietary flags: {', '.join(dietary) or '(none)'}")
        lines.append("")
    else:
        lines.append("## PREFERENCES: not yet configured")
        lines.append("")

    if picks:
        lines.append("## PICKS (top restaurants the user wants to match on)")
        for p in picks:
            e = p.get("eateries") or {}
            lines.append(f"- {e.get('name','(unknown)')} ({e.get('cuisine','')}, {e.get('price_tier','')})")
        lines.append("")

    if avail:
        lines.append("## UPCOMING AVAILABILITY")
        for a in avail:
            lines.append(f"- {a['slot_date']} {a['slot_time']} ({a['meal_type']})")
        lines.append("")

    if matches:
        lines.append("## MATCHES (upcoming or recent)")
        for m in matches:
            e = m.get("eateries") or {}
            lines.append(
                f"- {m['status'].upper()} · {m['scheduled_at']} · "
                f"{e.get('name','?')} · score {m.get('compatibility_score')}%"
            )
        lines.append("")

    blob = "\n".join(lines).strip()
    if len(blob) > max_chars:
        blob = blob[:max_chars] + "\n\n[… meal buddy context truncated …]"
    return blob


# ============================================================================
# Internal: compatibility scoring
# ============================================================================


def _compute_compatibility(
    sb, user_a_id: str, user_b_id: str, eatery_id: str
) -> tuple[int, dict[str, Any]]:
    """Return (score_0_to_100, factors_dict).

    Cheap heuristic based on:
      * cuisine overlap (max 40)
      * dietary overlap (max 30)
      * budget tier similarity (max 20)
      * same eatery in picks bonus (max 10)
    """
    try:
        a_prefs = (
            sb.table("dining_preferences")
            .select("*")
            .eq("user_id", user_a_id)
            .maybe_single()
            .execute()
        )
        b_prefs = (
            sb.table("dining_preferences")
            .select("*")
            .eq("user_id", user_b_id)
            .maybe_single()
            .execute()
        )
    except Exception:
        return 50, {}

    a = (a_prefs.data if a_prefs else {}) or {}
    b = (b_prefs.data if b_prefs else {}) or {}

    a_cuisines = set(a.get("cuisines") or [])
    b_cuisines = set(b.get("cuisines") or [])
    cuisine_overlap = len(a_cuisines & b_cuisines)
    cuisine_score = min(40, cuisine_overlap * 10)

    a_diet = set((a.get("dietary_flags") or []) + (a.get("custom_dietary") or []))
    b_diet = set((b.get("dietary_flags") or []) + (b.get("custom_dietary") or []))
    if not a_diet and not b_diet:
        dietary_score = 30  # no flags — trivially compatible
    elif a_diet == b_diet:
        dietary_score = 30
    elif a_diet & b_diet:
        dietary_score = 20
    elif a_diet.isdisjoint(b_diet):
        dietary_score = 10
    else:
        dietary_score = 15

    a_tier = a.get("budget_tier") or "$$"
    b_tier = b.get("budget_tier") or "$$"
    tier_map = {"$": 1, "$$": 2, "$$$": 3}
    tier_diff = abs(tier_map.get(a_tier, 2) - tier_map.get(b_tier, 2))
    budget_score = max(0, 20 - tier_diff * 10)

    # pick-overlap bonus
    try:
        a_picks = (
            sb.table("dining_picks").select("eatery_id").eq("user_id", user_a_id).execute()
        )
        b_picks = (
            sb.table("dining_picks").select("eatery_id").eq("user_id", user_b_id).execute()
        )
        a_set = {p["eatery_id"] for p in (a_picks.data or [])}
        b_set = {p["eatery_id"] for p in (b_picks.data or [])}
        pick_bonus = 10 if eatery_id in (a_set & b_set) else (5 if eatery_id in (a_set | b_set) else 0)
    except Exception:
        pick_bonus = 0

    total = cuisine_score + dietary_score + budget_score + pick_bonus
    total = max(0, min(100, total))

    factors = {
        "cuisine_align": cuisine_score,
        "dietary_comp": dietary_score,
        "budget_fit": budget_score,
        "picks_overlap": pick_bonus,
    }
    return total, factors
