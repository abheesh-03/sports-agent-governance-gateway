"""Approval layer: create and resolve human-in-the-loop approval requests."""
import json
from typing import Any, List, Optional

from sqlalchemy.orm import Session

from app import models


def create_approval_request(
    db: Session,
    request_id: str,
    user_id: str,
    user_role: str,
    tool_name: str,
    input_payload: Any,
    risk_level: Optional[str],
) -> models.ApprovalRequest:
    """Create a new pending approval request and persist it."""
    approval = models.ApprovalRequest(
        request_id=request_id,
        user_id=user_id,
        user_role=user_role,
        tool_name=tool_name,
        input_payload=json.dumps(input_payload) if input_payload is not None else None,
        risk_level=risk_level,
        status="pending",
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    return approval


def _resolve(
    db: Session,
    approval_id: int,
    status: str,
    reviewer: str,
    notes: Optional[str],
) -> Optional[models.ApprovalRequest]:
    approval = (
        db.query(models.ApprovalRequest)
        .filter(models.ApprovalRequest.id == approval_id)
        .first()
    )
    if approval is None:
        return None
    approval.status = status
    approval.reviewer = reviewer
    approval.review_notes = notes
    db.commit()
    db.refresh(approval)
    return approval


def approve_request(
    db: Session, approval_id: int, reviewer: str, notes: Optional[str] = None
) -> Optional[models.ApprovalRequest]:
    """Mark an approval request as approved."""
    return _resolve(db, approval_id, "approved", reviewer, notes)


def reject_request(
    db: Session, approval_id: int, reviewer: str, notes: Optional[str] = None
) -> Optional[models.ApprovalRequest]:
    """Mark an approval request as rejected."""
    return _resolve(db, approval_id, "rejected", reviewer, notes)


def list_pending_approvals(db: Session) -> List[models.ApprovalRequest]:
    """Return all pending approval requests, newest first."""
    return (
        db.query(models.ApprovalRequest)
        .filter(models.ApprovalRequest.status == "pending")
        .order_by(models.ApprovalRequest.id.desc())
        .all()
    )
