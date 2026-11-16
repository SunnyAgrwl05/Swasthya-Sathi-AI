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


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    actions_taken: list[str] = []
    safety_warning: str | None = None
    is_flagged: bool = False
    confidence_score: float | None = None


class SafetyVerificationRequest(BaseModel):
    response_text: str
    query: str | None = ""


class SafetyVerificationResponse(BaseModel):
    confidence_score: float
    risk_level: str
    is_flagged: bool
    warning_message: str | None = None
    flagged_reasons: list[str] = []
    grounded_terms: list[str] = []



