"""
Unit tests for Health Worker API Endpoints (/api/workers)
---------------------------------------------------------
"""


def test_get_workers_empty(client):
    """Verifies that GET /api/workers returns an empty list on a clean database."""
    response = client.get("/api/workers")
    assert response.status_code == 200
    assert response.json() == []


def test_get_workers_with_data(client, sample_worker):
    """Verifies that GET /api/workers returns existing workers."""
    response = client.get("/api/workers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == sample_worker.name
    assert data[0]["role"] == sample_worker.role
    assert data[0]["center"] == sample_worker.center


def test_create_worker_success(client):
    """Verifies creating a new health worker with valid payload."""
    payload = {
        "worker_code": "ASHA-PAT-101",
        "name": "Kajal Kumari",
        "role": "ASHA Worker",
        "center": "PHC Patna",
        "phone": "9876543211",
    }
    response = client.post("/api/workers", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["worker_code"] == payload["worker_code"]
    assert data["name"] == payload["name"]
    assert data["id"] is not None


def test_create_worker_duplicate_code(client, sample_worker):
    """Verifies that creating a worker with an existing worker_code returns 400 Bad Request."""
    payload = {
        "worker_code": sample_worker.worker_code,
        "name": "Duplicate Worker",
        "role": "ANM",
        "center": "PHC Patna",
        "phone": "9876543212",
    }
    response = client.post("/api/workers", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_worker_missing_fields(client):
    """Verifies that omitting mandatory fields returns 422 Unprocessable Entity."""
    incomplete_payload = {
        "name": "Incomplete Worker"
        # missing worker_code, center, phone
    }
    response = client.post("/api/workers", json=incomplete_payload)
    assert response.status_code == 422


def test_delete_worker_success(client, sample_worker):
    """Verifies deleting an existing health worker."""
    response = client.delete(f"/api/workers/{sample_worker.id}")
    assert response.status_code == 200
    assert response.json()["deleted"] == sample_worker.id

    # Confirm worker is gone
    get_res = client.get("/api/workers")
    assert len(get_res.json()) == 0


def test_delete_worker_not_found(client):
    """Verifies that deleting a non-existent worker ID returns 404."""
    response = client.delete("/api/workers/999999")
    assert response.status_code == 404
import models


def test_get_workers_empty(client):
    res = client.get("/api/workers")
    assert res.status_code == 200
    assert res.json() == []


def test_create_worker_success(client):
    payload = {
        "worker_code": "ASHA-999",
        "name": "Sunita Devi",
        "role": "ASHA Worker",
        "center": "Patna PHC",
        "phone": "+919876543210"
    }
    res = client.post("/api/workers", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["worker_code"] == "ASHA-999"
    assert data["name"] == "Sunita Devi"
    assert "id" in data


def test_create_worker_duplicate_code_fails(client):
    payload = {
        "worker_code": "ASHA-999",
        "name": "Sunita Devi",
        "role": "ASHA Worker",
        "center": "Patna PHC",
        "phone": "+919876543210"
    }
    res1 = client.post("/api/workers", json=payload)
    assert res1.status_code == 200

    res2 = client.post("/api/workers", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_delete_worker(client, db_session):
    worker = models.HealthWorker(
        worker_code="ASHA-DEL",
        name="Anjali Kumari",
        role="ANM",
        center="Gaya Sub-center",
        phone="+919811122233"
    )
    db_session.add(worker)
    db_session.commit()
    db_session.refresh(worker)

    res = client.delete(f"/api/workers/{worker.id}")
    assert res.status_code == 200
    assert res.json() == {"deleted": worker.id}

    # Verify 404 on deleting non-existent worker
    res_not_found = client.delete("/api/workers/999999")
    assert res_not_found.status_code == 404
