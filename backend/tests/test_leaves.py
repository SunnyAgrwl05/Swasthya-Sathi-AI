"""Unit tests for the Leave Management and Attendance Auto-Population system (closes #58)."""

import datetime
from fastapi.testclient import TestClient
from main import app
import models
from database import SessionLocal

client = TestClient(app)


def test_create_leave_and_auto_populate_attendance():
    db = SessionLocal()
    try:
        ts = int(datetime.datetime.now().timestamp() * 1000)
        worker = models.HealthWorker(
            worker_code=f"LEAVE-W1-{ts}",
            name="Rani Devi",
            role="ASHA",
            center="Phulwari",
            phone="9876543220",
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)

        start = datetime.date.today()
        end = start + datetime.timedelta(days=4)  # 5 days inclusive

        response = client.post(
            "/api/leaves",
            json={
                "worker_id": worker.id,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "leave_type": "medical",
                "reason": "Typhoid recovery",
                "approved_by": "Dr. Verma",
            },
        )
        assert response.status_code == 200
        leave_data = response.json()
        assert leave_data["worker_id"] == worker.id
        assert leave_data["leave_type"] == "medical"

        # Check attendance records auto-populated
        att_records = (
            db.query(models.AttendanceRecord)
            .filter_by(worker_id=worker.id)
            .all()
        )
        assert len(att_records) == 5
        for r in att_records:
            assert r.status == "leave"
            assert "Typhoid recovery" in (r.note or "")
    finally:
        db.close()


def test_create_leave_updates_existing_attendance_record():
    db = SessionLocal()
    try:
        ts = int(datetime.datetime.now().timestamp() * 1000)
        worker = models.HealthWorker(
            worker_code=f"LEAVE-W2-{ts}",
            name="Sunita Kumari",
            role="ANM",
            center="Danapur",
            phone="9876543221",
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)

        day = datetime.date.today() + datetime.timedelta(days=10)
        # Pre-mark as absent
        db.add(
            models.AttendanceRecord(
                worker_id=worker.id,
                date=day,
                status="absent",
                note="Uninformed",
            )
        )
        db.commit()

        # Log leave on that same day
        response = client.post(
            "/api/leaves",
            json={
                "worker_id": worker.id,
                "start_date": day.isoformat(),
                "end_date": day.isoformat(),
                "leave_type": "casual",
                "reason": "Family function",
                "approved_by": "Supervisor A",
            },
        )
        assert response.status_code == 200

        # Existing record should now be updated to leave
        updated = (
            db.query(models.AttendanceRecord)
            .filter_by(worker_id=worker.id, date=day)
            .first()
        )
        assert updated.status == "leave"
        assert "Family function" in (updated.note or "")
    finally:
        db.close()


def test_create_leave_worker_not_found():
    response = client.post(
        "/api/leaves",
        json={
            "worker_id": 999999,
            "start_date": "2026-11-01",
            "end_date": "2026-11-03",
            "leave_type": "casual",
        },
    )
    assert response.status_code == 404
    assert "Worker not found" in response.json()["detail"]


def test_create_leave_invalid_date_range():
    db = SessionLocal()
    try:
        ts = int(datetime.datetime.now().timestamp() * 1000)
        worker = models.HealthWorker(
            worker_code=f"LEAVE-W3-{ts}",
            name="Pooja Sharma",
            role="ASHA",
            center="Maner",
            phone="9876543222",
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)

        # start_date > end_date
        response = client.post(
            "/api/leaves",
            json={
                "worker_id": worker.id,
                "start_date": "2026-11-10",
                "end_date": "2026-11-05",
                "leave_type": "casual",
            },
        )
        assert response.status_code == 400
        assert "start_date cannot be after end_date" in response.json()["detail"]
    finally:
        db.close()


def test_get_leaves_endpoint():
    response = client.get("/api/leaves")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_worker_by_id():
    db = SessionLocal()
    try:
        ts = int(datetime.datetime.now().timestamp() * 1000)
        worker = models.HealthWorker(
            worker_code=f"LEAVE-W4-{ts}",
            name="Rekha Sinha",
            role="ASHA",
            center="Bikram",
            phone="9876543223",
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)

        response = client.get(f"/api/workers/{worker.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == worker.id
        assert data["name"] == "Rekha Sinha"

        not_found = client.get("/api/workers/999999")
        assert not_found.status_code == 404
    finally:
        db.close()
