
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from database import get_db
from main import app


@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    models.Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        models.Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(test_db):
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_workers_endpoint(client):
    response = client.get("/api/workers")
    assert response.status_code == 200


def test_delete_worker_success(client, test_db):
    worker = models.HealthWorker(
        worker_code="TEST001",
        name="Test Worker",
        center="Test Center",
        phone="9999999999",
    )
    test_db.add(worker)
    test_db.commit()
    test_db.refresh(worker)

    response = client.delete(f"/api/workers/{worker.id}")

    assert response.status_code == 200
    assert response.json() == {"deleted": worker.id}

    deleted_worker = (
        test_db.query(models.HealthWorker)
        .filter_by(id=worker.id)
        .first()
    )
    assert deleted_worker is None


def test_delete_nonexistent_worker(client):
    response = client.delete("/api/workers/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Worker not found"
