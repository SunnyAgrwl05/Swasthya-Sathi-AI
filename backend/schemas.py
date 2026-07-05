from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class WorkerCreate(BaseModel):
    name: str
    role: str = "ASHA Worker"
    center: Optional[str] = None
    phone: Optional[str] = None


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



