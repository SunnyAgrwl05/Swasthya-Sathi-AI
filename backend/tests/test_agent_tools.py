from unittest.mock import patch
from datetime import date
import models
from agent import (
    _resolve_worker,
    mark_attendance,
    who_has_not_marked_today,
)


def test_resolve_worker_exact_and_fuzzy(db_session):
    w = models.HealthWorker(worker_code="W-FZ", name="Rajesh Kumar", center="C1", phone="123")
    db_session.add(w)
    db_session.commit()

    resolved = _resolve_worker(db_session, "Rajesh Kumar")
    assert resolved is not None
    assert resolved.id == w.id

    # Fuzzy match test
    resolved_fuzzy = _resolve_worker(db_session, "Rajesh")
    assert resolved_fuzzy is not None
    assert resolved_fuzzy.id == w.id


def test_mark_attendance_tool(db_session):
    w = models.HealthWorker(worker_code="W-MK", name="Pooja Sharma", center="C2", phone="456")
    db_session.add(w)
    db_session.commit()

    with patch("agent.SessionLocal", return_value=db_session):
        res = mark_attendance("Pooja Sharma", "Present")
        assert "Pooja Sharma" in res
        assert "Present" in res


def test_who_has_not_marked_today_tool(db_session):
    w = models.HealthWorker(worker_code="W-ABS", name="Deepak Verma", center="C3", phone="789")
    db_session.add(w)
    db_session.commit()

    with patch("agent.SessionLocal", return_value=db_session):
        res = who_has_not_marked_today()
        assert "Deepak Verma" in res

