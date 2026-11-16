from datetime import date, timedelta
import models


def test_analytics_summary_empty(client):
    res = client.get("/api/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_workers" in data
    assert data["total_workers"] == 0
    assert data["attendance_rate"] == 0


def test_analytics_summary_with_records(client, db_session):
    w1 = models.HealthWorker(worker_code="W10", name="Worker 10", center="Center A", phone="111")
    w2 = models.HealthWorker(worker_code="W20", name="Worker 20", center="Center B", phone="222")
    db_session.add_all([w1, w2])
    db_session.commit()

    today = date.today()
    r1 = models.AttendanceRecord(worker_id=w1.id, date=today, status="Present")
    r2 = models.AttendanceRecord(worker_id=w2.id, date=today, status="Absent")
    db_session.add_all([r1, r2])
    db_session.commit()

    res = client.get("/api/analytics/summary?days=7")
    assert res.status_code == 200
    data = res.json()
    assert data["total_workers"] == 2
    assert data["attendance_rate"] == 50.0
    assert data["center_breakdown"]["Center A"]["present"] == 1


def test_low_attendance_endpoint(client, db_session):
    w = models.HealthWorker(worker_code="W_LOW", name="Low Worker", center="Center C", phone="333")
    db_session.add(w)
    db_session.commit()

    for i in range(5):
        r = models.AttendanceRecord(
            worker_id=w.id,
            date=date.today() - timedelta(days=i),
            status="Absent" if i < 4 else "Present"
        )
        db_session.add(r)
    db_session.commit()

    res = client.get("/api/analytics/low-attendance?threshold=50")
    assert res.status_code == 200
    results = res.json()
    assert len(results) == 1
    assert results[0]["worker_name"] == "Low Worker"
    assert results[0]["attendance_pct"] == 20.0
