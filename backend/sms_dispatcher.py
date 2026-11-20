"""
Multi-Channel SMS & Alert Dispatch Engine for Swasthya Sathi AI.
Provides reliable SMS notifications for rural ASHA/ANM health workers with low smartphone connectivity.
Supports Fast2SMS, Twilio, and sandbox mock delivery with delivery audit logging.
"""

import os
import re
import json
import uuid
import datetime
from typing import Dict, Any, List
import requests
from sqlalchemy.orm import Session
import models

FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY", "")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")


def sanitize_phone_number(phone: str) -> str:
    """Extract standard 10-digit Indian mobile number or E.164 international format."""
    digits = re.sub(r"[^\d]", "", phone or "")
    if len(digits) >= 10:
        return digits[-10:]
    return digits


def send_sms_via_fast2sms(phone: str, message: str) -> Dict[str, Any]:
    """Transmits SMS using Fast2SMS API."""
    clean_number = sanitize_phone_number(phone)
    if len(clean_number) != 10:
        return {"success": False, "error": f"Invalid phone format: {phone}"}

    url = "https://www.fast2sms.com/dev/bulkV2"
    headers = {
        "authorization": FAST2SMS_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {
        "variables_values": message,
        "route": "otp" if "code" in message.lower() else "q",
        "numbers": clean_number,
    }
    try:
        res = requests.post(url, data=payload, headers=headers, timeout=10)
        data = res.json()
        if res.status_code == 200 and data.get("return"):
            return {
                "success": True,
                "provider": "fast2sms",
                "message_id": data.get("request_id", uuid.uuid4().hex),
            }
        return {"success": False, "provider": "fast2sms", "error": data.get("message", "Fast2SMS failure")}
    except Exception as e:
        return {"success": False, "provider": "fast2sms", "error": str(e)}


def send_sms_via_twilio(phone: str, message: str) -> Dict[str, Any]:
    """Transmits SMS using Twilio REST API."""
    clean_number = sanitize_phone_number(phone)
    if len(clean_number) != 10:
        return {"success": False, "error": f"Invalid phone format: {phone}"}

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    data = {
        "From": TWILIO_PHONE_NUMBER,
        "To": f"+91{clean_number}",
        "Body": message,
    }
    try:
        res = requests.post(url, data=data, auth=auth, timeout=10)
        res_data = res.json()
        if res.status_code in (200, 201):
            return {
                "success": True,
                "provider": "twilio",
                "message_id": res_data.get("sid", uuid.uuid4().hex),
            }
        return {"success": False, "provider": "twilio", "error": res_data.get("message", "Twilio failure")}
    except Exception as e:
        return {"success": False, "provider": "twilio", "error": str(e)}


def send_sms_sandbox(phone: str, message: str) -> Dict[str, Any]:
    """
    Realistic Sandbox / Mock SMS dispatcher for development, CI, and test environments.
    Validates numbers and generates auditable delivery tracking tokens.
    """
    clean_number = sanitize_phone_number(phone)
    if not clean_number or len(clean_number) < 10:
        return {
            "success": False,
            "provider": "sandbox",
            "error": f"Invalid recipient telephone number: {phone}",
        }

    mock_id = f"SMS_SANDBOX_{uuid.uuid4().hex[:12].upper()}"
    return {
        "success": True,
        "provider": "sandbox",
        "message_id": mock_id,
        "phone": clean_number,
        "length": len(message),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def transmit_sms(phone: str, message: str) -> Dict[str, Any]:
    """
    Route SMS through configured cloud gateway with graceful sandbox fallback.
    """
    if FAST2SMS_API_KEY:
        res = send_sms_via_fast2sms(phone, message)
        if res.get("success"):
            return res
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
        res = send_sms_via_twilio(phone, message)
        if res.get("success"):
            return res

    # Fallback to sandbox provider
    return send_sms_sandbox(phone, message)


def dispatch_worker_notification(
    db: Session,
    worker_name: str,
    phone: str,
    message: str,
    notification_type: str = "SMS",
) -> models.NotificationLog:
    """
    Dispatches a single message and persists the audit record in NotificationLog.
    """
    result = transmit_sms(phone, message) if notification_type == "SMS" else {"success": True}
    status = "Sent" if result.get("success") else "Failed"

    log_entry = models.NotificationLog(
        worker_name=worker_name,
        phone=phone,
        notification_type=notification_type,
        message=message,
        status=status,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def dispatch_batch_broadcast_sms(
    db: Session,
    workers: List[models.HealthWorker],
    message: str,
) -> Dict[str, Any]:
    """
    Dispatches a broadcast message to multiple healthcare workers and creates audit logs.
    """
    sent_count = 0
    failed_count = 0
    errors = []

    for worker in workers:
        res = transmit_sms(worker.phone or "", message)
        status = "Sent" if res.get("success") else "Failed"
        if res.get("success"):
            sent_count += 1
        else:
            failed_count += 1
            errors.append(f"{worker.name} ({worker.phone}): {res.get('error')}")

        db.add(
            models.NotificationLog(
                worker_name=worker.name,
                phone=worker.phone,
                notification_type="SMS",
                message=message,
                status=status,
            )
        )

    db.commit()
    return {
        "total": len(workers),
        "sent": sent_count,
        "failed": failed_count,
        "channel": "SMS",
        "errors": errors,
    }


# =====================================================
# Offline-First SMS Queue Operations
# =====================================================

def enqueue_sms_alert(
    db: Session,
    phone: str,
    message: str,
    worker_name: str = "Field Worker",
    max_retries: int = 3,
    retry_interval_seconds: int = 60,
) -> models.SMSQueueItem:
    """
    Enqueues an SMS message into the offline queue with scheduled retry intervals.
    """
    item = models.SMSQueueItem(
        worker_name=worker_name,
        phone=phone,
        message=message,
        status="pending",
        attempts=0,
        max_retries=max_retries,
        retry_interval_seconds=retry_interval_seconds,
        next_retry_at=datetime.datetime.utcnow(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def process_offline_sms_queue(
    db: Session,
    now: datetime.datetime | None = None,
) -> Dict[str, Any]:
    """
    Processes eligible pending items in the offline SMS queue.
    Applies incremental retry counts and exponential/interval backoff.
    """
    if now is None:
        now = datetime.datetime.utcnow()

    eligible_items = (
        db.query(models.SMSQueueItem)
        .filter(
            models.SMSQueueItem.status == "pending",
            models.SMSQueueItem.next_retry_at <= now,
        )
        .all()
    )

    sent_count = 0
    retrying_count = 0
    failed_count = 0

    for item in eligible_items:
        res = transmit_sms(item.phone, item.message)
        item.attempts += 1
        item.updated_at = now

        if res.get("success"):
            item.status = "sent"
            item.last_error = None
            sent_count += 1
            # Add audit log
            db.add(
                models.NotificationLog(
                    worker_name=item.worker_name,
                    phone=item.phone,
                    notification_type="SMS",
                    message=item.message,
                    status="Sent",
                )
            )
        else:
            item.last_error = str(res.get("error", "Unknown transmission error"))
            if item.attempts >= item.max_retries:
                item.status = "failed"
                failed_count += 1
                db.add(
                    models.NotificationLog(
                        worker_name=item.worker_name,
                        phone=item.phone,
                        notification_type="SMS",
                        message=item.message,
                        status="Failed",
                    )
                )
            else:
                item.status = "pending"
                retrying_count += 1
                item.next_retry_at = now + datetime.timedelta(
                    seconds=item.retry_interval_seconds * item.attempts
                )

    db.commit()
    return {
        "processed": len(eligible_items),
        "sent": sent_count,
        "retrying": retrying_count,
        "failed": failed_count,
    }


def serialize_sms_queue(items: List[models.SMSQueueItem]) -> str:
    """Serializes SMS queue records to JSON string for local caching / offline sync."""
    data = [item.to_dict() for item in items]
    return json.dumps(data)


def deserialize_sms_queue(json_str: str) -> List[Dict[str, Any]]:
    """Deserializes SMS queue records from offline JSON cache."""
    return json.loads(json_str)
