import datetime
from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402
import models  # noqa: E402

# In-memory SQLite database for isolated test execution
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Provides a transactional database session per test function."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Provides a FastAPI TestClient with the database dependency overridden."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_worker(db_session):
    """Seeds a single active health worker into the test database."""
    worker = models.HealthWorker(
        worker_code="ASHA-PAT-001",
        name="Sunita Devi",
        role="ASHA Worker",
        center="PHC Patna",
        phone="9876543210",
    )
    db_session.add(worker)
    db_session.commit()
    db_session.refresh(worker)
    return worker


@pytest.fixture
def sample_attendance(db_session, sample_worker):
    """Seeds attendance records for the sample health worker."""
    today = datetime.date.today()
    records = []
    # Seed 5 days of attendance
    for i in range(5):
        day = today - datetime.timedelta(days=i)
        rec = models.AttendanceRecord(
            worker_id=sample_worker.id,
            date=day,
            status="present" if i < 4 else "absent",
            note="Regular field check",
        )
        db_session.add(rec)
        records.append(rec)
    db_session.commit()
    return records
