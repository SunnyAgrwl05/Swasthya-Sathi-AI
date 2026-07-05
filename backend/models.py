import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    Text,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


# =====================================================
# Health Worker
# =====================================================

class HealthWorker(Base):
    __tablename__ = "health_workers"

    id = Column(Integer, primary_key=True, index=True)

    worker_code = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    name = Column(
        String,
        nullable=False,
    )

    role = Column(
        String,
        default="ASHA Worker",
    )

    center = Column(
        String,
        nullable=False,
    )

    phone = Column(
        String,
        nullable=False,
    )

    joined_on = Column(
        Date,
        default=datetime.date.today,
    )

    records = relationship(
        "AttendanceRecord",
        back_populates="worker",
        cascade="all, delete-orphan",
    )


# =====================================================
# Attendance Record
# =====================================================

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)

    worker_id = Column(
        Integer,
        ForeignKey("health_workers.id"),
        nullable=False,
    )

    date = Column(
        Date,
        nullable=False,
    )

    status = Column(
        String,
        nullable=False,
    )  # present / absent / half-day / leave

    note = Column(
        Text,
        nullable=True,
    )

    marked_by = Column(
        String,
        default="AI Agent",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    worker = relationship(
        "HealthWorker",
        back_populates="records",
    )


# =====================================================
# Chat Logs
# =====================================================

class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)

    role = Column(
        String,
        nullable=False,
    )  # user / agent

    message = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# =====================================================
# Health Centers
# =====================================================

class HealthCenter(Base):
    __tablename__ = "health_centers"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String,
        unique=True,
        nullable=False,
    )

    district = Column(
        String,
        nullable=False,
    )

    block = Column(
        String,
        nullable=False,
    )

    center_type = Column(
        String,
        default="PHC",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# =====================================================
# Notification Logs
# =====================================================

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)

    worker_name = Column(
        String,
        nullable=False,
    )

    phone = Column(
        String,
        nullable=True,
    )

    notification_type = Column(
        String,
        default="WhatsApp",
    )  # SMS / WhatsApp / Email

    message = Column(
        Text,
        nullable=False,
    )

    status = Column(
        String,
        default="Sent",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# =====================================================
# Audit Logs
# =====================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    action = Column(
        String,
        nullable=False,
    )

    entity = Column(
        String,
        nullable=False,
    )

    performed_by = Column(
        String,
        default="AI Agent",
    )

    description = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# =====================================================
# Agent Logs
# =====================================================

class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)

    query = Column(
        Text,
        nullable=False,
    )

    response = Column(
        Text,
        nullable=False,
    )

    tools_used = Column(
        String,
        nullable=True,
    )

    execution_time_ms = Column(
        Integer,
        nullable=True,
    )

    status = Column(
        String,
        default="Success",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )