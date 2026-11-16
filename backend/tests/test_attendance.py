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
