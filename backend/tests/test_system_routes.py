from fastapi.testclient import TestClient

from loop_api.main import app

client = TestClient(app)


def test_liveness_returns_service_status_and_request_id() -> None:
    response = client.get("/health/live", headers={"x-request-id": "test-request"})

    assert response.status_code == 200
    assert response.json() == {
        "service": "loop-api",
        "status": "ok",
        "checks": [],
    }
    assert response.headers["x-request-id"] == "test-request"


def test_version_exposes_build_metadata() -> None:
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json()["version"] == "0.1.0"


def test_unknown_route_uses_shared_error_envelope() -> None:
    response = client.get("/missing")

    assert response.status_code == 404
    payload = response.json()
    assert payload["code"] == "http_error"
    assert payload["message"] == "Not Found"
    assert payload["request_id"] == response.headers["x-request-id"]


def test_openapi_is_published_at_versioned_path() -> None:
    response = client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    assert response.json()["openapi"].startswith("3.1")
