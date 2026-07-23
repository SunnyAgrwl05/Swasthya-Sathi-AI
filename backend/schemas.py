from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


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
    note: Optional[str] = None


class AttendanceOut(BaseModel):
    id: int
    worker_id: int
    date: date
    status: str
    note: Optional[str] = None
    marked_by: str

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    actions_taken: list[str] = []



