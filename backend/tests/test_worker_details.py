import datetime
import pytest
import models
from database import SessionLocal
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_get_worker_detail_success(db_session):
    """Test retrieving a single worker with their attendance history."""
    code = f"ASHA-DET-{int(datetime.datetime.now().timestamp())}"
    worker = models.HealthWorker(
        worker_code=code,
        name="Manju Kumari",
        role="ASHA Worker",
        center="Bihta PHC",
        phone="+919123456789",
    )
    db_session.add(worker)
    db_session.commit()
    db_session.refresh(worker)

    a1 = models.AttendanceRecord(
        worker_id=worker.id,
        date=datetime.date.today(),
        status="present",
        marked_by="manual",
    )
    db_session.add(a1)
    db_session.commit()

    response = client.get(f"/api/workers/{worker.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == worker.id
    assert data["name"] == "Manju Kumari"
    assert data["worker_code"] == code
    assert data["total_attendance_records"] >= 1
    assert len(data["recent_attendance"]) >= 1
    assert data["recent_attendance"][0]["status"] == "present"


def test_get_worker_detail_not_found():
    """Test retrieving a nonexistent worker returns 404."""
    response = client.get("/api/workers/999999")
    assert response.status_code == 404
    assert "Worker not found" in response.json()["detail"]


def test_update_worker_success(db_session):
    """Test updating worker fields (name, center, phone)."""
    code = f"ASHA-UPD-{int(datetime.datetime.now().timestamp())}"
    worker = models.HealthWorker(
        worker_code=code,
        name="Old Name",
        role="ASHA",
        center="Old Center",
        phone="+910000000000",
    )
    db_session.add(worker)
    db_session.commit()
    db_session.refresh(worker)

    payload = {
        "name": "Updated Name",
        "center": "New Center PHC",
        "phone": "+919988776655",
    }
    response = client.put(f"/api/workers/{worker.id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["center"] == "New Center PHC"
    assert data["phone"] == "+919988776655"
    assert data["role"] == "ASHA"


def test_update_worker_not_found():
    """Test updating a nonexistent worker returns 404."""
    response = client.put("/api/workers/999999", json={"name": "Ghost"})
    assert response.status_code == 404
    assert "Worker not found" in response.json()["detail"]
