"""Unit tests for the multi-channel SMS notification dispatch engine (closes #57)."""

import datetime
from fastapi.testclient import TestClient
from main import app
import models
from database import SessionLocal
from sms_dispatcher import (
    sanitize_phone_number,
    send_sms_sandbox,
    transmit_sms,
    dispatch_worker_notification,
    dispatch_batch_broadcast_sms,
)

client = TestClient(app)


def test_sanitize_phone_number():
    assert sanitize_phone_number("+919876543210") == "9876543210"
    assert sanitize_phone_number("09876543210") == "9876543210"
    assert sanitize_phone_number("9876543210") == "9876543210"
    assert sanitize_phone_number("+91 98765-43210") == "9876543210"
    assert sanitize_phone_number("123") == "123"


def test_send_sms_sandbox():
    success = send_sms_sandbox("9876543210", "Hello ASHA Worker")
    assert success["success"] is True
    assert success["provider"] == "sandbox"
    assert "SMS_SANDBOX_" in success["message_id"]

    fail = send_sms_sandbox("123", "Too short")
    assert fail["success"] is False
    assert "Invalid recipient" in fail["error"]


def test_transmit_sms_fallback():
    res = transmit_sms("+919988776655", "Daily health advisory")
    assert res["success"] is True
    assert res["provider"] == "sandbox"


def test_dispatch_worker_notification():
    db = SessionLocal()
    try:
        log = dispatch_worker_notification(
            db=db,
            worker_name="Kavita Test",
            phone="9876543219",
            message="Morning check-in reminder",
            notification_type="SMS",
        )
        assert log.id is not None
        assert log.status == "Sent"
        assert log.notification_type == "SMS"
        assert log.worker_name == "Kavita Test"
    finally:
        db.close()


def test_dispatch_batch_broadcast_sms():
    db = SessionLocal()
    try:
        ts = int(datetime.datetime.now().timestamp() * 1000)
        w1 = models.HealthWorker(worker_code=f"SMS-W1-{ts}", name="Worker 1", role="ASHA", center="Patna", phone="9876543211")
        w2 = models.HealthWorker(worker_code=f"SMS-W2-{ts}", name="Worker 2", role="ASHA", center="Danapur", phone="9876543212")
        db.add_all([w1, w2])
        db.commit()

        summary = dispatch_batch_broadcast_sms(db, [w1, w2], "Polio drive alert")
        assert summary["total"] == 2
        assert summary["sent"] == 2
        assert summary["failed"] == 0
    finally:
        db.close()


def test_api_dispatch_sms_endpoint():
    response = client.post(
        "/api/notifications/dispatch-sms",
        json={"target": "all", "message": "Test direct broadcast"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["channel"] == "SMS"
    assert data["total_recipients"] >= 0


def test_api_get_notification_logs():
    response = client.get("/api/notifications/logs?limit=10")
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    if logs:
        assert "worker_name" in logs[0]
        assert "notification_type" in logs[0]


def test_api_daily_broadcast_with_sms():
    response = client.get("/api/broadcast/daily?dispatch_sms=true")
    assert response.status_code == 200
    data = response.json()
    assert data["sms_dispatched"] is True
    assert data["sms_summary"] is not None
    assert "sent" in data["sms_summary"]
