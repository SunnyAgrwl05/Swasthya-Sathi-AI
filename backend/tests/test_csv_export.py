import csv
import datetime
import io
import pytest
import models
from database import SessionLocal
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_export_csv_empty():
    """Test exporting CSV returns valid headers and content-type."""
    response = client.get("/api/attendance/export-csv")
    assert response.status_code == 200
    assert response.headers.get("content-type") == "text/csv; charset=utf-8"
    assert 'attachment; filename="swasthya_attendance_report.csv"' in response.headers.get("content-disposition", "")

    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) >= 1
    assert rows[0] == [
        "Worker Code",
        "Worker Name",
        "Role",
        "Health Center",
        "Phone",
        "Date",
        "Status",
        "Note",
        "Marked By",
    ]


def test_export_csv_with_records(db_session):
    """Test exporting CSV with populated worker attendance records."""
    code = f"ASHA-CSV-{int(datetime.datetime.now().timestamp())}"
    worker = models.HealthWorker(
        worker_code=code,
        name="Kavita Singh",
        role="ASHA",
        center="Patna Sadar PHC",
        phone="+919876543210",
    )
    db_session.add(worker)
    db_session.commit()
    db_session.refresh(worker)

    today = datetime.date.today()
    att = models.AttendanceRecord(
        worker_id=worker.id,
        date=today,
        status="present",
        note="Field immunization drive, Sector 4",
        marked_by="manual",
    )
    db_session.add(att)
    db_session.commit()

    response = client.get(f"/api/attendance/export-csv?worker_id={worker.id}")
    assert response.status_code == 200

    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) >= 2
    data_row = next(r for r in rows[1:] if r[0] == code)
    assert data_row[1] == "Kavita Singh"
    assert data_row[2] == "ASHA"
    assert data_row[3] == "Patna Sadar PHC"
    assert data_row[4] == "+919876543210"
    assert data_row[5] == today.isoformat()
    assert data_row[6] == "present"
    assert data_row[7] == "Field immunization drive, Sector 4"
    assert data_row[8] == "manual"


def test_export_csv_filtering(db_session):
    """Test filtering CSV export by worker_id and center."""
    ts = int(datetime.datetime.now().timestamp())
    w1 = models.HealthWorker(worker_code=f"ANM-A-{ts}", name="Rekha", role="ANM", center=f"CenterA_{ts}", phone="111")
    w2 = models.HealthWorker(worker_code=f"ANM-B-{ts}", name="Pooja", role="ANM", center=f"CenterB_{ts}", phone="222")
    db_session.add_all([w1, w2])
    db_session.commit()

    d = datetime.date.today()
    a1 = models.AttendanceRecord(worker_id=w1.id, date=d, status="present", marked_by="manual")
    a2 = models.AttendanceRecord(worker_id=w2.id, date=d, status="absent", marked_by="manual")
    db_session.add_all([a1, a2])
    db_session.commit()

    # Filter by worker_id
    res_w1 = client.get(f"/api/attendance/export-csv?worker_id={w1.id}")
    reader_w1 = csv.reader(io.StringIO(res_w1.text))
    rows_w1 = list(reader_w1)[1:]
    assert all(r[0] == f"ANM-A-{ts}" for r in rows_w1)

    # Filter by center
    res_center = client.get(f"/api/attendance/export-csv?center=CenterB_{ts}")
    reader_center = csv.reader(io.StringIO(res_center.text))
    rows_center = list(reader_center)[1:]
    assert all(r[3] == f"CenterB_{ts}" for r in rows_center)


def test_reports_export_csv_alias():
    """Test /api/reports/export-csv alias endpoint."""
    response = client.get("/api/reports/export-csv")
    assert response.status_code == 200
    assert "Worker Code" in response.text


def test_export_workers_csv(db_session):
    """Test /api/workers/export-csv endpoint."""
    response = client.get("/api/workers/export-csv")
    assert response.status_code == 200
    assert response.headers.get("content-type") == "text/csv; charset=utf-8"
    assert "Worker Code,Name,Role,Center,Phone" in response.text


def test_import_workers_csv(db_session):
    """Test bulk worker CSV import endpoint."""
    ts = int(datetime.datetime.now().timestamp() * 1000)
    csv_content = (
        "worker_code,name,role,center,phone\n"
        f"BULK-{ts}-1,Meera {ts},ASHA Worker,Danapur Subcenter,9876543211\n"
        f"BULK-{ts}-2,Sunita {ts},ANM,Danapur Subcenter,9876543212\n"
    )
    files = {"file": ("workers.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/workers/import-csv", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 2
    assert len(data["errors"]) == 0

    # Verify workers exist in DB
    w1 = db_session.query(models.HealthWorker).filter_by(worker_code=f"BULK-{ts}-1").first()
    assert w1 is not None
    assert w1.name == f"Meera {ts}"


def test_import_attendance_csv(db_session):
    """Test bulk attendance CSV import endpoint."""
    ts = int(datetime.datetime.now().timestamp() * 1000)
    w = models.HealthWorker(
        worker_code=f"BULK-ATT-{ts}",
        name=f"Lalita {ts}",
        role="ASHA",
        center="Patna",
        phone="9998887776",
    )
    db_session.add(w)
    db_session.commit()

    csv_content = (
        "worker_code,date,status,note\n"
        f"BULK-ATT-{ts},2026-11-01,present,Maternal health survey\n"
    )
    files = {"file": ("attendance.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/attendance/import-csv", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["processed"] == 1
    assert len(data["errors"]) == 0

