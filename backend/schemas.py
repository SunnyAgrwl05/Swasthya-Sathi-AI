from datetime import date, datetime

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


class LeaveCreate(BaseModel):
    worker_id: int
    start_date: date
    end_date: date
    leave_type: str = "casual"
    reason: str | None = None
    approved_by: str = "supervisor"


class LeaveOut(BaseModel):
    id: int
    worker_id: int
    start_date: date
    end_date: date
    leave_type: str
    reason: str | None = None
    approved_by: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


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



