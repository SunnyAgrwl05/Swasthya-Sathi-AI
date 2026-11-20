import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models
from agent import (
    _resolve_worker,
    mark_attendance,
    get_attendance_summary,
    generate_daily_broadcast,
    find_low_attendance_workers,
)
from database import Base


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed test workers including two workers with the exact same name across different centers
    worker1 = models.HealthWorker(
        worker_code="ASHA-PAT-001",
        name="Pooja Singh",
        role="ASHA Worker",
        center="Patna Central",
        phone="9876543210",
    )
    worker2 = models.HealthWorker(
        worker_code="ASHA-DAN-002",
        name="Pooja Singh",
        role="ASHA Worker",
        center="Danapur",
        phone="9876543211",
    )
    worker3 = models.HealthWorker(
        worker_code="ANM-PAT-003",
        name="Anita Devi",
        role="ANM",
        center="Patna Central",
        phone="9876543212",
    )
    # A newly registered worker with zero logged attendance records
    new_worker = models.HealthWorker(
        worker_code="ASHA-NEW-004",
        name="Kavita Kumari",
        role="ASHA Worker",
        center="Phulwari Sharif",
        phone="9876543213",
        joined_on=datetime.date.today(),
    )

    db.add_all([worker1, worker2, worker3, new_worker])
    db.commit()

    # Seed some attendance records for worker3 (high attendance)
    today = datetime.date.today()
    for i in range(10):
        db.add(
            models.AttendanceRecord(
                worker_id=worker3.id,
                date=today - datetime.timedelta(days=i),
                status="present",
                marked_by="manual",
            )
        )
    # Seed 1 record for worker1 (poor attendance: 1 absent, 0 present)
    db.add(
        models.AttendanceRecord(
            worker_id=worker1.id,
            date=today - datetime.timedelta(days=1),
            status="absent",
            marked_by="manual",
        )
    )
    db.commit()

    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def test_resolve_worker_unique(test_db):
    worker = _resolve_worker(test_db, "Anita Devi")
    assert worker is not None
    assert isinstance(worker, models.HealthWorker)
    assert worker.name == "Anita Devi"


def test_resolve_worker_name_collision_returns_clarification(test_db):
    result = _resolve_worker(test_db, "Pooja Singh")
    assert isinstance(result, str)
    assert "Multiple workers found for 'Pooja Singh'" in result
    assert "Patna Central" in result
    assert "Danapur" in result
    assert "Please specify the center" in result


def test_resolve_worker_disambiguation_with_center_param(test_db):
    worker = _resolve_worker(test_db, "Pooja Singh", center="Danapur")
    assert isinstance(worker, models.HealthWorker)
    assert worker.name == "Pooja Singh"
    assert worker.center == "Danapur"
    assert worker.worker_code == "ASHA-DAN-002"


def test_resolve_worker_disambiguation_with_embedded_center(test_db):
    worker = _resolve_worker(test_db, "Pooja Singh at Patna Central")
    assert isinstance(worker, models.HealthWorker)
    assert worker.name == "Pooja Singh"
    assert worker.center == "Patna Central"
    assert worker.worker_code == "ASHA-PAT-001"


def test_resolve_worker_not_found(test_db):
    worker = _resolve_worker(test_db, "Nonexistent Person")
    assert worker is None


def test_mark_attendance_clarification_on_duplicate_worker(test_db, monkeypatch):
    # Point SessionLocal in agent to our test_db engine
    import agent
    monkeypatch.setattr(agent, "SessionLocal", lambda: test_db)

    result = mark_attendance("Pooja Singh", "present")
    assert "Multiple workers found for 'Pooja Singh'" in result
    assert "Please specify the center" in result


def test_mark_attendance_success_with_center(test_db, monkeypatch):
    import agent
    monkeypatch.setattr(agent, "SessionLocal", lambda: test_db)

    result = mark_attendance("Pooja Singh", "present", center="Danapur")
    assert "✅ Attendance Updated" in result
    assert "Pooja Singh" in result
    assert "Danapur" in result


def test_get_attendance_summary_clarification_on_duplicate_worker(test_db, monkeypatch):
    import agent
    monkeypatch.setattr(agent, "SessionLocal", lambda: test_db)

    result = get_attendance_summary("Pooja Singh")
    assert "Multiple workers found for 'Pooja Singh'" in result
    assert "Please specify the center" in result


def test_get_attendance_summary_success_with_center(test_db, monkeypatch):
    import agent
    monkeypatch.setattr(agent, "SessionLocal", lambda: test_db)

    result = get_attendance_summary("Pooja Singh", center="Danapur")
    assert "Pooja Singh" in result
    assert "Danapur" in result


def test_zero_record_worker_excluded_from_delinquency(test_db, monkeypatch):
    import agent
    monkeypatch.setattr(agent, "SessionLocal", lambda: test_db)

    # find_low_attendance_workers should flag worker1 (0% attendance with records),
    # but must NOT flag new_worker (Kavita Kumari with 0 records)
    res = find_low_attendance_workers(min_percent=75.0, days=30)
    assert "Pooja Singh" in res
    assert "Kavita Kumari" not in res


def test_daily_broadcast_excludes_zero_record_worker_from_delinquency(test_db, monkeypatch):
    import agent
    monkeypatch.setattr(agent, "SessionLocal", lambda: test_db)

    broadcast = generate_daily_broadcast()
    assert "Swasthya Sathi AI — Daily Update" in broadcast
    # New worker Kavita Kumari should appear under Pending Attendance, NOT under Follow-up delinquency
    if "Workers Requiring Follow-up" in broadcast:
        followup_section = broadcast.split("Workers Requiring Follow-up")[1].split("Operational Recommendation")[0]
        assert "Kavita Kumari" not in followup_section
