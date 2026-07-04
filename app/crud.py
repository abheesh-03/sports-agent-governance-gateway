"""Database access helpers for audit logs and approval requests.

These functions wrap common queries so router and gateway layers do not embed
SQLAlchemy query logic directly.
"""
import json
from typing import Any, List, Optional

from sqlalchemy.orm import Session

from app import models


def _decode_payload(raw: Optional[str]) -> Any:
    """Decode a JSON-encoded payload string back into Python objects."""
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return raw


def get_audit_logs(
    db: Session,
    user_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    decision: Optional[str] = None,
    limit: int = 50,
) -> List[models.AuditLog]:
    """Return recent audit logs, newest first, with optional filters."""
    query = db.query(models.AuditLog)
    if user_id:
        query = query.filter(models.AuditLog.user_id == user_id)
    if tool_name:
        query = query.filter(models.AuditLog.tool_name == tool_name)
    if decision:
        query = query.filter(models.AuditLog.decision == decision)
    query = query.order_by(models.AuditLog.id.desc())
    logs = query.limit(limit).all()
    # Decode stored JSON payloads into native objects for response models.
    for log in logs:
        log.input_payload = _decode_payload(log.input_payload)
    return logs


def get_approval(db: Session, approval_id: int) -> Optional[models.ApprovalRequest]:
    approval = (
        db.query(models.ApprovalRequest)
        .filter(models.ApprovalRequest.id == approval_id)
        .first()
    )
    if approval is not None:
        approval.input_payload = _decode_payload(approval.input_payload)
    return approval


def get_pending_approvals(db: Session) -> List[models.ApprovalRequest]:
    approvals = (
        db.query(models.ApprovalRequest)
        .filter(models.ApprovalRequest.status == "pending")
        .order_by(models.ApprovalRequest.id.desc())
        .all()
    )
    for approval in approvals:
        approval.input_payload = _decode_payload(approval.input_payload)
    return approvals
