import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from sms_dispatcher import (
    deserialize_sms_queue,
    enqueue_sms_alert,
    process_offline_sms_queue,
    serialize_sms_queue,
)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    models.Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


def test_enqueue_sms_and_serialization(db_session):
    # 1. Enqueue SMS alert
    item = enqueue_sms_alert(
        db=db_session,
        phone="9876543210",
        message="Monthly maternal health review meeting scheduled for Friday 10 AM.",
        worker_name="Sunita Devi",
        max_retries=3,
        retry_interval_seconds=60,
    )

    assert item.id is not None
    assert item.worker_name == "Sunita Devi"
    assert item.status == "pending"
    assert item.attempts == 0

    # 2. Test JSON Serialization
    json_data = serialize_sms_queue([item])
    assert "Sunita Devi" in json_data
    assert "9876543210" in json_data
    assert "pending" in json_data

    # 3. Test JSON Deserialization
    parsed = deserialize_sms_queue(json_data)
    assert len(parsed) == 1
    assert parsed[0]["worker_name"] == "Sunita Devi"
    assert parsed[0]["phone"] == "9876543210"
    assert parsed[0]["status"] == "pending"


def test_process_offline_sms_queue_success(db_session):
    item = enqueue_sms_alert(
        db=db_session,
        phone="9876543210",
        message="Reminder: update polio immunization logs.",
        worker_name="Anita Kumari",
    )

    summary = process_offline_sms_queue(db_session)
    assert summary["processed"] == 1
    assert summary["sent"] == 1
    assert summary["failed"] == 0

    db_session.refresh(item)
    assert item.status == "sent"
    assert item.attempts == 1
    assert item.last_error is None

    # Audit log created
    log = db_session.query(models.NotificationLog).filter_by(phone="9876543210").first()
    assert log is not None
    assert log.status == "Sent"


def test_process_offline_sms_queue_retry_and_exhaustion(db_session):
    # Enqueue with invalid phone number to trigger transmission failure in sandbox/cloud
    item = enqueue_sms_alert(
        db=db_session,
        phone="123",  # invalid short number
        message="Test alert",
        worker_name="Test Worker",
        max_retries=2,
        retry_interval_seconds=30,
    )

    # First attempt: should retry
    summary1 = process_offline_sms_queue(db_session)
    assert summary1["processed"] == 1
    assert summary1["retrying"] == 1
    assert summary1["sent"] == 0

    db_session.refresh(item)
    assert item.status == "pending"
    assert item.attempts == 1
    assert item.last_error is not None
    assert item.next_retry_at > datetime.datetime.utcnow()

    # Second attempt: advance time to allow retry
    future_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=120)
    summary2 = process_offline_sms_queue(db_session, now=future_time)
    assert summary2["processed"] == 1
    assert summary2["failed"] == 1

    db_session.refresh(item)
    assert item.status == "failed"
    assert item.attempts == 2

    # NotificationLog marked as Failed
    log = db_session.query(models.NotificationLog).filter_by(worker_name="Test Worker").first()
    assert log is not None
    assert log.status == "Failed"
