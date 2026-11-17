import csv
import datetime
import io
import time

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
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
from hallucination_detector import detect_hallucination

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


@app.get("/api/workers/{worker_id}", response_model=schemas.WorkerDetailOut)
def get_worker(worker_id: int, db: Session = Depends(get_db)):
    worker = db.query(models.HealthWorker).filter_by(id=worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    recent = (
        db.query(models.AttendanceRecord)
        .filter_by(worker_id=worker_id)
        .order_by(models.AttendanceRecord.date.desc())
        .limit(30)
        .all()
    )

    return schemas.WorkerDetailOut(
        id=worker.id,
        worker_code=worker.worker_code,
        name=worker.name,
        role=worker.role,
        center=worker.center,
        phone=worker.phone,
        total_attendance_records=len(worker.records),
        recent_attendance=recent,
    )


@app.put("/api/workers/{worker_id}", response_model=schemas.WorkerOut)
def update_worker(
    worker_id: int,
    worker_update: schemas.WorkerUpdate,
    db: Session = Depends(get_db),
):
    worker = db.query(models.HealthWorker).filter_by(id=worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    if worker_update.name is not None:
        worker.name = worker_update.name
    if worker_update.role is not None:
        worker.role = worker_update.role
    if worker_update.center is not None:
        worker.center = worker_update.center
    if worker_update.phone is not None:
        worker.phone = worker_update.phone

    db.commit()
    db.refresh(worker)
    return worker


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


@app.get("/api/attendance/export-csv")
@app.get("/api/reports/export-csv")
def export_attendance_csv(
    worker_id: int | None = None,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    status: str | None = None,
    center: str | None = None,
    db: Session = Depends(get_db),
):
    """Export attendance logs as RFC-4180 compliant CSV stream with optional filters."""
    q = db.query(models.AttendanceRecord).join(models.HealthWorker)

    if worker_id:
        q = q.filter(models.AttendanceRecord.worker_id == worker_id)
    if start_date:
        q = q.filter(models.AttendanceRecord.date >= start_date)
    if end_date:
        q = q.filter(models.AttendanceRecord.date <= end_date)
    if status:
        q = q.filter(models.AttendanceRecord.status == status)
    if center:
        q = q.filter(models.HealthWorker.center == center)

    records = q.order_by(models.AttendanceRecord.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        "Worker Code",
        "Worker Name",
        "Role",
        "Health Center",
        "Phone",
        "Date",
        "Status",
        "Note",
        "Marked By",
    ])

    for r in records:
        w = r.worker
        writer.writerow([
            w.worker_code if w else "",
            w.name if w else "",
            w.role if w else "",
            w.center if w else "",
            w.phone if w else "",
            r.date.isoformat(),
            r.status,
            r.note or "",
            r.marked_by or "",
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="swasthya_attendance_report.csv"',
            "Content-Type": "text/csv; charset=utf-8",
        },
    )


# =====================================================
# ANALYTICS
# =====================================================

@app.get("/api/analytics/summary")
def analytics_summary(
    days: int = 30,
    db: Session = Depends(get_db),
):

    since = datetime.date.today() - datetime.timedelta(days=days)

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

        result.append(
            {
                "worker_id": w.id,
                "name": w.name,
                "role": w.role,
                "center": w.center,
                "present": present,
                "total_logged": total,
                "attendance_pct": pct,
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

    return schemas.ChatResponse(
        reply=reply,
        actions_taken=actions,
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
# REPORTS
# =====================================================

@app.get("/api/broadcast/daily")
def daily_broadcast(db: Session = Depends(get_db)):
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
    return {
        "message": msg
    }


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

