"""FastAPI application exposing the governed agent gateway."""
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud
from app.config import settings
from app.database import get_db, init_db
from app.schemas import (
    AgentRequest,
    AgentResponse,
    ApprovalDecisionRequest,
    ApprovalRequestResponse,
    AuditLogResponse,
    HealthResponse,
    ToolCallRequest,
    ToolCallResponse,
    ToolMetadata,
)
from gateway.approvals import approve_request, list_pending_approvals, reject_request
from gateway.router import execute_tool_call, route_agent_message
from gateway.tool_registry import list_tools

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Create database tables on startup.
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "A governed middleware gateway that decides which tools an AI agent may "
        "call against fake sports business systems, applying permissions, risk "
        "scoring, human approval, and audit logging."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "service": settings.SERVICE_NAME,
        "app_name": settings.APP_NAME,
        "org": settings.DEFAULT_ORG,
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.SERVICE_NAME)


@app.get("/tools", response_model=List[ToolMetadata], tags=["tools"])
def get_tools() -> List[ToolMetadata]:
    tools = list_tools()
    return [
        ToolMetadata(
            name=name,
            description=meta["description"],
            risk_level=meta["risk_level"],
            requires_approval=meta["requires_approval"],
            allowed_roles=meta["allowed_roles"],
        )
        for name, meta in tools.items()
    ]


@app.post("/agent/request", response_model=AgentResponse, tags=["agent"])
def agent_request(
    request: AgentRequest, db: Session = Depends(get_db)
) -> AgentResponse:
    return route_agent_message(db, request)


@app.post("/tools/call", response_model=ToolCallResponse, tags=["tools"])
def tool_call(
    request: ToolCallRequest, db: Session = Depends(get_db)
) -> ToolCallResponse:
    return execute_tool_call(db, request)


@app.get("/audit-logs", response_model=List[AuditLogResponse], tags=["audit"])
def audit_logs(
    user_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    decision: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[AuditLogResponse]:
    return crud.get_audit_logs(
        db, user_id=user_id, tool_name=tool_name, decision=decision, limit=limit
    )


@app.get(
    "/approvals/pending",
    response_model=List[ApprovalRequestResponse],
    tags=["approvals"],
)
def pending_approvals(db: Session = Depends(get_db)) -> List[ApprovalRequestResponse]:
    return list_pending_approvals(db)


@app.post(
    "/approvals/{approval_id}/approve",
    response_model=ApprovalRequestResponse,
    tags=["approvals"],
)
def approve(
    approval_id: int,
    decision: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
) -> ApprovalRequestResponse:
    approval = approve_request(
        db, approval_id, reviewer=decision.reviewer, notes=decision.notes
    )
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return approval


@app.post(
    "/approvals/{approval_id}/reject",
    response_model=ApprovalRequestResponse,
    tags=["approvals"],
)
def reject(
    approval_id: int,
    decision: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
) -> ApprovalRequestResponse:
    approval = reject_request(
        db, approval_id, reviewer=decision.reviewer, notes=decision.notes
    )
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return approval
