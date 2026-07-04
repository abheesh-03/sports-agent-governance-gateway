"""Gateway router: the governed execution path for tool calls and agent messages.

Every tool call flows through:
    1. tool existence check
    2. role permission check
    3. risk classification
    4. approval routing (high-risk actions become approval requests)
    5. tool execution (only when allowed and no approval required)
    6. audit logging (always)
"""
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.schemas import AgentRequest, AgentResponse, ToolCallRequest, ToolCallResponse
from gateway.approvals import create_approval_request
from gateway.audit import write_audit_log
from gateway.permissions import is_tool_allowed
from gateway.risk import get_tool_risk
from tools.content import search_content
from tools.fans import lookup_fan_profile
from tools.policies import search_policy
from tools.responses import draft_fan_response
from tools.schedule import get_schedule
from tools.tickets import request_ticket_hold, search_ticket_options
from tools.visual_assets import classify_visual_asset


def _new_request_id() -> str:
    return f"req_{uuid.uuid4().hex[:10]}"


def _execute_tool(tool_name: str, payload: Dict[str, Any]) -> Any:
    """Dispatch to the concrete tool implementation with the given payload."""
    payload = payload or {}
    if tool_name == "get_schedule":
        return get_schedule(event_id=payload.get("event_id"))
    if tool_name == "search_policy":
        return search_policy(query=payload.get("query", ""))
    if tool_name == "search_content":
        return search_content(query=payload.get("query", ""))
    if tool_name == "lookup_fan_profile":
        return lookup_fan_profile(fan_id=payload.get("fan_id", ""))
    if tool_name == "search_ticket_options":
        return search_ticket_options(
            event_id=payload.get("event_id", ""),
            seat_count=int(payload.get("seat_count", 2)),
        )
    if tool_name == "draft_fan_response":
        return draft_fan_response(context=payload.get("context", payload))
    if tool_name == "classify_visual_asset":
        return classify_visual_asset(asset_id=payload.get("asset_id", ""))
    if tool_name == "request_ticket_hold":
        return request_ticket_hold(
            ticket_id=payload.get("ticket_id", ""),
            seat_count=int(payload.get("seat_count", 1)),
        )
    raise ValueError(f"No implementation registered for tool '{tool_name}'")


def execute_tool_call(
    db: Session, request: ToolCallRequest, request_id: Optional[str] = None
) -> ToolCallResponse:
    """Execute a single governed tool call and return a structured response."""
    request_id = request_id or _new_request_id()
    tool_name = request.tool_name
    payload = request.input_payload or {}

    # 1 & 2: permission check (also catches unknown tools).
    allowed, reason = is_tool_allowed(request.user_role, tool_name)

    # 3: risk classification.
    risk = get_tool_risk(tool_name)
    risk_level = risk["risk_level"]
    requires_approval = risk["requires_approval"]

    if not allowed:
        decision = (
            "blocked_unknown_tool"
            if reason == "unknown_tool"
            else "blocked_permission_denied"
        )
        log = write_audit_log(
            db,
            request_id=request_id,
            user_id=request.user_id,
            user_role=request.user_role,
            tool_name=tool_name,
            input_payload=payload,
            decision=decision,
            risk_level=risk_level if reason != "unknown_tool" else None,
            approval_required=requires_approval,
            status="blocked",
            reason=reason,
        )
        return ToolCallResponse(
            request_id=request_id,
            tool_name=tool_name,
            user_role=request.user_role,
            decision=decision,
            status="blocked",
            risk_level=log.risk_level,
            approval_required=requires_approval,
            reason=reason,
            result=None,
            audit_log_id=log.id,
        )

    # 6: high-risk actions are routed to human approval instead of executing.
    if requires_approval:
        approval = create_approval_request(
            db,
            request_id=request_id,
            user_id=request.user_id,
            user_role=request.user_role,
            tool_name=tool_name,
            input_payload=payload,
            risk_level=risk_level,
        )
        log = write_audit_log(
            db,
            request_id=request_id,
            user_id=request.user_id,
            user_role=request.user_role,
            tool_name=tool_name,
            input_payload=payload,
            decision="pending_approval",
            risk_level=risk_level,
            approval_required=True,
            status="pending_approval",
            reason="high_risk_requires_approval",
        )
        return ToolCallResponse(
            request_id=request_id,
            tool_name=tool_name,
            user_role=request.user_role,
            decision="pending_approval",
            status="pending_approval",
            risk_level=risk_level,
            approval_required=True,
            reason="high_risk_requires_approval",
            result={"approval_id": approval.id, "status": "pending_approval"},
            audit_log_id=log.id,
            approval_id=approval.id,
        )

    # 7: allowed and no approval required -> execute the tool.
    result = _execute_tool(tool_name, payload)
    log = write_audit_log(
        db,
        request_id=request_id,
        user_id=request.user_id,
        user_role=request.user_role,
        tool_name=tool_name,
        input_payload=payload,
        decision="allowed",
        risk_level=risk_level,
        approval_required=False,
        status="completed",
        reason="allowed",
    )
    return ToolCallResponse(
        request_id=request_id,
        tool_name=tool_name,
        user_role=request.user_role,
        decision="allowed",
        status="completed",
        risk_level=risk_level,
        approval_required=False,
        reason="allowed",
        result=result,
        audit_log_id=log.id,
    )


# --- Deterministic agent simulation (no LLM in version 1) -------------------

# Keyword -> tool routing rules. The first matching keyword for each tool adds
# that tool to the plan. Order of TOOL_KEYWORDS defines execution order.
TOOL_KEYWORDS = [
    ("search_ticket_options", ["ticket", "seat", "seats"]),
    ("search_policy", ["bag", "parking", "policy", "policies", "accessibility"]),
    ("get_schedule", ["schedule", "game", "event"]),
    ("lookup_fan_profile", ["fan profile", "member", "membership"]),
    ("search_content", ["content", "clip", "highlight", "sponsor"]),
]


def _default_payload_for(tool_name: str, message: str) -> Dict[str, Any]:
    """Build a best-effort payload for a keyword-routed tool call."""
    if tool_name == "search_policy":
        return {"query": message}
    if tool_name == "search_content":
        return {"query": message}
    if tool_name == "search_ticket_options":
        # Default to the first upcoming event; keyword routing has no event id.
        events = get_schedule()
        event_id = events[0]["event_id"] if events else ""
        return {"event_id": event_id, "seat_count": 2}
    if tool_name == "get_schedule":
        return {}
    if tool_name == "lookup_fan_profile":
        return {"fan_id": ""}
    return {}


def plan_tools(message: str) -> List[str]:
    """Return the ordered list of tools implied by a natural language message."""
    text = message.lower()
    planned: List[str] = []
    for tool_name, keywords in TOOL_KEYWORDS:
        if any(kw in text for kw in keywords):
            planned.append(tool_name)
    return planned


def route_agent_message(db: Session, agent_request: AgentRequest) -> AgentResponse:
    """Route a natural language agent message through governed tool calls."""
    request_id = _new_request_id()
    planned = plan_tools(agent_request.message)

    tool_results: List[ToolCallResponse] = []
    allowed_tools: List[str] = []
    blocked_tools: List[str] = []
    approval_requests: List[int] = []
    audit_log_ids: List[int] = []
    approval_required = False

    for tool_name in planned:
        payload = _default_payload_for(tool_name, agent_request.message)
        call = ToolCallRequest(
            user_id=agent_request.user_id,
            user_role=agent_request.user_role,
            tool_name=tool_name,
            input_payload=payload,
        )
        response = execute_tool_call(db, call, request_id=request_id)
        tool_results.append(response)

        if response.audit_log_id is not None:
            audit_log_ids.append(response.audit_log_id)

        if response.status == "blocked":
            blocked_tools.append(tool_name)
        elif response.status == "pending_approval":
            approval_required = True
            if response.approval_id is not None:
                approval_requests.append(response.approval_id)
        else:
            allowed_tools.append(tool_name)

    return AgentResponse(
        request_id=request_id,
        user_role=agent_request.user_role,
        message="Processed agent request through governed tool routing.",
        allowed_tools=allowed_tools,
        blocked_tools=blocked_tools,
        approval_required=approval_required,
        tool_results=tool_results,
        approval_requests=approval_requests,
        audit_log_ids=audit_log_ids,
    )
