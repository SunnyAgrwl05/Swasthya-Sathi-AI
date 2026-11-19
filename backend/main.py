import datetime
import time

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
import schemas
from agent import (
    chat_with_agent,
    generate_daily_broadcast,
    generate_weekly_insights,
)
from database import engine, get_db
from hallucination_detector import get_detector
from hallucination_detector import detect_hallucination
from sms_dispatcher import (
    dispatch_batch_broadcast_sms,
    enqueue_sms_alert,
    process_offline_sms_queue,
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Swasthya Sathi AI",
    version="1.0.0",
)

class WeeklyInsightsRequest(BaseModel):
    language: str = "hi"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Swasthya Sathi AI Backend",
        "database": "Connected",
    }


# =====================================================
# HEALTH WORKERS
# =====================================================

@app.get("/api/workers", response_model=list[schemas.WorkerOut])
def get_workers(db: Session = Depends(get_db)):
    return db.query(models.HealthWorker).all()


@app.post("/api/workers", response_model=schemas.WorkerOut)
def create_worker(worker: schemas.WorkerCreate, db: Session = Depends(get_db)):
    existing = db.query(models.HealthWorker).filter_by(worker_code=worker.worker_code).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Worker with this worker_code already exists"
        )
    db_worker = models.HealthWorker(**worker.model_dump())
    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)
    return db_worker


@app.delete("/api/workers/{worker_id}")
def delete_worker(worker_id: int, db: Session = Depends(get_db)):
    worker = db.query(models.HealthWorker).filter_by(id=worker_id).first()

    if not worker:
        raise HTTPException(404, "Worker not found")

    db.delete(worker)
    db.commit()

    return {"deleted": worker_id}


# =====================================================
# ATTENDANCE
# =====================================================

@app.get("/api/attendance", response_model=list[schemas.AttendanceOut])
def get_attendance(
    worker_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.AttendanceRecord)

    if worker_id:
        q = q.filter_by(worker_id=worker_id)

    return (
        q.order_by(models.AttendanceRecord.date.desc())
        .limit(500)
        .all()
    )


@app.post("/api/attendance", response_model=schemas.AttendanceOut)
def create_attendance(
    record: schemas.AttendanceCreate,
    db: Session = Depends(get_db),
):
    worker = db.query(models.HealthWorker).filter_by(id=record.worker_id).first()
    if not worker:
        raise HTTPException(
            status_code=404,
            detail="Worker not found"
        )

    existing = (
        db.query(models.AttendanceRecord)
        .filter_by(
            worker_id=record.worker_id,
            date=record.date,
        )
        .first()
    )

    if existing:
        existing.status = record.status
        existing.note = record.note
        existing.marked_by = "manual"

        db.add(models.AuditLog(
            action="Update Attendance",
            entity="AttendanceRecord",
            performed_by="manual",
            description=f"Updated attendance for worker_id {record.worker_id} on {record.date} to {record.status}",
        ))

        db.commit()
        db.refresh(existing)

        return existing

    db_record = models.AttendanceRecord(
        **record.model_dump(),
        marked_by="manual",
    )

    db.add(db_record)
    db.flush()
    db.add(models.AuditLog(
        action="Create Attendance",
        entity="AttendanceRecord",
        performed_by="manual",
        description=f"Created attendance for worker_id {record.worker_id} on {record.date} as {record.status}",
    ))
    db.commit()
    db.refresh(db_record)

    return db_record


# =====================================================
# LEAVE & ATTENDANCE HISTORY (HEATMAP)
# =====================================================

@app.post("/api/leaves", response_model=schemas.LeaveOut)
def create_leave(
    leave: schemas.LeaveCreate,
    db: Session = Depends(get_db),
):
    """
    Applies an approved leave date range for a health worker, auto-populating daily attendance records.
    """
    worker = db.query(models.HealthWorker).filter_by(id=leave.worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    if leave.start_date > leave.end_date:
        raise HTTPException(status_code=400, detail="start_date must be on or before end_date")

    if (leave.end_date - leave.start_date).days > 365:
        raise HTTPException(status_code=400, detail="Leave duration cannot exceed 365 days")

    db_leave = models.LeaveRecord(
        worker_id=leave.worker_id,
        start_date=leave.start_date,
        end_date=leave.end_date,
        leave_type=leave.leave_type.lower(),
        reason=leave.reason,
        status="Approved",
        approved_by=leave.approved_by,
    )
    db.add(db_leave)

    delta = (leave.end_date - leave.start_date).days
    note_text = f"Leave ({leave.leave_type.capitalize()}): {leave.reason or 'Approved'}"
    for i in range(delta + 1):
        day = leave.start_date + datetime.timedelta(days=i)
        existing_att = (
            db.query(models.AttendanceRecord)
            .filter_by(worker_id=leave.worker_id, date=day)
            .first()
        )
        if existing_att:
            existing_att.status = "leave"
            existing_att.note = note_text
            existing_att.marked_by = leave.approved_by
        else:
            new_att = models.AttendanceRecord(
                worker_id=leave.worker_id,
                date=day,
                status="leave",
                note=note_text,
                marked_by=leave.approved_by,
            )
            db.add(new_att)

    db.commit()
    db.refresh(db_leave)
    return db_leave


@app.get("/api/leaves", response_model=list[schemas.LeaveOut])
def get_leaves(
    worker_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Retrieves leave records with optional worker filter."""
    q = db.query(models.LeaveRecord)
    if worker_id:
        q = q.filter_by(worker_id=worker_id)
    return q.order_by(models.LeaveRecord.start_date.desc()).all()


@app.patch("/api/leaves/{leave_id}/status", response_model=schemas.LeaveOut)
def update_leave_status(
    leave_id: int,
    req: schemas.LeaveStatusUpdate,
    db: Session = Depends(get_db),
):
    """
    Approves or rejects a leave request, updating worker attendance records accordingly.
    """
    db_leave = db.query(models.LeaveRecord).filter_by(id=leave_id).first()
    if not db_leave:
        raise HTTPException(status_code=404, detail="Leave record not found")

    new_status = req.status.capitalize()
    if new_status not in {"Approved", "Rejected", "Pending"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid status. Must be Approved, Rejected, or Pending.",
        )

    prev_status = db_leave.status
    db_leave.status = new_status
    db_leave.approved_by = req.approved_by

    delta = (db_leave.end_date - db_leave.start_date).days
    if new_status == "Approved":
        note_text = f"Leave ({db_leave.leave_type.capitalize()}): Approved"
        for i in range(delta + 1):
            day = db_leave.start_date + datetime.timedelta(days=i)
            existing_att = (
                db.query(models.AttendanceRecord)
                .filter_by(worker_id=db_leave.worker_id, date=day)
                .first()
            )
            if existing_att:
                existing_att.status = "leave"
                existing_att.note = note_text
                existing_att.marked_by = req.approved_by
            else:
                db.add(
                    models.AttendanceRecord(
                        worker_id=db_leave.worker_id,
                        date=day,
                        status="leave",
                        note=note_text,
                        marked_by=req.approved_by,
                    )
                )
    elif new_status in {"Rejected", "Pending"} and prev_status == "Approved":
        for i in range(delta + 1):
            day = db_leave.start_date + datetime.timedelta(days=i)
            existing_att = (
                db.query(models.AttendanceRecord)
                .filter_by(worker_id=db_leave.worker_id, date=day)
                .first()
            )
            if existing_att and existing_att.status == "leave":
                db.delete(existing_att)

    db.commit()
    db.refresh(db_leave)
    return db_leave


@app.get("/api/workers/{worker_id}/attendance-history", response_model=schemas.WorkerAttendanceHistoryOut)
def get_worker_attendance_history(
    worker_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """
    Returns an indexed daily attendance history for 30-day heatmap visualization.
    """
    worker = db.query(models.HealthWorker).filter_by(id=worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    today = datetime.date.today()
    start_window = today - datetime.timedelta(days=days - 1)

    records = (
        db.query(models.AttendanceRecord)
        .filter(
            models.AttendanceRecord.worker_id == worker_id,
            models.AttendanceRecord.date >= start_window,
            models.AttendanceRecord.date <= today,
        )
        .all()
    )
    records_by_date = {r.date: r for r in records}

    leaves = (
        db.query(models.LeaveRecord)
        .filter(
            models.LeaveRecord.worker_id == worker_id,
            models.LeaveRecord.status == "Approved",
            models.LeaveRecord.end_date >= start_window,
            models.LeaveRecord.start_date <= today,
        )
        .all()
    )

    day_items = []
    present_cnt = 0
    absent_cnt = 0
    leave_cnt = 0

    for i in range(days):
        current_date = start_window + datetime.timedelta(days=i)
        rec = records_by_date.get(current_date)

        leave_match = next(
            (lv for lv in leaves if lv.start_date <= current_date <= lv.end_date), None
        )

        if rec:
            status = rec.status
            note = rec.note
            marked_by = rec.marked_by
            l_type = leave_match.leave_type if leave_match else None
        elif leave_match:
            status = "leave"
            note = f"Leave ({leave_match.leave_type.capitalize()}): {leave_match.reason or 'Approved'}"
            marked_by = leave_match.approved_by
            l_type = leave_match.leave_type
        else:
            status = "unmarked"
            note = None
            marked_by = None
            l_type = None

        if status == "present":
            present_cnt += 1
        elif status == "absent":
            absent_cnt += 1
        elif status == "leave":
            leave_cnt += 1

        day_items.append(
            schemas.AttendanceHistoryDay(
                date=current_date,
                status=status,
                note=note,
                marked_by=marked_by,
                leave_type=l_type,
            )
        )

    attendance_pct = round((present_cnt / days) * 100, 1) if days > 0 else 0.0

    return schemas.WorkerAttendanceHistoryOut(
        worker_id=worker.id,
        name=worker.name,
        role=worker.role,
        center=worker.center,
        days=day_items,
        total_days=days,
        present_days=present_cnt,
        absent_days=absent_cnt,
        leave_days=leave_cnt,
        attendance_pct=attendance_pct,
    )


# =====================================================
# ANALYTICS
# =====================================================

@app.get("/api/analytics/summary")
def analytics_summary(
    days: int = 30,
    db: Session = Depends(get_db),
):

    today = datetime.date.today()
    since = today - datetime.timedelta(days=days)
    this_week_start = today - datetime.timedelta(days=7)
    last_week_start = today - datetime.timedelta(days=14)

    workers = db.query(models.HealthWorker).all()

    result = []

    for w in workers:

        records = [r for r in w.records if r.date >= since]

        present = sum(
            1
            for r in records
            if r.status == "present"
        )

        total = len(records)

        pct = round((present / total) * 100, 1) if total else 0

        # Week-over-Week trend calculations
        this_week = [r for r in w.records if this_week_start <= r.date <= today]
        last_week = [r for r in w.records if last_week_start <= r.date < this_week_start]

        this_week_pct = (
            round((sum(1 for r in this_week if r.status == "present") / len(this_week)) * 100, 1)
            if this_week
            else None
        )
        last_week_pct = (
            round((sum(1 for r in last_week if r.status == "present") / len(last_week)) * 100, 1)
            if last_week
            else None
        )

        trend_delta = (
            round(this_week_pct - last_week_pct, 1)
            if (this_week_pct is not None and last_week_pct is not None)
            else None
        )

        result.append(
            {
                "worker_id": w.id,
                "name": w.name,
                "role": w.role,
                "center": w.center,
                "present": present,
                "total_logged": total,
                "attendance_pct": pct,
                "this_week_pct": this_week_pct,
                "last_week_pct": last_week_pct,
                "trend_delta": trend_delta,
            }
        )

    result.sort(key=lambda x: x["attendance_pct"])

    return result


# =====================================================
# AI CHAT
# =====================================================

@app.post("/api/chat", response_model=schemas.ChatResponse)
def chat(
    req: schemas.ChatRequest,
    db: Session = Depends(get_db),
):

    db.add(
        models.ChatLog(
            role="user",
            message=req.message,
        )
    )

    db.commit()

    start_time = time.time()
    reply, actions = chat_with_agent(req.message)
    end_time = time.time()
    exec_time = int((end_time - start_time) * 1000)

    # Perform automated hallucination and clinical safety assessment
    check_result = detect_hallucination(
        query=req.message,
        response=reply,
        context=req.context,
    )

    db.add(
        models.ChatLog(
            role="agent",
            message=reply,
        )
    )

    db.add(
        models.AgentLog(
            query=req.message,
            response=reply,
            tools_used=", ".join(actions) if actions else None,
            execution_time_ms=exec_time,
            status="Flagged" if check_result.is_flagged else "Success",
        )
    )

    db.commit()

    # Run hallucination / medical-safety check on every AI reply
    detector = get_detector()
    safety_report = detector.assess_response(reply, req.message)

    return schemas.ChatResponse(
        reply=reply,
        actions_taken=actions,
        safety_warning=safety_report.warning_message,
        is_flagged=safety_report.is_flagged,
        confidence_score=safety_report.confidence_score,
        hallucination_check=schemas.HallucinationCheckOut(**check_result.to_dict()),
    )


@app.post("/api/safety/check-hallucination", response_model=schemas.HallucinationCheckOut)
def check_hallucination_endpoint(req: schemas.HallucinationCheckRequest):
    """
    Standalone endpoint to verify medical text and calculate confidence / hallucination risk.
    """
    result = detect_hallucination(
        query=req.query,
        response=req.response,
        context=req.context,
        retrieval_score=req.retrieval_score,
    )
    return schemas.HallucinationCheckOut(**result.to_dict())


# =====================================================
# SAFETY VERIFICATION
# =====================================================

@app.post("/api/safety/verify", response_model=schemas.SafetyVerificationResponse)
def verify_response_safety(req: schemas.SafetyVerificationRequest):
    """
    Standalone endpoint to run the hallucination/medical-safety check on any
    AI-generated text.  Useful for frontend or integration testing.
    """
    from hallucination_detector import verify_medical_response  # local import keeps startup clean

    result = verify_medical_response(req.response_text, req.query or "")
    return schemas.SafetyVerificationResponse(**result)


# =====================================================
# REPORTS
# =====================================================

@app.get("/api/broadcast/daily")
def daily_broadcast(dispatch_sms: bool = False, db: Session = Depends(get_db)):
    msg = generate_daily_broadcast()
    workers = db.query(models.HealthWorker).all()
    for w in workers:
        db.add(
            models.NotificationLog(
                worker_name=w.name,
                phone=w.phone,
                notification_type="WhatsApp",
                message=msg,
                status="Sent"
            )
        )
    db.commit()

    sms_summary = None
    if dispatch_sms:
        sms_summary = dispatch_batch_broadcast_sms(db, workers, msg)

    return {
        "message": msg,
        "sms_dispatched": dispatch_sms,
        "sms_summary": sms_summary,
    }


@app.post("/api/notifications/dispatch-sms", response_model=schemas.SMSDispatchSummaryOut)
def dispatch_sms_endpoint(
    req: schemas.SMSDispatchRequest,
    db: Session = Depends(get_db),
):
    """
    Dispatches automated SMS alerts to offline field workers with delivery audit logging.
    """
    text = req.message or generate_daily_broadcast()

    if req.target == "worker" and req.worker_id:
        worker = db.query(models.HealthWorker).filter_by(id=req.worker_id).first()
        if not worker:
            raise HTTPException(status_code=404, detail="Worker not found")
        workers = [worker]
    elif req.target == "pending":
        today = datetime.date.today()
        marked_ids = {
            r.worker_id
            for r in db.query(models.AttendanceRecord.worker_id).filter_by(date=today).all()
        }
        workers = db.query(models.HealthWorker).filter(models.HealthWorker.id.notin_(marked_ids)).all()
    else:
        workers = db.query(models.HealthWorker).all()

    summary = dispatch_batch_broadcast_sms(db, workers, text)
    return schemas.SMSDispatchSummaryOut(
        status="completed",
        total_recipients=summary["total"],
        sent=summary["sent"],
        failed=summary["failed"],
        channel="SMS",
        errors=summary.get("errors", []),
    )


@app.get("/api/notifications/logs", response_model=list[schemas.NotificationLogOut])
def get_notification_logs(
    notification_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    Retrieves recent dispatched notification audit records across SMS, WhatsApp, etc.
    """
    q = db.query(models.NotificationLog)
    if notification_type:
        q = q.filter(models.NotificationLog.notification_type == notification_type)
    if status:
        q = q.filter(models.NotificationLog.status == status)

    return q.order_by(models.NotificationLog.id.desc()).limit(limit).all()


@app.get("/api/notifications/queue", response_model=list[schemas.SMSQueueItemOut])
def get_sms_queue(
    status: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Retrieves items from the offline SMS dispatch queue."""
    q = db.query(models.SMSQueueItem)
    if status:
        q = q.filter_by(status=status)
    return q.order_by(models.SMSQueueItem.id.desc()).limit(limit).all()


@app.post("/api/notifications/queue/process", response_model=schemas.SMSQueueProcessSummary)
def process_sms_queue_endpoint(
    db: Session = Depends(get_db),
):
    """Processes eligible pending SMS alerts in the offline dispatch queue."""
    summary = process_offline_sms_queue(db)
    return schemas.SMSQueueProcessSummary(**summary)


@app.post("/api/notifications/queue/enqueue", response_model=schemas.SMSQueueItemOut)
def enqueue_sms_endpoint(
    worker_name: str,
    phone: str,
    message: str,
    max_retries: int = 3,
    retry_interval_seconds: int = 60,
    db: Session = Depends(get_db),
):
    """Enqueues an SMS message into the offline queue."""
    item = enqueue_sms_alert(
        db=db,
        phone=phone,
        message=message,
        worker_name=worker_name,
        max_retries=max_retries,
        retry_interval_seconds=retry_interval_seconds,
    )
    return item


@app.get("/api/insights/weekly")
def weekly_insights(language: str = "hi"):
    return {
        "report": generate_weekly_insights(language=language)
    }

@app.post("/api/insights/weekly")
def weekly_insights_post(request: WeeklyInsightsRequest):
    return {
        "report": generate_weekly_insights(
            language=request.language
        )
    }


# =====================================================
# PUBLIC HEALTH KNOWLEDGE BASE (RAG)
# =====================================================

@app.get("/api/knowledge/search")
def search_knowledge(q: str = ""):
    from knowledge.rag_service import get_health_knowledge_base

    if not q.strip():
        return {"query": q, "results": []}

    kb = get_health_knowledge_base()
    results = kb.search(q, top_k=3)
    return {"query": q, "results": results}

