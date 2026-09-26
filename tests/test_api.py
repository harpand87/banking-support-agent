import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from app.api import app


def test_local_api_health_and_grounded_answer():
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok", "mode": "offline_demo"}
    response = client.post("/v1/answer", json={"text": "What is the monthly fee for the Everyday Account?"})
    assert response.status_code == 200
    assert response.json()["decision"] == "answer"
    assert response.json()["sources"] == ["KB-001"]


def test_api_rejects_unbounded_or_extra_input_fields():
    client = TestClient(app)
    too_long = client.post("/v1/answer", json={"text": "x" * 2001})
    extra = client.post("/v1/answer", json={"text": "hello", "password": "not-accepted"})
    assert too_long.status_code == 422
    assert extra.status_code == 422
