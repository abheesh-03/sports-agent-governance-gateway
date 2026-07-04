"""SQLAlchemy ORM models for audit logs and approval requests."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database import Base


class AuditLog(Base):
    """A record of every governed tool call decision."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)
    user_role = Column(String, nullable=False)
    tool_name = Column(String, index=True, nullable=False)
    # Stored as a JSON-encoded string for portability across databases.
    input_payload = Column(Text, nullable=True)
    decision = Column(String, index=True, nullable=False)
    risk_level = Column(String, nullable=True)
    approval_required = Column(String, nullable=True)
    status = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ApprovalRequest(Base):
    """A pending human-in-the-loop approval for a high-risk tool call."""

    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)
    user_role = Column(String, nullable=False)
    tool_name = Column(String, index=True, nullable=False)
    input_payload = Column(Text, nullable=True)
    risk_level = Column(String, nullable=True)
    # One of: pending, approved, rejected
    status = Column(String, default="pending", index=True, nullable=False)
    reviewer = Column(String, nullable=True)
    review_notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
