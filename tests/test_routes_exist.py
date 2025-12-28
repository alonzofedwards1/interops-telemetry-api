from fastapi.routing import APIRoute

from app.main import app


def test_expected_routes_are_registered():
    """Ensure the frontend contract endpoints are mounted under the /api prefix."""
    paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    expected_paths = {
        "/api/tokens/manual",
        "/api/tokens/status",
        "/api/tokens/refresh",
        "/api/pd/search",
    }

    missing = expected_paths - paths
    assert not missing, f"Missing routes: {sorted(missing)}"
