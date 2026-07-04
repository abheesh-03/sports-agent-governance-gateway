def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "sports-agent-governance-gateway"


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"status": "ok", "service": "sports-agent-governance-gateway"}


def test_tools_endpoint(client):
    resp = client.get("/tools")
    assert resp.status_code == 200
    tools = resp.json()
    names = {t["name"] for t in tools}
    assert "get_schedule" in names
    assert "request_ticket_hold" in names
    # request_ticket_hold is high risk and requires approval.
    hold = next(t for t in tools if t["name"] == "request_ticket_hold")
    assert hold["risk_level"] == "high"
    assert hold["requires_approval"] is True
