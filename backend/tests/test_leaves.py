import datetime
from fastapi.testclient import TestClient

from database import Base, SessionLocal, engine
from main import app
import models

client = TestClient(app)


def setup_function():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Clean tables
    db.query(models.LeaveRecord).delete()
    db.query(models.AttendanceRecord).delete()
    db.query(models.HealthWorker).delete()
    db.commit()

    # Create a test worker
    worker = models.HealthWorker(
        worker_code="TEST-ASHA-001",
        name="Sunita Sharma",
        role="ASHA Worker",
        center="Patna Central",
        phone="9988776655",
    )
    db.add(worker)
    db.commit()
    db.close()


def test_create_leave_and_auto_populate_attendance():
    db = SessionLocal()
    worker = db.query(models.HealthWorker).filter_by(worker_code="TEST-ASHA-001").first()
    worker_id = worker.id
    db.close()

    start_date = "2026-11-01"
    end_date = "2026-11-05"  # 5 days: 1, 2, 3, 4, 5

    payload = {
        "worker_id": worker_id,
        "start_date": start_date,
        "end_date": end_date,
        "leave_type": "medical",
        "reason": "Viral fever recovery",
        "approved_by": "Dr. Verma",
    }

    res = client.post("/api/leaves", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["worker_id"] == worker_id
    assert data["start_date"] == start_date
    assert data["end_date"] == end_date
    assert data["leave_type"] == "medical"
    assert data["reason"] == "Viral fever recovery"
    assert data["approved_by"] == "Dr. Verma"

    # Verify 5 daily attendance records were created as "leave"
    att_res = client.get(f"/api/attendance?worker_id={worker_id}")
    assert att_res.status_code == 200
    records = att_res.json()
    assert len(records) == 5

    record_dates = [r["date"] for r in records]
    for expected_day in ["2026-11-01", "2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05"]:
        assert expected_day in record_dates

    for r in records:
        assert r["status"] == "leave"
        assert r["note"] == "Viral fever recovery"
        assert r["marked_by"] == "Dr. Verma"


def test_create_leave_updates_existing_attendance_record():
    db = SessionLocal()
    worker = db.query(models.HealthWorker).filter_by(worker_code="TEST-ASHA-001").first()
    worker_id = worker.id

    # Pre-seed an existing record for 2026-11-02 as "absent"
    db.add(
        models.AttendanceRecord(
            worker_id=worker_id,
            date=datetime.date(2026, 11, 2),
            status="absent",
            note="Unexplained absence",
            marked_by="manual",
        )
    )
    db.commit()
    db.close()

    # Log 3-day leave covering that date
    payload = {
        "worker_id": worker_id,
        "start_date": "2026-11-01",
        "end_date": "2026-11-03",
        "leave_type": "casual",
        "reason": "Family function",
        "approved_by": "Supervisor Anita",
    }
    res = client.post("/api/leaves", json=payload)
    assert res.status_code == 200

    # Query attendance records
    att_res = client.get(f"/api/attendance?worker_id={worker_id}")
    records = att_res.json()
    assert len(records) == 3

    nov_2 = next(r for r in records if r["date"] == "2026-11-02")
    assert nov_2["status"] == "leave"
    assert nov_2["note"] == "Family function"
    assert nov_2["marked_by"] == "Supervisor Anita"


def test_create_leave_worker_not_found():
    res = client.post(
        "/api/leaves",
        json={
            "worker_id": 99999,
            "start_date": "2026-11-01",
            "end_date": "2026-11-02",
            "leave_type": "casual",
        },
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Worker not found"


def test_create_leave_invalid_date_range():
    db = SessionLocal()
    worker = db.query(models.HealthWorker).filter_by(worker_code="TEST-ASHA-001").first()
    worker_id = worker.id
    db.close()

    res = client.post(
        "/api/leaves",
        json={
            "worker_id": worker_id,
            "start_date": "2026-11-10",
            "end_date": "2026-11-05",  # start > end
            "leave_type": "casual",
        },
    )
    assert res.status_code == 400
    assert "start_date cannot be after end_date" in res.json()["detail"]


def test_get_leaves_endpoint():
    db = SessionLocal()
    worker = db.query(models.HealthWorker).filter_by(worker_code="TEST-ASHA-001").first()
    worker_id = worker.id
    db.close()

    # Create leave
    client.post(
        "/api/leaves",
        json={
            "worker_id": worker_id,
            "start_date": "2026-11-10",
            "end_date": "2026-11-12",
            "leave_type": "annual",
            "reason": "Vacation",
        },
    )

    res = client.get("/api/leaves")
    assert res.status_code == 200
    leaves = res.json()
    assert len(leaves) >= 1
    assert leaves[0]["leave_type"] == "annual"

    res_worker = client.get(f"/api/leaves?worker_id={worker_id}")
    assert res_worker.status_code == 200
    assert len(res_worker.json()) >= 1


def test_get_worker_by_id():
    db = SessionLocal()
    worker = db.query(models.HealthWorker).filter_by(worker_code="TEST-ASHA-001").first()
    worker_id = worker.id
    db.close()

    res = client.get(f"/api/workers/{worker_id}")
    assert res.status_code == 200
    assert res.json()["name"] == "Sunita Sharma"

    res_404 = client.get("/api/workers/99999")
    assert res_404.status_code == 404
