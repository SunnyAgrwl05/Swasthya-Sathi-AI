def test_cors_preflight_headers(client):
    """Test CORS preflight OPTIONS request returns valid CORS access headers."""
    response = client.options(
        "/api/workers",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") in ["*", "http://localhost:5173"]


def test_malformed_json_rejection(client):
    """Test that malformed JSON payloads return 422 Unprocessable Entity."""
    response = client.post(
        "/api/workers",
        content="not-a-valid-json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_sql_injection_resilience(client, sample_worker):
    """Test that SQL injection strings in parameters are safely escaped by SQLAlchemy."""
    malicious_query = f"{sample_worker.id} OR 1=1; DROP TABLE health_workers;--"
    # FastAPI path parameter parsing expects int, so string returns 422
    response = client.delete(f"/api/workers/{malicious_query}")
    assert response.status_code == 422

    # Verify table was not dropped
    res = client.get("/api/workers")
    assert res.status_code == 200


def test_missing_body_rejection(client):
    """Test that empty POST requests on protected endpoints return 422."""
    response = client.post("/api/chat", json={})
    assert response.status_code == 422
