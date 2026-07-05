import datetime

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
import schemas
from database import engine, get_db
from agent import (
    chat_with_agent,
    generate_daily_broadcast,
    generate_weekly_insights,
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Swasthya Sathi AI",
    version="1.0.0",
)

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

        db.commit()
        db.refresh(existing)

        return existing

    db_record = models.AttendanceRecord(
        **record.model_dump(),
        marked_by="manual",
    )

    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    return db_record


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

    reply, actions = chat_with_agent(req.message)

    db.add(
        models.ChatLog(
            role="agent",
            message=reply,
        )
    )

    db.commit()

    return schemas.ChatResponse(
        reply=reply,
        actions_taken=actions,
    )


# =====================================================
# REPORTS
# =====================================================

@app.get("/api/broadcast/daily")
def daily_broadcast():
    return {
        "message": generate_daily_broadcast()
    }


@app.get("/api/insights/weekly")
def weekly_insights():
    return {
        "report": generate_weekly_insights()
    }