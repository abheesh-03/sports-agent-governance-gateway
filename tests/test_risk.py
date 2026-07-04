from gateway.risk import get_tool_risk


def test_low_risk_tools_do_not_require_approval():
    for tool in ("get_schedule", "search_policy", "search_content"):
        risk = get_tool_risk(tool)
        assert risk["risk_level"] == "low"
        assert risk["requires_approval"] is False


def test_medium_risk_tools():
    for tool in ("lookup_fan_profile", "search_ticket_options", "draft_fan_response"):
        risk = get_tool_risk(tool)
        assert risk["risk_level"] == "medium"
        assert risk["requires_approval"] is False


def test_high_risk_tool_requires_approval():
    risk = get_tool_risk("request_ticket_hold")
    assert risk["risk_level"] == "high"
    assert risk["requires_approval"] is True


def test_unknown_tool_defaults_to_high_risk():
    risk = get_tool_risk("mystery_tool")
    assert risk["risk_level"] == "high"
    assert risk["requires_approval"] is True
