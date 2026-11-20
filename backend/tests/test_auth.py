"""Tests for authentication and route security placeholders."""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_cors_middleware_headers():
    res = client.options(
        "/api/workers",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert res.status_code == 200
    assert "access-control-allow-origin" in res.headers


def test_route_not_found():
    res = client.get("/api/nonexistent-route")
    assert res.status_code == 404
