from __future__ import annotations

from asyncio import Lock
from datetime import UTC, datetime
from uuid import uuid4

from src.config import settings
from src.models import ActionType, SessionStatePatch, VoiceSessionStartRequest, VoiceSessionStartResponse


_sessions: dict[str, dict] = {}
_lock = Lock()


async def start_session(payload: VoiceSessionStartRequest) -> VoiceSessionStartResponse:
    session_id = uuid4().hex
    async with _lock:
        _sessions[session_id] = {
            "session_id": session_id,
            "app_activated": payload.app_activated,
            "listening_enabled": payload.listening_enabled,
            "last_action": None,
            "updated_at": datetime.now(UTC),
        }
    return VoiceSessionStartResponse(
        session_id=session_id,
        listening_enabled=payload.listening_enabled,
        app_activated=payload.app_activated,
        wake_phrase=settings.voice_wake_phrase,
    )


async def get_or_create(session_id: str) -> dict:
    async with _lock:
        session = _sessions.get(session_id)
        if session is None:
            session = {
                "session_id": session_id,
                "app_activated": False,
                "listening_enabled": True,
                "last_action": None,
                "updated_at": datetime.now(UTC),
            }
            _sessions[session_id] = session
        return dict(session)


async def apply_patch(session_id: str, patch: SessionStatePatch) -> dict:
    async with _lock:
        session = _sessions.setdefault(
            session_id,
            {
                "session_id": session_id,
                "app_activated": False,
                "listening_enabled": True,
                "last_action": None,
                "updated_at": datetime.now(UTC),
            },
        )
        if patch.app_activated is not None:
            session["app_activated"] = patch.app_activated
        if patch.listening_enabled is not None:
            session["listening_enabled"] = patch.listening_enabled
        if patch.last_action is not None:
            session["last_action"] = patch.last_action
        session["updated_at"] = datetime.now(UTC)
        return dict(session)


def make_patch(
    *,
    app_activated: bool | None = None,
    listening_enabled: bool | None = None,
    last_action: ActionType | None = None,
) -> SessionStatePatch:
    return SessionStatePatch(
        app_activated=app_activated,
        listening_enabled=listening_enabled,
        last_action=last_action,
    )
