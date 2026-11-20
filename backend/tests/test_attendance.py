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
