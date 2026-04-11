from io import BytesIO

from fastapi.testclient import TestClient

from src.main import app
from src.models import (
    ActionType,
    PhaseResult,
    ProviderHealth,
    SessionStatePatch,
    VoiceCommandResponse,
)
from src.services import health, voice_command


client = TestClient(app)


def _multipart(mode: str, ui_context: str = "{}", session_id: str = "demo-session", want_voice_response: bool = False):
    return {
        "audio_file": ("command.wav", BytesIO(b"audio-bytes"), "audio/wav"),
        "session_id": (None, session_id),
        "mode": (None, mode),
        "ui_context": (None, ui_context),
        "want_voice_response": (None, str(want_voice_response).lower()),
    }


def test_voice_command_wake_flow(monkeypatch) -> None:
    async def fake_process_voice_command(**kwargs):
        return VoiceCommandResponse(
            session_id=kwargs["session_id"],
            mode=kwargs["mode"],
            transcript="hey jarvis",
            phase_result=PhaseResult.wake_detected,
            action=ActionType.activate_app,
            confidence=0.98,
            spoken_response_text="Jarvis is awake.",
            session_state_patch=SessionStatePatch(app_activated=True, last_action=ActionType.activate_app),
            provider_chain={"stt": "openai:gpt-4o-transcribe", "reasoning": "openai:gpt-5.4-mini"},
        )

    monkeypatch.setattr(voice_command, "process_voice_command", fake_process_voice_command)

    response = client.post("/api/voice/command", files=_multipart("wake_mode"))

    assert response.status_code == 200
    body = response.json()
    assert body["phase_result"] == "wake_detected"
    assert body["action"] == "activate_app"


def test_voice_command_generate_story(monkeypatch) -> None:
    async def fake_process_voice_command(**kwargs):
        return VoiceCommandResponse(
            session_id=kwargs["session_id"],
            mode=kwargs["mode"],
            transcript="make me a fantasy story",
            phase_result=PhaseResult.command_detected,
            action=ActionType.generate_story,
            confidence=0.94,
            spoken_response_text="Generating your bedtime story now.",
            result={
                "story_id": "story-1",
                "title": "The Lantern Fox",
                "body": "Once upon a midnight hush...",
                "provider_used": "openai",
                "model_used": "gpt-5.4-mini",
            },
        )

    monkeypatch.setattr(voice_command, "process_voice_command", fake_process_voice_command)

    response = client.post(
        "/api/voice/command",
        files=_multipart("command_mode", '{"genre":"fantasy","mood":"cozy","length":"3","app_activated":true}'),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "generate_story"
    assert body["result"]["title"] == "The Lantern Fox"


def test_voice_command_ui_only_action(monkeypatch) -> None:
    async def fake_process_voice_command(**kwargs):
        return VoiceCommandResponse(
            session_id=kwargs["session_id"],
            mode=kwargs["mode"],
            transcript="play it",
            phase_result=PhaseResult.command_detected,
            action=ActionType.play_audio,
            confidence=0.87,
            spoken_response_text="Done.",
            ui_command="play_audio",
        )

    monkeypatch.setattr(voice_command, "process_voice_command", fake_process_voice_command)

    response = client.post(
        "/api/voice/command",
        files=_multipart("command_mode", '{"audio_url":"/media/example.mp3","app_activated":true}'),
    )

    assert response.status_code == 200
    assert response.json()["ui_command"] == "play_audio"


def test_voice_command_returns_spoken_audio(monkeypatch) -> None:
    async def fake_process_voice_command(**kwargs):
        return VoiceCommandResponse(
            session_id=kwargs["session_id"],
            mode=kwargs["mode"],
            transcript="turn listening off",
            phase_result=PhaseResult.command_detected,
            action=ActionType.listening_off,
            confidence=0.9,
            spoken_response_text="Listening is off.",
            spoken_response_audio_url="/media/assistant.mp3",
        )

    monkeypatch.setattr(voice_command, "process_voice_command", fake_process_voice_command)

    response = client.post("/api/voice/command", files=_multipart("command_mode", '{"app_activated":true}', want_voice_response=True))

    assert response.status_code == 200
    assert response.json()["spoken_response_audio_url"] == "/media/assistant.mp3"


def test_health_degraded_when_primary_provider_open(monkeypatch) -> None:
    degraded = ProviderHealth(
        primary_provider="openai",
        primary_model="gpt-4o-transcribe",
        primary_state="OPEN",
        fallback_provider="google",
        fallback_model="chirp_2",
        fallback_state="CLOSED",
    )
    healthy = ProviderHealth(
        primary_provider="openai",
        primary_model="gpt-5.4-mini",
        primary_state="CLOSED",
        fallback_provider="google",
        fallback_model="gemma-4",
        fallback_state="CLOSED",
    )

    monkeypatch.setattr(health.story_generator, "get_health", lambda: healthy)
    monkeypatch.setattr(health.stt, "get_health", lambda: degraded)
    monkeypatch.setattr(health.intent_parser, "get_health", lambda: healthy)
    monkeypatch.setattr(health.tts, "get_health", lambda: healthy)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
