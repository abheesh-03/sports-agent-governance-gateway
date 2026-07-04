def _create_hold(client):
    return client.post(
        "/tools/call",
        json={
            "user_id": "manager_001",
            "user_role": "ticketing_manager",
            "tool_name": "request_ticket_hold",
            "input_payload": {"ticket_id": "tix_5001", "seat_count": 2},
        },
    ).json()


def test_pending_approvals_endpoint(client):
    _create_hold(client)
    resp = client.get("/approvals/pending")
    assert resp.status_code == 200
    pending = resp.json()
    assert len(pending) == 1
    assert pending[0]["tool_name"] == "request_ticket_hold"
    assert pending[0]["status"] == "pending"


def test_approve_request_flow(client):
    hold = _create_hold(client)
    approval_id = hold["approval_id"]

    resp = client.post(
        f"/approvals/{approval_id}/approve",
        json={"reviewer": "admin_001", "notes": "Approved for ticketing workflow."},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "approved"
    assert body["reviewer"] == "admin_001"

    # No longer pending.
    pending = client.get("/approvals/pending").json()
    assert pending == []


def test_reject_request_flow(client):
    hold = _create_hold(client)
    approval_id = hold["approval_id"]

    resp = client.post(
        f"/approvals/{approval_id}/reject",
        json={"reviewer": "admin_001", "notes": "Does not match policy."},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "rejected"
    assert body["review_notes"] == "Does not match policy."


def test_approve_missing_request_returns_404(client):
    resp = client.post(
        "/approvals/9999/approve",
        json={"reviewer": "admin_001", "notes": "n/a"},
    )
    assert resp.status_code == 404
