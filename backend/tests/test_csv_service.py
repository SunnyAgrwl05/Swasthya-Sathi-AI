import datetime
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from database import Base, get_db
from main import app

# Isolated In-Memory SQLite Engine
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_get_sample_csv_endpoint(client):
    response = client.get("/api/workers/sample-csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert 'filename="sample_workers_template.csv"' in response.headers["content-disposition"]
    text = response.text
    # Verify UTF-8 BOM
    assert text.startswith("\ufeff")
    assert "worker_code,name,role,center,phone" in text
    assert "Pooja Kumari" in text


def test_import_workers_csv_success(client, setup_test_db):
    csv_data = (
        "worker_code,name,role,center,phone\n"
        "W101,Asha Devi,ASHA Worker,Danapur,+91-9876543210\n"
        "W102,Kajal Kumari,ANM,Patna Central,+91-9876543211\n"
    )
    files = {"file": ("workers.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/api/workers/import-csv", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 2
    assert data["created"] == 2
    assert data["skipped"] == 0
    assert data["errors"] == []

    # Verify workers in database
    workers = setup_test_db.query(models.HealthWorker).all()
    assert len(workers) == 2
    assert {w.worker_code for w in workers} == {"W101", "W102"}


def test_import_workers_csv_deduplication(client, setup_test_db):
    # Pre-seed one worker
    existing = models.HealthWorker(
        worker_code="W101",
        name="Asha Devi",
        role="ASHA Worker",
        center="Danapur",
        phone="+91-9876543210",
        joined_on=datetime.date.today(),
    )
    setup_test_db.add(existing)
    setup_test_db.commit()

    csv_data = (
        "worker_code,name,role,center,phone\n"
        "W101,Asha Devi,ASHA Worker,Danapur,+91-9876543210\n"
        "W103,Ravi Kumar,Supervisor,Maner,+91-9876543213\n"
    )
    files = {"file": ("workers.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/api/workers/import-csv", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 2
    assert data["created"] == 1
    assert data["skipped"] == 1
    assert data["errors"] == []

    workers = setup_test_db.query(models.HealthWorker).all()
    assert len(workers) == 2


def test_import_workers_csv_missing_columns(client):
    csv_data = "name,role\nAsha Devi,ASHA\n"
    files = {"file": ("workers.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/api/workers/import-csv", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 0
    assert len(data["errors"]) > 0
    assert "Missing required columns" in data["errors"][0]


def test_import_workers_invalid_file_extension(client):
    files = {"file": ("workers.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")}
    response = client.post("/api/workers/import-csv", files=files)
    assert response.status_code == 400
    assert "Only .csv files are supported" in response.json()["detail"]


def test_export_attendance_csv_success(client, setup_test_db):
    w1 = models.HealthWorker(
        worker_code="W201",
        name="Pooja Singh",
        role="ASHA Worker",
        center="Danapur",
        phone="+91-9999999991",
        joined_on=datetime.date(2026, 11, 1),
    )
    setup_test_db.add(w1)
    setup_test_db.commit()

    # Add attendance records
    att1 = models.AttendanceRecord(
        worker_id=w1.id,
        date=datetime.date(2026, 11, 1),
        status="present",
        marked_by="manual",
    )
    att2 = models.AttendanceRecord(
        worker_id=w1.id,
        date=datetime.date(2026, 11, 2),
        status="absent",
        marked_by="manual",
    )
    setup_test_db.add_all([att1, att2])
    setup_test_db.commit()

    response = client.get("/api/attendance/export-csv?month=2026-11&center=Danapur")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert 'filename="attendance_Danapur_2026-11.csv"' in response.headers["content-disposition"]

    content = response.text
    assert content.startswith("\ufeff")
    assert "Worker Code,Name,Role,Center,Phone" in content
    assert "Day 1,Day 2,Day 3" in content
    assert "W201,Pooja Singh,ASHA Worker,Danapur" in content
    assert "50.0%" in content  # 1 present out of 2 logged days


def test_export_attendance_csv_center_filter(client, setup_test_db):
    w1 = models.HealthWorker(
        worker_code="W301",
        name="Worker One",
        role="ASHA",
        center="Patna",
        phone="111",
    )
    w2 = models.HealthWorker(
        worker_code="W302",
        name="Worker Two",
        role="ASHA",
        center="Danapur",
        phone="222",
    )
    setup_test_db.add_all([w1, w2])
    setup_test_db.commit()

    response = client.get("/api/attendance/export-csv?month=2026-11&center=Patna")
    assert response.status_code == 200
    content = response.text
    assert "Worker One" in content
    assert "Worker Two" not in content


def test_export_attendance_csv_invalid_month(client):
    response = client.get("/api/attendance/export-csv?month=invalid-date")
    assert response.status_code == 400
    assert "Invalid month format" in response.json()["detail"]
