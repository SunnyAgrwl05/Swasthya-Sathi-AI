"""
Unit tests for Root, Health Check, and Basic Security/CORS Endpoints
-------------------------------------------------------------------
"""


def test_root_health_check(client):
    """Verifies that the root health endpoint returns ok status and connected database."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Swasthya Sathi AI Backend"
    assert data["database"] == "Connected"


def test_cors_headers_present(client):
    """Verifies that CORS middleware headers are properly returned for cross-origin requests."""
    response = client.get("/", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") in ("*", "http://localhost:5173")
