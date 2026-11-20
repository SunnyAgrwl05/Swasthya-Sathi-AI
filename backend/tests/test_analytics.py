from datetime import date
import models


def test_analytics_summary_empty(client):
    res = client.get("/api/analytics/summary")
    assert res.status_code == 200
    assert res.json() == []


def test_analytics_summary_with_records(client, db_session):
    w1 = models.HealthWorker(worker_code="W10", name="Worker 10", center="Center A", phone="111")
    w2 = models.HealthWorker(worker_code="W20", name="Worker 20", center="Center B", phone="222")
    db_session.add_all([w1, w2])
    db_session.commit()

    today = date.today()
    r1 = models.AttendanceRecord(worker_id=w1.id, date=today, status="present")
    r2 = models.AttendanceRecord(worker_id=w2.id, date=today, status="absent")
    db_session.add_all([r1, r2])
    db_session.commit()

    res = client.get("/api/analytics/summary?days=7")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    # Verify workers are present in results with attendance_pct calculated
    w1_item = next(item for item in data if item["worker_id"] == w1.id)
    assert w1_item["present"] == 1
    assert w1_item["total_logged"] == 1
    assert w1_item["attendance_pct"] == 100.0


def test_analytics_summary_sorting_order(client, db_session):
    w1 = models.HealthWorker(worker_code="W_HIGH", name="High Worker", center="Center A", phone="111")
    w2 = models.HealthWorker(worker_code="W_LOW", name="Low Worker", center="Center B", phone="222")
    db_session.add_all([w1, w2])
    db_session.commit()

    r1 = models.AttendanceRecord(worker_id=w1.id, date=date.today(), status="present")
    r2 = models.AttendanceRecord(worker_id=w2.id, date=date.today(), status="absent")
    db_session.add_all([r1, r2])
    db_session.commit()

    res = client.get("/api/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    # Sorted ascending by attendance_pct
    assert data[0]["attendance_pct"] <= data[1]["attendance_pct"]

