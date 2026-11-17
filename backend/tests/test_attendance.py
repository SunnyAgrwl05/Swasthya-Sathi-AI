import datetime
import models


def test_create_attendance_record(client, sample_worker, db_session):
    """Test creating an attendance record marks status and logs audit entry."""
    today = datetime.date.today().isoformat()
    payload = {
        "worker_id": sample_worker.id,
        "date": today,
        "status": "present",
        "note": "Field duty completed",
    }
    response = client.post("/api/attendance", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["worker_id"] == sample_worker.id
    assert data["status"] == "present"
    assert data["marked_by"] == "manual"
    assert data["note"] == "Field duty completed"

    # Verify audit log was created
    audit = db_session.query(models.AuditLog).filter_by(action="Create Attendance").first()
    assert audit is not None
    assert f"worker_id {sample_worker.id}" in audit.description


def test_update_existing_attendance_record(client, sample_worker, db_session):
    """Test updating existing attendance on the same date updates status and adds audit log."""
    today = datetime.date.today().isoformat()
    # First mark present
    client.post("/api/attendance", json={
        "worker_id": sample_worker.id,
        "date": today,
        "status": "present",
        "note": "Morning check-in"
    })

    # Update to leave
    update_payload = {
        "worker_id": sample_worker.id,
        "date": today,
        "status": "leave",
        "note": "Half-day medical emergency"
    }
    response = client.post("/api/attendance", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "leave"
    assert data["note"] == "Half-day medical emergency"

    # Verify update audit log
    audit = db_session.query(models.AuditLog).filter_by(action="Update Attendance").first()
    assert audit is not None
    assert "to leave" in audit.description


def test_get_attendance_list_and_filter(client, sample_worker, db_session):
    """Test retrieving attendance list and filtering by worker_id."""
    d1 = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    d2 = datetime.date.today().isoformat()

    client.post("/api/attendance", json={"worker_id": sample_worker.id, "date": d1, "status": "present"})
    client.post("/api/attendance", json={"worker_id": sample_worker.id, "date": d2, "status": "absent"})

    # Get all attendance
    res_all = client.get("/api/attendance")
    assert res_all.status_code == 200
    records = res_all.json()
    assert len(records) >= 2

    # Filter by worker_id
    res_filtered = client.get(f"/api/attendance?worker_id={sample_worker.id}")
    assert res_filtered.status_code == 200
    filtered_records = res_filtered.json()
    assert all(r["worker_id"] == sample_worker.id for r in filtered_records)


def test_analytics_summary(client, sample_worker, db_session):
    """Test analytics summary computes correct attendance percentage and present counts."""
    # Add another worker
    worker2 = models.HealthWorker(
        name="Anjali Sharma",
        role="ANM",
        phone="+919876543299",
        center="Patna Center",
        worker_code="ANM-PAT-002",
    )
    db_session.add(worker2)
    db_session.commit()
    db_session.refresh(worker2)

    today = datetime.date.today()
    # Worker 1: 2 present, 0 absent = 100%
    client.post("/api/attendance", json={"worker_id": sample_worker.id, "date": today.isoformat(), "status": "present"})
    client.post("/api/attendance", json={"worker_id": sample_worker.id, "date": (today - datetime.timedelta(days=1)).isoformat(), "status": "present"})

    # Worker 2: 1 present, 1 absent = 50%
    client.post("/api/attendance", json={"worker_id": worker2.id, "date": today.isoformat(), "status": "present"})
    client.post("/api/attendance", json={"worker_id": worker2.id, "date": (today - datetime.timedelta(days=1)).isoformat(), "status": "absent"})

    res = client.get("/api/analytics/summary?days=30")
    assert res.status_code == 200
    summary = res.json()
    assert len(summary) == 2

    # Should be sorted lowest attendance first
    assert summary[0]["worker_id"] == worker2.id
    assert summary[0]["attendance_pct"] == 50.0
    assert summary[0]["present"] == 1
    assert summary[0]["total_logged"] == 2

    assert summary[1]["worker_id"] == sample_worker.id
    assert summary[1]["attendance_pct"] == 100.0
    assert summary[1]["present"] == 2
    assert summary[1]["total_logged"] == 2
