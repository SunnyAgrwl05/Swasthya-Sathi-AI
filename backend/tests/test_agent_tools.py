from unittest.mock import MagicMock, patch
from datetime import date
import models
from agent import (
    get_worker_id,
    mark_worker_attendance,
    get_attendance_summary,
    list_low_attendance_workers,
    find_absent_today,
)


def test_get_worker_id_exact_and_fuzzy(db_session):
    w = models.HealthWorker(worker_code="W-FZ", name="Rajesh Kumar", center="C1", phone="123")
    db_session.add(w)
    db_session.commit()

    with patch("agent.SessionLocal", return_value=db_session):
        wid = get_worker_id("Rajesh Kumar")
        assert wid == w.id

        # Fuzzy match test
        wid_fuzzy = get_worker_id("Rajesh")
        assert wid_fuzzy == w.id


def test_mark_worker_attendance_tool(db_session):
    w = models.HealthWorker(worker_code="W-MK", name="Pooja Sharma", center="C2", phone="456")
    db_session.add(w)
    db_session.commit()

    with patch("agent.SessionLocal", return_value=db_session):
        res = mark_worker_attendance("Pooja Sharma", "Present")
        assert "Attendance marked" in res
        assert "Present" in res


def test_find_absent_today_tool(db_session):
    w = models.HealthWorker(worker_code="W-ABS", name="Deepak Verma", center="C3", phone="789")
    db_session.add(w)
    db_session.commit()

    with patch("agent.SessionLocal", return_value=db_session):
        res = find_absent_today()
        assert "Deepak Verma" in res
