def test_every_call_writes_audit_log(client):
    client.post(
        "/tools/call",
        json={
            "user_id": "user_123",
            "user_role": "fan_support_agent",
            "tool_name": "get_schedule",
            "input_payload": {},
        },
    )
    logs = client.get("/audit-logs").json()
    assert len(logs) == 1
    assert logs[0]["tool_name"] == "get_schedule"
    assert logs[0]["decision"] == "allowed"


def test_blocked_calls_are_logged(client):
    client.post(
        "/tools/call",
        json={
            "user_id": "guest_001",
            "user_role": "guest",
            "tool_name": "lookup_fan_profile",
            "input_payload": {"fan_id": "fan_001"},
        },
    )
    logs = client.get("/audit-logs", params={"decision": "blocked_permission_denied"}).json()
    assert len(logs) == 1
    assert logs[0]["status"] == "blocked"


def test_approval_requests_are_logged(client):
    client.post(
        "/tools/call",
        json={
            "user_id": "manager_001",
            "user_role": "ticketing_manager",
            "tool_name": "request_ticket_hold",
            "input_payload": {"ticket_id": "tix_5001", "seat_count": 2},
        },
    )
    logs = client.get("/audit-logs", params={"decision": "pending_approval"}).json()
    assert len(logs) == 1
    assert logs[0]["approval_required"] == "true"


def test_audit_log_filter_by_tool_and_limit(client):
    for _ in range(3):
        client.post(
            "/tools/call",
            json={
                "user_id": "user_123",
                "user_role": "fan_support_agent",
                "tool_name": "get_schedule",
                "input_payload": {},
            },
        )
    logs = client.get("/audit-logs", params={"tool_name": "get_schedule", "limit": 2}).json()
    assert len(logs) == 2
    assert all(log["tool_name"] == "get_schedule" for log in logs)
