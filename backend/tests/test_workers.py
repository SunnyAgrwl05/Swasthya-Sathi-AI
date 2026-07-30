from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_workers_endpoint():
    response = client.get("/api/workers")
    assert response.status_code == 200