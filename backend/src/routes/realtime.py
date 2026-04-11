"""Realtime voice router.

Exposes endpoints that:
- mint short-lived OpenAI Realtime client secrets, and
- receive client-side debug breadcrumbs (so we can see what a remote
  browser is doing during the WebRTC handshake without needing DevTools
  access to that browser).

Router prefix is `/api/realtime` because the current Vite dev proxy in
frontend/vite.config.js forwards `/api/*` verbatim (no rewrite), so this path
matches end-to-end.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel, Field

from src.auth import get_current_user_id
from src.services.realtime_voice import create_client_secret

router = APIRouter(prefix="/api/realtime", tags=["realtime"])

CLIENT_DEBUG_LOG = Path("/tmp/jarvis_client_debug.log")


class RealtimeSessionRequest(BaseModel):
    model: str | None = None
    voice: str | None = None
    instructions: str | None = None


async def _optional_user_id(authorization: str | None) -> str | None:
    """Resolve the caller's user id if a Bearer token is present, else None.

    Keeps the endpoint backward-compatible — if the frontend calls without
    auth, the session is still minted (without a personal dossier).
    """
    if not authorization:
        return None
    try:
        return await get_current_user_id(authorization)
    except Exception:
        return None


@router.post("/session")
async def start_realtime_session(
    body: RealtimeSessionRequest | None = None,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Return a short-lived OpenAI Realtime client secret + session metadata.

    Callers can override `model`, `voice`, and `instructions` per request; if
    omitted, values fall through to `backend/config/openai_speech_to_speech.json`
    → env vars (`OPENAI_REALTIME_*`) → hardcoded defaults.

    If the caller includes a `Authorization: Bearer <supabase_access_token>`
    header, we also inject their live Meal & Friends dossier (prefs / picks /
    availability / upcoming matches) into the session instructions so Sage
    has immediate personal context without needing to call tools first.
    """
    body = body or RealtimeSessionRequest()
    user_id = await _optional_user_id(authorization)
    return await create_client_secret(
        model=body.model,
        voice=body.voice,
        instructions=body.instructions,
        user_id=user_id,
    )


@router.get("/health")
async def realtime_health() -> dict[str, str]:
    return {"status": "ok", "service": "jarvis-realtime"}


class DebugBreadcrumb(BaseModel):
    """Single debug breadcrumb from a browser client."""
    event: str = Field(..., max_length=80)
    session: str | None = Field(default=None, max_length=64)
    data: dict[str, Any] | None = None


@router.post("/debug")
async def post_client_debug(
    body: DebugBreadcrumb,
    request: Request,
) -> dict[str, str]:
    """Receive a client-side debug breadcrumb from the browser and append it to
    /tmp/jarvis_client_debug.log so we can tail it from a shell session.
    """
    ts = datetime.now(timezone.utc).isoformat()
    ua = request.headers.get("user-agent", "")[:100]
    session = body.session or "-"
    data_json = json.dumps(body.data or {}, default=str)
    # Keep lines to reasonable length for tailing
    if len(data_json) > 600:
        data_json = data_json[:597] + "..."
    line = (
        f"{ts}  sess={session}  {body.event:<28}  ua=\"{ua}\"  data={data_json}\n"
    )
    try:
        with CLIENT_DEBUG_LOG.open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        # Never fail the breadcrumb — it's diagnostic-only
        pass
    return {"ok": "1"}
