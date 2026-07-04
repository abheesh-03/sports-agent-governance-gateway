# Sports Agent Governance Gateway

A portfolio-level project that simulates how a sports organization could safely
let AI agents interact with business systems such as ticketing, schedules,
content libraries, fan profiles, and venue policies.

> **Core idea:** AI agents should not have unrestricted access to business
> systems. They need permissions, tool boundaries, audit logs, risk scoring, and
> human approval for sensitive actions.

The project is built around a **fictional** sports organization called
**Northstar Athletics**. It does **not** use real client data, real sports team
data, or real ticketing APIs. All data is fake and generated inside this repo.

---

## What it does

Instead of letting an agent call any system directly, this gateway decides:

- what tools the agent can call
- whether the user's role has permission
- whether the action is low, medium, or high risk
- whether human approval is required
- what gets logged for audit purposes
- what safe, structured response is returned

Every tool call flows through **permissions → risk scoring → approval routing →
audit logging** before anything executes.

---

## Architecture

```text
Agent / User Request
        |
        v
FastAPI API Layer
        |
        v
Gateway Router
        |
        ├── Tool Registry      (which tools exist + metadata)
        ├── Permission Check    (can this role call this tool?)
        ├── Risk Scoring        (low / medium / high)
        ├── Approval Routing    (high-risk -> human approval queue)
        └── Audit Logging       (every decision is recorded)
        |
        v
Approved Tool Execution
        |
        v
Structured Response
```

See [`docs/architecture.md`](docs/architecture.md) for a layer-by-layer
explanation and [`docs/governance_model.md`](docs/governance_model.md) for the
governance rules.

---

## Roles

| Role                | Allowed behavior                                      |
| ------------------- | ----------------------------------------------------- |
| `guest`             | Search public schedule and policies                   |
| `fan_support_agent` | Search policies, tickets, schedule, draft responses   |
| `content_editor`    | Search content records                                |
| `ticketing_manager` | Search tickets/schedule and request ticket holds      |
| `admin`             | Access all tools, approvals, and audit logs           |

## Tools & risk levels

| Tool                    | Risk   | Approval required |
| ----------------------- | ------ | ----------------- |
| `get_schedule`          | low    | no                |
| `search_policy`         | low    | no                |
| `search_content`        | low    | no                |
| `lookup_fan_profile`    | medium | no (logged)       |
| `search_ticket_options` | medium | no                |
| `draft_fan_response`    | medium | no                |
| `request_ticket_hold`   | high   | **yes**           |

---

## Tech stack

Python 3.10+, FastAPI, Uvicorn, Pydantic, SQLAlchemy, SQLite (default), Pytest,
Docker + Docker Compose. **No paid LLM APIs are required** — version 1 uses
deterministic keyword routing and rule-based agent simulation.

---

## Quickstart

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# (optional) create tables and print a fake-data summary
python -m scripts.seed_data

# run the API
uvicorn app.main:app --reload
```

Then open the interactive docs:

```text
http://localhost:8000/docs
```

Run the tests:

```bash
pytest
```

Run with Docker:

```bash
docker compose up --build
```

---

## API endpoints

| Method | Path                              | Description                          |
| ------ | --------------------------------- | ------------------------------------ |
| GET    | `/`                               | Service metadata                     |
| GET    | `/health`                         | Health check                         |
| GET    | `/tools`                          | List registered tools + metadata     |
| POST   | `/agent/request`                  | Natural-language agent request       |
| POST   | `/tools/call`                     | Single governed tool call            |
| GET    | `/audit-logs`                     | Recent audit logs (filterable)       |
| GET    | `/approvals/pending`              | Pending approval requests            |
| POST   | `/approvals/{approval_id}/approve`| Approve a pending request            |
| POST   | `/approvals/{approval_id}/reject` | Reject a pending request             |

Full curl examples live in [`docs/api_examples.md`](docs/api_examples.md).

### Example: agent request

```bash
curl -X POST http://localhost:8000/agent/request \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "user_role": "fan_support_agent",
    "message": "Find two tickets for the next game and tell me the bag policy."
  }'
```

### Example: blocked request (guest tries a fan-profile lookup)

```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "guest_001",
    "user_role": "guest",
    "tool_name": "lookup_fan_profile",
    "input_payload": { "fan_id": "fan_001" }
  }'
# -> decision: "blocked_permission_denied", status: "blocked"
```

### Example: high-risk request routed for approval

```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "manager_001",
    "user_role": "ticketing_manager",
    "tool_name": "request_ticket_hold",
    "input_payload": { "ticket_id": "tix_5001", "seat_count": 2 }
  }'
# -> decision: "pending_approval", approval_required: true
```

---

## Project structure

```text
app/       FastAPI app, config, DB, models, schemas, CRUD
gateway/   tool registry, permissions, risk, audit, approvals, router
tools/     simulated business-system tools (read fake JSON data)
data/      fake JSON data (schedule, policies, tickets, fans, content)
scripts/   seed / init helper
tests/     pytest suite
docs/      architecture, governance, API examples, fake data, interview notes
```

---

## Fake data disclaimer

All data is fictional. **Northstar Athletics** is an invented organization. No
real team, league, venue, ticketing system, CRM, or fan data is used. See
[`docs/fake_data.md`](docs/fake_data.md) and [`data/README.md`](data/README.md).

---

## Interview framing

> I built a portfolio-level sports agent governance gateway to explore how AI
> agents can safely interact with business systems. The project uses a fictional
> sports organization and fake data. Every tool call goes through permissions,
> risk scoring, audit logging, and human approval when needed. The goal was to
> show that useful AI agents need governance, not just model output.

More in [`docs/interview_notes.md`](docs/interview_notes.md).

---

## Future improvements

LangGraph workflow routing, Claude/OpenAI tool-calling, JWT auth, real RBAC
middleware, PostgreSQL + pgvector search, a React approvals dashboard, Slack/email
approval notifications, rate limiting, and OpenTelemetry tracing.
