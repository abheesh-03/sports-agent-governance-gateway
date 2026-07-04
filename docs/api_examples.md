# API Examples

All examples assume the server is running locally on port 8000:

```bash
uvicorn app.main:app --reload
```

## Health

```bash
curl http://localhost:8000/health
```

```json
{ "status": "ok", "service": "sports-agent-governance-gateway" }
```

## List tools

```bash
curl http://localhost:8000/tools
```

Returns each registered tool with its `risk_level`, `requires_approval`, and
`allowed_roles`.

## Agent request: tickets + policy

```bash
curl -X POST http://localhost:8000/agent/request \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "user_role": "fan_support_agent",
    "message": "Find two tickets for the next game and tell me the bag policy."
  }'
```

Keyword routing plans `search_ticket_options`, `search_policy`, and `get_schedule`,
runs each through the gateway, and returns combined results plus the audit log ids.

## Single governed tool call (allowed)

```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "user_role": "fan_support_agent",
    "tool_name": "search_policy",
    "input_payload": { "query": "bag policy" }
  }'
```

```json
{
  "decision": "allowed",
  "status": "completed",
  "risk_level": "low",
  "result": [ { "policy_id": "pol_001", "title": "Clear Bag Policy", "...": "..." } ]
}
```

## Blocked request: guest tries a fan-profile lookup

```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "guest_001",
    "user_role": "guest",
    "tool_name": "lookup_fan_profile",
    "input_payload": { "fan_id": "fan_001" }
  }'
```

```json
{
  "decision": "blocked_permission_denied",
  "status": "blocked",
  "reason": "role_not_allowed"
}
```

## Classify a visual asset (simulated PyTorch vision service)

A content editor classifies a fake visual asset. The gateway governs the call
(permission + risk + audit); the tool returns pre-computed metadata from a
simulated external PyTorch vision service — no real model runs in this repo.

```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "editor_001",
    "user_role": "content_editor",
    "tool_name": "classify_visual_asset",
    "input_payload": { "asset_id": "asset_001" }
  }'
```

```json
{
  "decision": "allowed",
  "status": "completed",
  "risk_level": "medium",
  "result": {
    "asset_id": "asset_001",
    "filename": "postgame_celebration.jpg",
    "predicted_class": "event",
    "confidence": 0.91,
    "visual_tags": ["celebration", "crowd", "sponsor_board"],
    "model_source": "simulated_pytorch_vision_service"
  }
}
```

A guest calling `classify_visual_asset` is denied with
`blocked_permission_denied`, and an unknown `asset_id` returns a safe
`{"error": "asset_not_found"}` result (still logged).

## Pending approval: request a ticket hold

```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "manager_001",
    "user_role": "ticketing_manager",
    "tool_name": "request_ticket_hold",
    "input_payload": { "ticket_id": "tix_5001", "seat_count": 2 }
  }'
```

```json
{
  "decision": "pending_approval",
  "status": "pending_approval",
  "approval_required": true,
  "approval_id": 1
}
```

## View pending approvals

```bash
curl http://localhost:8000/approvals/pending
```

## Approve a request

```bash
curl -X POST http://localhost:8000/approvals/1/approve \
  -H "Content-Type: application/json" \
  -d '{ "reviewer": "admin_001", "notes": "Approved for ticketing manager workflow." }'
```

## Reject a request

```bash
curl -X POST http://localhost:8000/approvals/1/reject \
  -H "Content-Type: application/json" \
  -d '{ "reviewer": "admin_001", "notes": "Rejected because request does not match policy." }'
```

## View audit logs

```bash
curl http://localhost:8000/audit-logs
```

Optional filters: `user_id`, `tool_name`, `decision`, `limit`.

```bash
curl "http://localhost:8000/audit-logs?decision=blocked_permission_denied&limit=10"
```
