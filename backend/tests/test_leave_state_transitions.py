import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from database import get_db
from main import app


@pytest.fixture
def client_and_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    models.Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    yield client, session

    app.dependency_overrides.clear()
    session.close()


def test_leave_state_transitions(client_and_db):
    client, db = client_and_db

    # Create worker
    worker = models.HealthWorker(
        worker_code="W100",
        name="Pooja Verma",
        role="ASHA",
        center="Patna Sadar",
        phone="9876543210",
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)

    today = datetime.date.today()
    day1 = today
    day2 = today + datetime.timedelta(days=1)

    # 1. Apply Leave
    create_resp = client.post(
        "/api/leaves",
        json={
            "worker_id": worker.id,
            "start_date": day1.isoformat(),
            "end_date": day2.isoformat(),
            "leave_type": "sick",
            "reason": "Viral fever recovery",
            "approved_by": "Dr. Sharma",
        },
    )
    assert create_resp.status_code == 200
    leave_data = create_resp.json()
    leave_id = leave_data["id"]
    assert leave_data["status"] == "Approved"

    # Verify attendance records created
    records = (
        db.query(models.AttendanceRecord)
        .filter_by(worker_id=worker.id)
        .all()
    )
    assert len(records) == 2
    assert all(r.status == "leave" for r in records)

    # 2. Transition from Approved to Rejected
    reject_resp = client.patch(
        f"/api/leaves/{leave_id}/status",
        json={"status": "Rejected", "approved_by": "Chief Medical Officer"},
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "Rejected"

    # Attendance records should be cleared
    records_after_reject = (
        db.query(models.AttendanceRecord)
        .filter_by(worker_id=worker.id)
        .all()
    )
    assert len(records_after_reject) == 0

    # 3. Transition from Rejected back to Approved
    reapprove_resp = client.patch(
        f"/api/leaves/{leave_id}/status",
        json={"status": "Approved", "approved_by": "Director Health Services"},
    )
    assert reapprove_resp.status_code == 200
    assert reapprove_resp.json()["status"] == "Approved"

    records_after_reapprove = (
        db.query(models.AttendanceRecord)
        .filter_by(worker_id=worker.id)
        .all()
    )
    assert len(records_after_reapprove) == 2
    assert all(r.status == "leave" for r in records_after_reapprove)

    # 4. Invalid status transition returns 400
    invalid_resp = client.patch(
        f"/api/leaves/{leave_id}/status",
        json={"status": "UnknownStatus", "approved_by": "Supervisor"},
    )
    assert invalid_resp.status_code == 400
