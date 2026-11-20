"""Unit tests for worker leave management and 30-day attendance heatmap (closes #58)."""

import datetime
from fastapi.testclient import TestClient
from main import app
import models
from database import SessionLocal

client = TestClient(app)


def test_create_leave_success():
    db = SessionLocal()
    try:
        ts = int(datetime.datetime.now().timestamp() * 1000)
        worker = models.HealthWorker(
            worker_code=f"LEAVE-W-{ts}",
            name=f"Sunita Leave {ts}",
            role="ASHA",
            center="Danapur Subcenter",
            phone="9876543210",
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)

        start = datetime.date.today()
        end = start + datetime.timedelta(days=4)  # 5 days total

        payload = {
            "worker_id": worker.id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "leave_type": "maternity",
            "reason": "Maternity leave first term",
            "approved_by": "Dr. Sharma",
        }
        res = client.post("/api/leaves", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["leave_type"] == "maternity"
        assert data["worker_id"] == worker.id
        assert data["status"] == "Approved"

        # Verify daily attendance records were populated
        records = (
            db.query(models.AttendanceRecord)
            .filter_by(worker_id=worker.id)
            .order_by(models.AttendanceRecord.date.asc())
            .all()
        )
        assert len(records) == 5
        for r in records:
            assert r.status == "leave"
            assert "Maternity" in r.note
            assert r.marked_by == "Dr. Sharma"
    finally:
        db.close()


def test_create_leave_invalid_dates():
    db = SessionLocal()
    try:
        ts = int(datetime.datetime.now().timestamp() * 1000)
        worker = models.HealthWorker(
            worker_code=f"LEAVE-INV-{ts}",
            name="Invalid Date Worker",
            role="ANM",
            center="Patna",
            phone="9998887776",
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)

        start = datetime.date.today()
        end = start - datetime.timedelta(days=2)  # Invalid: end before start

        payload = {
            "worker_id": worker.id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "leave_type": "sick",
        }
        res = client.post("/api/leaves", json=payload)
        assert res.status_code == 400
        assert "start_date must be on or before end_date" in res.json()["detail"]
    finally:
        db.close()


def test_create_leave_worker_not_found():
    payload = {
        "worker_id": 999999,
        "start_date": "2026-11-01",
        "end_date": "2026-11-05",
        "leave_type": "casual",
    }
    res = client.post("/api/leaves", json=payload)
    assert res.status_code == 404
    assert "Worker not found" in res.json()["detail"]


def test_get_leaves_endpoint():
    res = client.get("/api/leaves")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_worker_attendance_history_heatmap():
    db = SessionLocal()
    try:
        ts = int(datetime.datetime.now().timestamp() * 1000)
        worker = models.HealthWorker(
            worker_code=f"HEATMAP-W-{ts}",
            name=f"Pooja Heatmap {ts}",
            role="ASHA",
            center="Patna Sadar",
            phone="9123456780",
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)

        today = datetime.date.today()
        # Mark present today
        att = models.AttendanceRecord(
            worker_id=worker.id,
            date=today,
            status="present",
            note="Field inspection",
            marked_by="Supervisor",
        )
        db.add(att)
        db.commit()

        res = client.get(f"/api/workers/{worker.id}/attendance-history?days=30")
        assert res.status_code == 200
        data = res.json()
        assert data["worker_id"] == worker.id
        assert data["total_days"] == 30
        assert len(data["days"]) == 30
        assert data["present_days"] >= 1

        today_item = next(d for d in data["days"] if d["date"] == today.isoformat())
        assert today_item["status"] == "present"
    finally:
        db.close()
