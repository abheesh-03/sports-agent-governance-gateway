"""Pydantic schemas for requests and responses."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class AgentRequest(BaseModel):
    user_id: str
    user_role: str
    message: str = Field(..., description="Natural language request from the user.")


class ToolCallRequest(BaseModel):
    user_id: str
    user_role: str
    tool_name: str
    input_payload: Dict[str, Any] = Field(default_factory=dict)


class ToolCallResponse(BaseModel):
    request_id: str
    tool_name: str
    user_role: str
    decision: str
    status: str
    risk_level: Optional[str] = None
    approval_required: bool = False
    reason: Optional[str] = None
    result: Optional[Any] = None
    audit_log_id: Optional[int] = None
    approval_id: Optional[int] = None


class AgentResponse(BaseModel):
    request_id: str
    user_role: str
    message: str
    allowed_tools: List[str] = Field(default_factory=list)
    blocked_tools: List[str] = Field(default_factory=list)
    approval_required: bool = False
    tool_results: List[ToolCallResponse] = Field(default_factory=list)
    approval_requests: List[int] = Field(default_factory=list)
    audit_log_ids: List[int] = Field(default_factory=list)


class AuditLogResponse(BaseModel):
    id: int
    request_id: str
    user_id: str
    user_role: str
    tool_name: str
    input_payload: Optional[Any] = None
    decision: str
    risk_level: Optional[str] = None
    approval_required: Optional[str] = None
    status: str
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalRequestResponse(BaseModel):
    id: int
    request_id: str
    user_id: str
    user_role: str
    tool_name: str
    input_payload: Optional[Any] = None
    risk_level: Optional[str] = None
    status: str
    reviewer: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalDecisionRequest(BaseModel):
    reviewer: str
    notes: Optional[str] = None


class ToolMetadata(BaseModel):
    name: str
    description: str
    risk_level: str
    requires_approval: bool
    allowed_roles: List[str]
