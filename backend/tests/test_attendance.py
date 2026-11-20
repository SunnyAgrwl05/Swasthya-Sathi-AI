"""
Unit tests for Attendance API Endpoints (/api/attendance)
---------------------------------------------------------
"""

import datetime


def test_get_attendance_empty(client):
    """Verifies that GET /api/attendance returns an empty list on a clean database."""
    response = client.get("/api/attendance")
    assert response.status_code == 200
    assert response.json() == []


def test_create_attendance_record(client, sample_worker):
    """Verifies logging attendance for a health worker."""
    today = datetime.date.today().isoformat()
    payload = {
        "worker_id": sample_worker.id,
        "date": today,
        "status": "present",
        "note": "Field vaccination drive",
    }
    response = client.post("/api/attendance", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["worker_id"] == sample_worker.id
    assert data["date"] == today
    assert data["status"] == "present"
    assert data["marked_by"] == "manual"


def test_update_existing_attendance_record(client, sample_worker):
    """Verifies that posting attendance for the same worker and date updates the existing record."""
    today = datetime.date.today().isoformat()
    initial_payload = {
        "worker_id": sample_worker.id,
        "date": today,
        "status": "absent",
        "note": "Initial log",
    }
    res1 = client.post("/api/attendance", json=initial_payload)
    assert res1.status_code == 200
    record_id = res1.json()["id"]

    update_payload = {
        "worker_id": sample_worker.id,
        "date": today,
        "status": "present",
        "note": "Corrected by supervisor",
    }
    res2 = client.post("/api/attendance", json=update_payload)
    assert res2.status_code == 200
    updated_data = res2.json()
    assert updated_data["id"] == record_id  # Same record ID, updated in place
    assert updated_data["status"] == "present"
    assert updated_data["note"] == "Corrected by supervisor"


def test_filter_attendance_by_worker(client, sample_worker, sample_attendance):
    """Verifies filtering attendance records by worker_id."""
    response = client.get(f"/api/attendance?worker_id={sample_worker.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(sample_attendance)
    assert all(r["worker_id"] == sample_worker.id for r in data)


def test_attendance_invalid_payload(client):
    """Verifies that invalid date format returns 422 Unprocessable Entity."""
    payload = {
        "worker_id": 1,
        "date": "invalid-date",
        "status": "present",
    }
    response = client.post("/api/attendance", json=payload)
    assert response.status_code == 422
from datetime import date
import models


def test_get_attendance_empty(client):
    res = client.get("/api/attendance")
    assert res.status_code == 200
    assert res.json() == []


def test_mark_attendance_success(client, db_session):
    worker = models.HealthWorker(
        worker_code="ASHA-101",
        name="Kavita Singh",
        role="ASHA Worker",
        center="Muzaffarpur PHC",
        phone="+919822233344"
    )
    db_session.add(worker)
    db_session.commit()
    db_session.refresh(worker)

    payload = {
        "worker_id": worker.id,
        "date": str(date.today()),
        "status": "Present",
        "note": "Attended morning immunization drive"
    }
    res = client.post("/api/attendance", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["worker_id"] == worker.id
    assert data["status"] == "Present"
    assert data["note"] == "Attended morning immunization drive"


def test_mark_attendance_worker_not_found(client):
    payload = {
        "worker_id": 99999,
        "date": str(date.today()),
        "status": "Present"
    }
    res = client.post("/api/attendance", json=payload)
    assert res.status_code == 404
    assert "Worker not found" in res.json()["detail"]


def test_filter_attendance_by_worker(client, db_session):
    w1 = models.HealthWorker(worker_code="W1", name="Worker 1", center="C1", phone="123")
    w2 = models.HealthWorker(worker_code="W2", name="Worker 2", center="C2", phone="456")
    db_session.add_all([w1, w2])
    db_session.commit()

    r1 = models.AttendanceRecord(worker_id=w1.id, date=date.today(), status="Present")
    r2 = models.AttendanceRecord(worker_id=w2.id, date=date.today(), status="Absent")
    db_session.add_all([r1, r2])
    db_session.commit()

    res = client.get(f"/api/attendance?worker_id={w1.id}")
    assert res.status_code == 200
    records = res.json()
    assert len(records) == 1
    assert records[0]["worker_id"] == w1.id
