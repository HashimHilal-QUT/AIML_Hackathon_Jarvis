from fastapi.testclient import TestClient

from src.main import app
from src.models import RealtimeVoiceSessionResponse
from src.services import realtime_voice


client = TestClient(app)


def test_build_session_payload_uses_defaults() -> None:
    payload = realtime_voice.build_session_payload()

    assert payload["session"]["type"] == "realtime"
    assert payload["session"]["model"] == "gpt-realtime"
    assert payload["session"]["audio"]["output"]["voice"] == "marin"


def test_realtime_session_route_returns_token(monkeypatch) -> None:
    async def fake_create_client_secret(payload):
        return RealtimeVoiceSessionResponse(
            client_secret="secret-123",
            expires_at=1_900_000_000,
            model="gpt-realtime",
            voice="sage",
            instructions="Reply warmly and briefly in voice.",
        )

    monkeypatch.setattr(realtime_voice, "create_client_secret", fake_create_client_secret)

    response = client.post("/api/voice/realtime/session", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["client_secret"] == "secret-123"
    assert body["model"] == "gpt-realtime"


def test_realtime_test_page_exists() -> None:
    response = client.get("/api/voice/realtime/test-page")

    assert response.status_code == 200
    assert "OpenAI Realtime Voice Test" in response.text
