"""Regression tests for worker resolution and new-hire attendance handling."""

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
    """Provide an isolated in-memory database for agent worker-resolution tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    models.Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    session = testing_session_local()
    monkeypatch.setattr("agent.SessionLocal", testing_session_local)

    yield session

    session.close()
    engine.dispose()


def _add_worker(db_session, code, name, role, center, phone):
    worker = models.HealthWorker(
        worker_code=code,
        name=name,
        role=role,
        center=center,
        phone=phone,
    )
    db_session.add(worker)
    db_session.commit()
    return worker


def test_unique_worker_resolution_and_fuzzy_match(db_session):
    worker = _add_worker(
        db_session, "W001", "Amina Khatun", "ASHA", "Rampur", "9988776655"
    )

    resolved = _resolve_worker(db_session, "amina khatun")
    assert resolved.id == worker.id

    fuzzy = _resolve_worker(db_session, "Amina Khatu")
    assert fuzzy.id == worker.id


def test_duplicate_worker_name_requires_disambiguation(db_session):
    patna = _add_worker(
        db_session, "W002", "Pooja Singh", "ASHA", "Patna Central", "9111111111"
    )
    danapur = _add_worker(
        db_session, "W003", "Pooja Singh", "ANM", "Danapur", "9222222222"
    )

    with pytest.raises(AmbiguousWorkerError) as exc_info:
        _resolve_worker(db_session, "Pooja Singh")

    message = str(exc_info.value)
    assert "Multiple health workers found matching 'Pooja Singh'" in message
    assert "Patna Central" in message
    assert "Danapur" in message

    assert _resolve_worker(db_session, "Pooja Singh", center="Patna").id == patna.id
    assert _resolve_worker(db_session, "Pooja Singh", center="Danapur").id == danapur.id
    assert _resolve_worker(db_session, "Pooja Singh Danapur").id == danapur.id
    assert _resolve_worker(db_session, f"#{patna.id}").id == patna.id
    assert _resolve_worker(db_session, f"id: {danapur.id}").id == danapur.id


def test_mark_attendance_does_not_update_wrong_duplicate_worker(db_session):
    _add_worker(
        db_session, "W006", "Pooja Singh", "ASHA", "Patna Central", "9111111111"
    )
    danapur = _add_worker(
        db_session, "W007", "Pooja Singh", "ANM", "Danapur", "9222222222"
    )

    ambiguous = mark_attendance(worker_name="Pooja Singh", status="present")
    assert "Multiple health workers found" in ambiguous
    assert db_session.query(models.AttendanceRecord).count() == 0

    success = mark_attendance(
        worker_name="Pooja Singh",
        status="present",
        center="Danapur",
    )
    assert "Attendance Updated" in success
    assert "Danapur" in success

    records = db_session.query(models.AttendanceRecord).all()
    assert len(records) == 1
    assert records[0].worker_id == danapur.id


def test_new_hire_without_attendance_records_is_not_flagged(db_session):
    today = datetime.date.today()
    veteran = _add_worker(
        db_session, "W008", "Sunita Devi", "ASHA", "Patna Central", "9888888888"
    )
    _add_worker(
        db_session, "W009", "Neha Kumari", "ANM", "Danapur", "9777777777"
    )

    for day_offset in range(10):
        status = "present" if day_offset == 0 else "absent"
        db_session.add(
            models.AttendanceRecord(
                worker_id=veteran.id,
                date=today - datetime.timedelta(days=day_offset + 1),
                status=status,
                marked_by="test",
            )
        )
    db_session.commit()

    analysis = find_low_attendance_workers(min_percent=75.0, days=30)
    assert "Sunita Devi" in analysis
    assert "Neha Kumari" not in analysis

    broadcast = generate_daily_broadcast()
    assert "Sunita Devi" in broadcast
    assert "Neha Kumari (0.0%)" not in broadcast
    assert "Neha Kumari (0%)" not in broadcast
