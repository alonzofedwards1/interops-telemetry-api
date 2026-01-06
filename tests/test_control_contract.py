from fastapi.testclient import TestClient

from app.api.telemetry import store as telemetry_store
from app.auth.user_store import get_user_store
from app.main import app


def _ensure_seed_user():
    store = get_user_store()
    store.ensure_seed_user()


def test_auth_token_returns_digest_and_user():
    _ensure_seed_user()
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/token",
            json={"email": "admin@interoplens.io", "password": "admin123"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body.get("digest")

        user = body.get("user") or {}
        assert user.get("email") == "admin@interoplens.io"
        assert user.get("role") == "admin"
        assert user.get("id")


def test_control_endpoints_return_arrays():
    with TestClient(app) as client:
        for path in ("/api/findings", "/api/pd-executions", "/api/committee/queue"):
            response = client.get(path)
            assert response.status_code == 200
            assert response.json() == []


def test_telemetry_events_default_empty_list():
    telemetry_store.clear()
    with TestClient(app) as client:
        response = client.get("/api/telemetry/events")
        assert response.status_code == 200
        assert response.json() == []
