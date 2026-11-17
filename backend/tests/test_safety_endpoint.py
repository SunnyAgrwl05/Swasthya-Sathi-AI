"""Integration tests for the safety check endpoint."""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_safety_check_endpoint_flagged():
    payload = {
        "query": "Is there a permanent instant cure for fever?",
        "response": "Drinking this concoction 100% guarantees to cure fever instantly with no side effects.",
    }
    res = client.post("/api/safety/check-hallucination", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_flagged"] is True
    assert data["risk_level"] == "HIGH"
    assert data["warning_message"] is not None
    assert "Critical Advisory" in data["warning_message"]


def test_safety_check_endpoint_clean():
    payload = {
        "query": "How can I maintain good hydration?",
        "response": "Drink water regularly throughout the day. For individualized hydration advice, consult a physician.",
    }
    res = client.post("/api/safety/check-hallucination", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] in ("LOW", "MEDIUM")
    assert "confidence_score" in data
