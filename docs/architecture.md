# Architecture

The Sports Agent Governance Gateway is a controlled middleware layer between an
AI agent (or a user) and a set of simulated sports business systems. No system
is called directly — every request passes through the gateway.

```text
Agent / User Request
        |
        v
FastAPI API Layer
        |
        v
Gateway Router
        |
        ├── Tool Registry
        ├── Permission Check
        ├── Risk Scoring
        ├── Approval Routing
        └── Audit Logging
        |
        v
Approved Tool Execution
        |
        v
Structured Response
```

## Layers

### 1. FastAPI API Layer (`app/main.py`)

Exposes the HTTP endpoints (`/agent/request`, `/tools/call`, `/tools`,
`/audit-logs`, `/approvals/*`, `/health`). It handles request validation via
Pydantic schemas (`app/schemas.py`) and delegates all governance decisions to the
gateway. It owns no business rules itself.

### 2. Gateway Router (`gateway/router.py`)

The heart of the system. Two entry points:

- `execute_tool_call` — governs a **single** explicit tool call.
- `route_agent_message` — simulates an agent by turning a natural-language
  message into an ordered list of tool calls (deterministic keyword routing, no
  LLM), then runs each through `execute_tool_call`.

The governed path for every tool call is:

1. **Tool existence + permission check** (`gateway/permissions.py`)
2. **Risk classification** (`gateway/risk.py`)
3. If not allowed → write audit log, return a blocked response.
4. If approval required → create an approval request, write audit log, return a
   `pending_approval` response.
5. Otherwise → execute the tool, write audit log, return the result.

Audit logging happens on **every** branch — nothing is silent.

### 3. Tool Registry (`gateway/tool_registry.py`)

The single source of truth for which tools exist and their governance metadata:
`risk_level`, `requires_approval`, and `allowed_roles`. Permissions and risk both
read from here, so there is one place to change policy.

### 4. Permission Check (`gateway/permissions.py`)

`is_tool_allowed(user_role, tool_name)` returns `(allowed, reason)` where reason is
`allowed`, `unknown_tool`, or `role_not_allowed`. Unknown tools are rejected.

### 5. Risk Scoring (`gateway/risk.py`)

`get_tool_risk(tool_name)` returns the tool's `risk_level` and `requires_approval`.
Unregistered tools default to **high risk / approval required** — fail closed.

### 6. Approval Routing (`gateway/approvals.py`)

High-risk tools do not execute immediately. They create an `ApprovalRequest`
(status `pending`) that a `ticketing_manager` or `admin` can approve or reject via
the API. This is the human-in-the-loop control point.

### 7. Audit Logging (`gateway/audit.py`)

Every decision is written to the `audit_logs` table with the request id, user,
role, tool, input payload, decision, risk level, approval flag, status, and
reason. This is the auditability guarantee.

### 8. Tools (`tools/`)

Thin, deterministic functions that read fake JSON data from `data/`. They contain
**no** governance logic — they assume the gateway already authorized the call.
`request_ticket_hold` is intentionally simulation-only and never mutates data.

## Data flow example

`POST /agent/request` with "Find two tickets for the next game and tell me the bag
policy":

1. Router plans `[search_ticket_options, search_policy, get_schedule]`.
2. Each is permission-checked and risk-scored for the `fan_support_agent` role.
3. All three are allowed (low/medium, no approval), so each executes.
4. Three audit-log rows are written.
5. A combined `AgentResponse` is returned with results, allowed tools, and audit
   log ids.

## Persistence

SQLAlchemy models (`app/models.py`) back two tables — `audit_logs` and
`approval_requests` — on SQLite by default. The fake **business** data
(schedule, tickets, etc.) stays in flat JSON files, not the database.
