from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from loop_api.core.schemas import DependencyCheck
from loop_api.main import app

client = TestClient(app)


@patch(
    "loop_api.http.routers.system.collect_readiness_checks",
    new_callable=AsyncMock,
)
def test_readiness_ok_with_sqlite_and_no_threads(mock_collect) -> None:
    mock_collect.return_value = [
        DependencyCheck(name="sqlite", status="ok"),
        DependencyCheck(name="redis", status="ok"),
    ]

    response = client.get("/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert {check["name"] for check in payload["checks"]} == {"sqlite", "redis"}


@patch(
    "loop_api.http.routers.system.collect_readiness_checks",
    new_callable=AsyncMock,
)
def test_readiness_not_ready_when_sqlite_fails(mock_collect) -> None:
    mock_collect.return_value = [
        DependencyCheck(name="sqlite", status="unavailable", detail="connection failed"),
        DependencyCheck(name="redis", status="ok"),
    ]

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"


@patch(
    "loop_api.http.routers.system.collect_readiness_checks",
    new_callable=AsyncMock,
)
def test_readiness_includes_postgres_threads_when_enabled(mock_collect) -> None:
    mock_collect.return_value = [
        DependencyCheck(name="sqlite", status="ok"),
        DependencyCheck(name="redis", status="ok"),
        DependencyCheck(name="postgresql_threads", status="ok"),
    ]

    response = client.get("/health/ready")

    assert response.status_code == 200
    names = [check["name"] for check in response.json()["checks"]]
    assert names == ["sqlite", "redis", "postgresql_threads"]


@patch(
    "loop_api.http.routers.system.collect_readiness_checks",
    new_callable=AsyncMock,
)
def test_readiness_not_ready_when_threads_postgres_unavailable(mock_collect) -> None:
    mock_collect.return_value = [
        DependencyCheck(name="sqlite", status="ok"),
        DependencyCheck(name="redis", status="ok"),
        DependencyCheck(
            name="postgresql_threads",
            status="unavailable",
            detail="connection failed",
        ),
    ]

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
