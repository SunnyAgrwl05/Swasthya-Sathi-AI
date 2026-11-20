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
