from datetime import date

from pydantic import BaseModel


class WorkerCreate(BaseModel):
    worker_code: str
    name: str
    role: str = "ASHA Worker"
    center: str
    phone: str


class WorkerOut(WorkerCreate):
    id: int

    class Config:
        from_attributes = True


class WorkerUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    center: str | None = None
    phone: str | None = None


class AttendanceCreate(BaseModel):
    worker_id: int
    date: date
    status: str
    note: str | None = None


class AttendanceOut(BaseModel):
    id: int
    worker_id: int
    date: date
    status: str
    note: str | None = None
    marked_by: str

    class Config:
        from_attributes = True


class WorkerDetailOut(WorkerOut):
    total_attendance_records: int = 0
    recent_attendance: list[AttendanceOut] = []


class ChatRequest(BaseModel):
    message: str
    context: str | None = None


class HallucinationCheckOut(BaseModel):
    is_flagged: bool
    confidence_score: float
    risk_level: str
    flagged_reasons: list[str] = []
    warning_message: str | None = None
    breakdown: dict = {}


class ChatResponse(BaseModel):
    reply: str
    actions_taken: list[str] = []
    hallucination_check: HallucinationCheckOut | None = None


class HallucinationCheckRequest(BaseModel):
    query: str
    response: str
    context: str | None = None
    retrieval_score: float | None = None



