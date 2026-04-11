from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException

from src.config import CONFIG_DIR, settings
from src.models import RealtimeVoiceSessionRequest, RealtimeVoiceSessionResponse


REALTIME_CONFIG_PATH = CONFIG_DIR / "openai_speech_to_speech.json"
REALTIME_TEST_PAGE_PATH = CONFIG_DIR / "openai_realtime_test.html"


@lru_cache(maxsize=1)
def _load_realtime_template() -> dict[str, Any]:
    if REALTIME_CONFIG_PATH.exists():
        return json.loads(REALTIME_CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def load_test_page() -> str:
    return REALTIME_TEST_PAGE_PATH.read_text(encoding="utf-8")


def build_session_payload(payload: RealtimeVoiceSessionRequest | None = None) -> dict[str, Any]:
    payload = payload or RealtimeVoiceSessionRequest()
    template = _load_realtime_template()
    session_template = template.get("session", {})
    model = payload.model or session_template.get("model") or settings.openai_realtime_model
    voice = payload.voice or session_template.get("voice") or settings.openai_realtime_voice
    instructions = (
        payload.instructions
        or session_template.get("instructions")
        or settings.openai_realtime_instructions
    )

    return {
        "session": {
            "type": "realtime",
            "model": model,
            "instructions": instructions,
            "audio": {
                "output": {
                    "voice": voice,
                },
            },
        }
    }


async def create_client_secret(payload: RealtimeVoiceSessionRequest | None = None) -> RealtimeVoiceSessionResponse:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    session_payload = build_session_payload(payload)
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/realtime/client_secrets",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json=session_payload,
        )
        if response.is_error:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "OpenAI Realtime client secret request failed",
                    "status_code": response.status_code,
                    "response": _safe_json_or_text(response),
                    "request_payload": session_payload,
                },
            )
        data = response.json()

    client_secret = _extract_client_secret(data)
    session_config = session_payload["session"]
    return RealtimeVoiceSessionResponse(
        session_id=data.get("id"),
        client_secret=client_secret["value"],
        expires_at=client_secret.get("expires_at"),
        model=session_config["model"],
        voice=session_config["audio"]["output"]["voice"],
        instructions=session_config["instructions"],
    )


def _extract_client_secret(data: dict[str, Any]) -> dict[str, Any]:
    client_secret = data.get("client_secret")
    if isinstance(client_secret, dict) and client_secret.get("value"):
        return client_secret
    if data.get("value"):
        return {"value": data["value"], "expires_at": data.get("expires_at")}
    raise RuntimeError("OpenAI Realtime client secret response did not include a token")


def _safe_json_or_text(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text
