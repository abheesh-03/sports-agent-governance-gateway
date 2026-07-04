# Governance Model

This document describes the governance rules the gateway enforces on every tool
call.

## Why unrestricted agent access is risky

AI agents are only useful if they can take action. But in a real business, an
agent that can freely touch ticketing, payments, CRM, fan profiles, content
rights, and venue operations is a liability:

- It can leak sensitive fan/customer data.
- It can take irreversible actions (holds, refunds, changes) with no oversight.
- It leaves no trail of what happened or why.
- It cannot distinguish a safe read from a sensitive write.

Governance replaces "the agent can do anything" with "the agent can do exactly
what its role permits, at a known risk level, with sensitive actions gated behind
a human, and everything recorded."

## Roles

| Role                | Intended behavior                                     |
| ------------------- | ----------------------------------------------------- |
| `guest`             | Search public schedule and policies only              |
| `fan_support_agent` | Policies, tickets, schedule, fan lookup, draft replies|
| `content_editor`    | Search content records and classify visual assets     |
| `ticketing_manager` | Tickets, schedule, fan lookup, request ticket holds   |
| `admin`             | All tools, approvals, and audit logs                  |

Permissions are declared per-tool via `allowed_roles` in the tool registry.

## Risk levels

Every tool is classified `low`, `medium`, or `high`.

| Risk   | Meaning                                             | Approval |
| ------ | --------------------------------------------------- | -------- |
| low    | Public, read-only, no sensitive data                | no       |
| medium | Read of sensitive data or a draft action            | no (logged) |
| high   | A consequential/write-like action                   | **yes**  |

| Tool                    | Risk   | Approval required     |
| ----------------------- | ------ | --------------------- |
| `get_schedule`          | low    | no                    |
| `search_policy`         | low    | no                    |
| `search_content`        | low    | no                    |
| `lookup_fan_profile`    | medium | no, but logged carefully |
| `search_ticket_options` | medium | no                    |
| `draft_fan_response`    | medium | no                    |
| `classify_visual_asset` | medium | no                    |
| `request_ticket_hold`   | high   | yes                   |

`classify_visual_asset` is a governed *adapter* to an external vision service.
The gateway treats it like any other tool (permission + risk + audit), even
though the actual classification would run in a separate PyTorch vision service.
No CV model runs in this repo; the tool returns fake pre-computed metadata.

Any tool that is **not registered** is treated as high risk and requires
approval — the system fails closed.

## Approval rules (human-in-the-loop)

High-risk actions never execute immediately. Instead:

1. Permission is checked.
2. Risk is marked high.
3. An approval record is created with status `pending`.
4. The response is `pending_approval` (nothing was executed).
5. The request is written to the audit log.
6. A `ticketing_manager` or `admin` approves or rejects it via
   `POST /approvals/{id}/approve` or `.../reject`.

Approval status values: `pending`, `approved`, `rejected`.

## Audit logging

Every governed tool call writes an audit log row, regardless of outcome. Fields:

```text
id, request_id, user_id, user_role, tool_name, input_payload,
decision, risk_level, approval_required, status, reason, created_at
```

Decision values used by the gateway:

```text
allowed
blocked_permission_denied
blocked_unknown_tool
pending_approval
```

Approval outcomes (`approved` / `rejected`) live on the approval record and can
be correlated by `request_id`.

## Summary of guarantees

1. **Permissioned** — a role can only call tools it is allowed to.
2. **Risk-aware** — every call carries a known risk classification.
3. **Human-gated** — high-risk actions require explicit human approval.
4. **Auditable** — every decision is recorded, including denials.
5. **Fail-closed** — unknown tools are denied / treated as high risk.
