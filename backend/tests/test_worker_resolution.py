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


@pytest.fixture
def db_session(monkeypatch):
    """Provides an isolated in-memory SQLite DB session for resolution tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    models.Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Monkeypatch SessionLocal in agent to use this in-memory DB
    monkeypatch.setattr("agent.SessionLocal", TestingSessionLocal)

    yield session
    session.close()


def test_unique_worker_resolution(db_session):
    w = models.HealthWorker(worker_code="W001", name="Amina Khatun", role="ASHA", center="Rampur", phone="9988776655")
    db_session.add(w)
    db_session.commit()

    resolved = _resolve_worker(db_session, "amina khatun")
    assert resolved is not None
    assert resolved.id == w.id
    assert resolved.name == "Amina Khatun"

    # Fuzzy match
    fuzzy = _resolve_worker(db_session, "Amina Khatu")
    assert fuzzy is not None
    assert fuzzy.id == w.id


def test_duplicate_worker_collision_raises_ambiguous_error(db_session):
    w1 = models.HealthWorker(worker_code="W002", name="Pooja Singh", role="ASHA", center="Patna Central", phone="9111111111")
    w2 = models.HealthWorker(worker_code="W003", name="Pooja Singh", role="ANM", center="Danapur", phone="9222222222")
    db_session.add_all([w1, w2])
    db_session.commit()

    with pytest.raises(AmbiguousWorkerError) as exc_info:
        _resolve_worker(db_session, "Pooja Singh")

    err_msg = str(exc_info.value)
    assert "Multiple health workers found matching 'Pooja Singh'" in err_msg
    assert "Patna Central" in err_msg
    assert "Danapur" in err_msg


def test_duplicate_worker_disambiguation_by_center(db_session):
    w1 = models.HealthWorker(worker_code="W004", name="Pooja Singh", role="ASHA", center="Patna Central", phone="9111111111")
    w2 = models.HealthWorker(worker_code="W005", name="Pooja Singh", role="ANM", center="Danapur", phone="9222222222")
    db_session.add_all([w1, w2])
    db_session.commit()

    # Disambiguate by center parameter
    resolved_patna = _resolve_worker(db_session, "Pooja Singh", center="Patna")
    assert resolved_patna.id == w1.id

    resolved_danapur = _resolve_worker(db_session, "Pooja Singh", center="Danapur")
    assert resolved_danapur.id == w2.id

    # Disambiguate by combined query string
    resolved_combined = _resolve_worker(db_session, "Pooja Singh Danapur")
    assert resolved_combined.id == w2.id


def test_mark_attendance_handles_ambiguity(db_session):
    w1 = models.HealthWorker(worker_code="W006", name="Pooja Singh", role="ASHA", center="Patna Central", phone="9111111111")
    w2 = models.HealthWorker(worker_code="W007", name="Pooja Singh", role="ANM", center="Danapur", phone="9222222222")
    db_session.add_all([w1, w2])
    db_session.commit()

    # Calling mark_attendance without center returns helpful disambiguation prompt instead of crashing
    res = mark_attendance(worker_name="Pooja Singh", status="present")
    assert "Multiple health workers found matching 'Pooja Singh'" in res

    # Calling with center succeeds
    res_success = mark_attendance(worker_name="Pooja Singh", status="present", center="Danapur")
    assert "Attendance Updated" in res_success
    assert "Danapur" in res_success


def test_newly_registered_worker_with_zero_records_not_flagged(db_session):
    today = datetime.date.today()

    # Worker 1: Veteran with low attendance (1 present out of 10 days = 10%)
    w1 = models.HealthWorker(worker_code="W008", name="Sunita Devi", role="ASHA", center="Patna Central", phone="9888888888")
    # Worker 2: Newly registered worker with 0 attendance records
    w2 = models.HealthWorker(worker_code="W009", name="Neha Kumari", role="ANM", center="Danapur", phone="9777777777")
    db_session.add_all([w1, w2])
    db_session.commit()

    for i in range(10):
        status = "present" if i == 0 else "absent"
        db_session.add(
            models.AttendanceRecord(
                worker_id=w1.id,
                date=today - datetime.timedelta(days=i + 1),
                status=status,
                marked_by="test",
            )
        )
    db_session.commit()

    # 1. Check find_low_attendance_workers
    analysis = find_low_attendance_workers(min_percent=75.0, days=30)
    assert "Sunita Devi" in analysis
    assert "Neha Kumari" not in analysis  # New worker with 0 logs must NOT be falsely flagged!

    # 2. Check generate_daily_broadcast
    broadcast = generate_daily_broadcast()
    assert "Sunita Devi" in broadcast
    assert "Neha Kumari (0.0%)" not in broadcast
    assert "Neha Kumari (0%)" not in broadcast
