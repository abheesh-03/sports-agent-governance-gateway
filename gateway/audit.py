"""Audit logging layer: persist a record of every governed tool call."""
import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app import models


def write_audit_log(
    db: Session,
    request_id: str,
    user_id: str,
    user_role: str,
    tool_name: str,
    input_payload: Any,
    decision: str,
    risk_level: Optional[str],
    approval_required: bool,
    status: str,
    reason: Optional[str] = None,
) -> models.AuditLog:
    """Write and persist an audit log entry, returning the saved row."""
    log = models.AuditLog(
        request_id=request_id,
        user_id=user_id,
        user_role=user_role,
        tool_name=tool_name,
        input_payload=json.dumps(input_payload) if input_payload is not None else None,
        decision=decision,
        risk_level=risk_level,
        approval_required=str(bool(approval_required)).lower(),
        status=status,
        reason=reason,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
