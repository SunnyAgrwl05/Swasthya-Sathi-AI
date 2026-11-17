import models


def test_get_workers_empty(client):
    """Test retrieving health workers when no workers are present."""
    response = client.get("/api/workers")
    assert response.status_code == 200
    assert response.json() == []


def test_create_worker_success(client):
    """Test successful creation of a new health worker."""
    payload = {
        "name": "Pooja Kumari",
        "role": "ANM",
        "phone": "+919812345678",
        "center": "Danapur Sub-Center",
        "worker_code": "ANM-DAN-101",
    }
    response = client.post("/api/workers", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Pooja Kumari"
    assert data["role"] == "ANM"
    assert data["worker_code"] == "ANM-DAN-101"
    assert "id" in data


def test_create_worker_duplicate_code(client, sample_worker):
    """Test that creating a worker with an existing worker_code returns 400 Bad Request."""
    payload = {
        "name": "Duplicate Worker",
        "role": "ASHA",
        "phone": "+919999999999",
        "center": "Another PHC",
        "worker_code": sample_worker.worker_code,
    }
    response = client.post("/api/workers", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_worker_missing_fields(client):
    """Test validation error when required fields are missing."""
    payload = {
        "name": "Incomplete Worker"
        # missing role, phone, center, worker_code
    }
    response = client.post("/api/workers", json=payload)
    assert response.status_code == 422


def test_delete_worker_success(client, sample_worker):
    """Test successful deletion of a health worker."""
    response = client.delete(f"/api/workers/{sample_worker.id}")
    assert response.status_code == 200
    assert response.json() == {"deleted": sample_worker.id}

    # Verify worker no longer exists
    get_res = client.get("/api/workers")
    assert len(get_res.json()) == 0


def test_delete_worker_not_found(client):
    """Test deleting a nonexistent worker returns 404."""
    response = client.delete("/api/workers/99999")
    assert response.status_code == 404
    assert "Worker not found" in response.json()["detail"]


def test_list_multiple_workers(client, db_session):
    """Test listing multiple workers."""
    w1 = models.HealthWorker(name="Worker 1", role="ASHA", phone="111", center="C1", worker_code="W1")
    w2 = models.HealthWorker(name="Worker 2", role="ANM", phone="222", center="C2", worker_code="W2")
    db_session.add_all([w1, w2])
    db_session.commit()

    response = client.get("/api/workers")
    assert response.status_code == 200
    workers = response.json()
    assert len(workers) == 2
    codes = [w["worker_code"] for w in workers]
    assert "W1" in codes and "W2" in codes
