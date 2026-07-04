def test_agent_request_ticket_and_policy(client):
    resp = client.post(
        "/agent/request",
        json={
            "user_id": "user_123",
            "user_role": "fan_support_agent",
            "message": "Find two tickets for the next game and tell me the bag policy.",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    # Ticket + policy + schedule (message mentions "game") should be planned.
    assert "search_ticket_options" in body["allowed_tools"]
    assert "search_policy" in body["allowed_tools"]
    assert body["blocked_tools"] == []
    assert len(body["audit_log_ids"]) >= 2


def test_allowed_single_tool_call_executes(client):
    resp = client.post(
        "/tools/call",
        json={
            "user_id": "user_123",
            "user_role": "fan_support_agent",
            "tool_name": "search_policy",
            "input_payload": {"query": "bag policy"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "allowed"
    assert body["status"] == "completed"
    assert body["result"]  # non-empty policy match
    assert body["audit_log_id"] is not None


def test_blocked_tool_call_is_denied_and_logged(client):
    resp = client.post(
        "/tools/call",
        json={
            "user_id": "guest_001",
            "user_role": "guest",
            "tool_name": "lookup_fan_profile",
            "input_payload": {"fan_id": "fan_001"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "blocked_permission_denied"
    assert body["status"] == "blocked"
    assert body["result"] is None

    # The denial must be recorded in the audit log.
    logs = client.get("/audit-logs", params={"user_id": "guest_001"}).json()
    assert any(log["decision"] == "blocked_permission_denied" for log in logs)


def test_classify_visual_asset_executes_and_logs(client):
    resp = client.post(
        "/tools/call",
        json={
            "user_id": "editor_001",
            "user_role": "content_editor",
            "tool_name": "classify_visual_asset",
            "input_payload": {"asset_id": "asset_001"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "allowed"
    assert body["status"] == "completed"
    assert body["risk_level"] == "medium"
    assert body["result"]["predicted_class"] == "event"
    assert body["result"]["model_source"] == "simulated_pytorch_vision_service"

    # The classification must be recorded in the audit log.
    logs = client.get("/audit-logs", params={"tool_name": "classify_visual_asset"}).json()
    assert len(logs) == 1
    assert logs[0]["decision"] == "allowed"
    assert logs[0]["user_role"] == "content_editor"


def test_guest_cannot_classify_visual_asset_via_api(client):
    resp = client.post(
        "/tools/call",
        json={
            "user_id": "guest_001",
            "user_role": "guest",
            "tool_name": "classify_visual_asset",
            "input_payload": {"asset_id": "asset_001"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "blocked_permission_denied"
    assert body["status"] == "blocked"
    assert body["result"] is None


def test_high_risk_tool_creates_approval_request(client):
    resp = client.post(
        "/tools/call",
        json={
            "user_id": "manager_001",
            "user_role": "ticketing_manager",
            "tool_name": "request_ticket_hold",
            "input_payload": {"ticket_id": "tix_5001", "seat_count": 2},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "pending_approval"
    assert body["status"] == "pending_approval"
    assert body["approval_required"] is True
    assert body["approval_id"] is not None
