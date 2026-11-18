import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from agent import (
    AmbiguousWorkerError,
    _resolve_worker,
    find_low_attendance_workers,
    generate_daily_broadcast,
    mark_attendance,
)
from database import Base

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    monkeypatch.setattr("agent.SessionLocal", lambda: db)
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def test_resolve_worker_unique(setup_test_db):
    w1 = models.HealthWorker(
        worker_code="HW101",
        name="Sunita Devi",
        role="ASHA Worker",
        center="Patna Central",
        phone="111",
    )
    setup_test_db.add(w1)
    setup_test_db.commit()

    resolved = _resolve_worker(setup_test_db, "Sunita Devi")
    assert resolved is not None
    assert resolved.worker_code == "HW101"

    # Fuzzy match
    fuzzy = _resolve_worker(setup_test_db, "sunita dev")
    assert fuzzy is not None
    assert fuzzy.worker_code == "HW101"


def test_resolve_worker_collision_raises_ambiguous_error(setup_test_db):
    w1 = models.HealthWorker(
        worker_code="HW201",
        name="Pooja Singh",
        role="ASHA Worker",
        center="Patna Central",
        phone="222",
    )
    w2 = models.HealthWorker(
        worker_code="HW202",
        name="Pooja Singh",
        role="ANM",
        center="Danapur",
        phone="333",
    )
    setup_test_db.add_all([w1, w2])
    setup_test_db.commit()

    # Calling with duplicate name should raise AmbiguousWorkerError
    with pytest.raises(AmbiguousWorkerError) as exc_info:
        _resolve_worker(setup_test_db, "Pooja Singh")

    err_msg = str(exc_info.value)
    assert "Multiple health workers found matching 'Pooja Singh'" in err_msg
    assert "Patna Central" in err_msg
    assert "Danapur" in err_msg


def test_resolve_worker_disambiguation_by_center(setup_test_db):
    w1 = models.HealthWorker(
        worker_code="HW201",
        name="Pooja Singh",
        role="ASHA Worker",
        center="Patna Central",
        phone="222",
    )
    w2 = models.HealthWorker(
        worker_code="HW202",
        name="Pooja Singh",
        role="ANM",
        center="Danapur",
        phone="333",
    )
    setup_test_db.add_all([w1, w2])
    setup_test_db.commit()

    # Disambiguate by center parameter
    resolved_patna = _resolve_worker(setup_test_db, "Pooja Singh", center="Patna Central")
    assert resolved_patna.worker_code == "HW201"

    resolved_danapur = _resolve_worker(setup_test_db, "Pooja Singh", center="Danapur")
    assert resolved_danapur.worker_code == "HW202"

    # Disambiguate by combined string query
    resolved_query = _resolve_worker(setup_test_db, "Pooja Singh Danapur")
    assert resolved_query.worker_code == "HW202"


def test_mark_attendance_ambiguous_collision_prompt(setup_test_db):
    w1 = models.HealthWorker(
        worker_code="HW301",
        name="Anita Kumari",
        role="ASHA Worker",
        center="Maner",
        phone="444",
    )
    w2 = models.HealthWorker(
        worker_code="HW302",
        name="Anita Kumari",
        role="ASHA Worker",
        center="Bakhtiyarpur",
        phone="555",
    )
    setup_test_db.add_all([w1, w2])
    setup_test_db.commit()

    # mark_attendance should gracefully notify the supervisor
    res = mark_attendance("Anita Kumari", "present")
    assert "Multiple health workers found matching 'Anita Kumari'" in res
    assert "Maner" in res
    assert "Bakhtiyarpur" in res


def test_new_hire_not_falsely_flagged_for_delinquency(setup_test_db):
    # Active worker with high attendance
    w_active = models.HealthWorker(
        worker_code="HW401",
        name="Active Worker",
        role="ASHA",
        center="Center A",
        phone="101",
    )
    # Newly onboarded worker with 0 attendance records
    w_new = models.HealthWorker(
        worker_code="HW402",
        name="New Hire",
        role="ASHA",
        center="Center B",
        phone="102",
        joined_on=datetime.date.today(),
    )
    setup_test_db.add_all([w_active, w_new])
    setup_test_db.commit()

    # Add 10 present records for active worker
    today = datetime.date.today()
    for i in range(10):
        setup_test_db.add(
            models.AttendanceRecord(
                worker_id=w_active.id,
                date=today - datetime.timedelta(days=i),
                status="present",
                marked_by="agent",
            )
        )
    setup_test_db.commit()

    # 1. find_low_attendance_workers should NOT flag the new hire under disciplinary action
    analysis = find_low_attendance_workers()
    assert "New Hire" not in analysis or "Newly Onboarded" in analysis
    assert "All health workers with logged records have maintained attendance above" in analysis or "No follow-up required" in analysis

    # 2. generate_daily_broadcast should NOT list New Hire under 0.0% low attendance
    broadcast = generate_daily_broadcast()
    assert "New Hire (0.0%)" not in broadcast
