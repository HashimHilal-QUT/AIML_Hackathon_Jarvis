from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_health_route_exists() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "bedtime-story-backend"
    assert "providers" in body


def test_story_routes_exist() -> None:
    routes = {route.path for route in app.routes}
    assert "/api/stories/generate" in routes
    assert "/api/stories/audio" in routes
    assert "/api/voice/command" in routes
    assert "/api/voice/session/start" in routes
    assert "/api/voice/realtime/session" in routes
    assert "/api/voice/realtime/test-page" in routes
    assert "/api/feedback" in routes
