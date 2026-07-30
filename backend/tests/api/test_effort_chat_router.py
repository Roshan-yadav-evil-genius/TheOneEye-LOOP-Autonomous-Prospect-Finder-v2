import pytest
from fastapi.testclient import TestClient

from main import app


def test_effort_chat_history_route_resolution():
    client = TestClient(app)
    effort_prefix = "LOOP_6075efa6-c4c8-428d-b18b-26f7f75ec02f_6a5204ba-e21b-4c7c-a7de-df0949a773f8_48fa7682-75fe-4fb2-bc40-2ec1d160927f_3"
    planner_thread_id = f"{effort_prefix}_planner"

    response = client.get(
        f"/api/v1/efforts/{effort_prefix}/chat/history?thread_id={planner_thread_id}"
    )

    # Must return 200 OK with thread_id and empty messages array, not 404
    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == planner_thread_id
    assert "messages" in data


import asyncio
from persistence.database import create_schema


def test_effort_plan_route():
    asyncio.run(create_schema())
    client = TestClient(app)
    effort_prefix = "LOOP_org1_prod1_strat1_1"

    response = client.get(f"/api/v1/efforts/{effort_prefix}/plan")
    assert response.status_code == 200
    data = response.json()
    assert data["planner_id"] == f"planner-{effort_prefix}"
    assert "phases" in data
    assert "runtime" in data
    assert "knowledge" in data


