from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


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
    hallucination_check: HallucinationCheckOut | None = None


class HallucinationCheckRequest(BaseModel):
    query: str
    response: str
    context: str | None = None
    retrieval_score: float | None = None


class LeaveCreate(BaseModel):
    worker_id: int
    start_date: date
    end_date: date
    leave_type: str = "casual"
    reason: str | None = None
    approved_by: str = "Supervisor"


class LeaveOut(BaseModel):
    id: int
    worker_id: int
    start_date: date
    end_date: date
    leave_type: str
    reason: str | None = None
    status: str
    approved_by: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class NotificationLogOut(BaseModel):
    id: int
    worker_name: str
    phone: str | None = None
    notification_type: str
    message: str
    status: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class AttendanceHistoryDay(BaseModel):
    date: date
    status: str
    note: str | None = None
    marked_by: str | None = None
    leave_type: str | None = None


class WorkerAttendanceHistoryOut(BaseModel):
    worker_id: int
    name: str
    role: str
    center: str
    days: list[AttendanceHistoryDay]
    total_days: int
    present_days: int
    absent_days: int
    leave_days: int
    attendance_pct: float


class SMSDispatchRequest(BaseModel):
    message: str | None = None
    worker_id: int | None = None
    target: str = "all"  # "all", "pending", "worker"


class SMSDispatchSummaryOut(BaseModel):
    status: str
    total_recipients: int
    sent: int
    failed: int
    channel: str = "SMS"
    errors: list[str] = []


class LeaveStatusUpdate(BaseModel):
    status: str  # "Approved", "Rejected", "Pending"
    approved_by: str = "Supervisor"


class SMSQueueItemOut(BaseModel):
    id: int
    worker_name: str
    phone: str
    message: str
    status: str
    attempts: int
    max_retries: int
    retry_interval_seconds: int
    next_retry_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class SMSQueueProcessSummary(BaseModel):
    processed: int
    sent: int
    retrying: int
    failed: int



