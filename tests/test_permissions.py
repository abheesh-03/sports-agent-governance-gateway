from gateway.permissions import is_tool_allowed


def test_guest_can_search_policies():
    allowed, reason = is_tool_allowed("guest", "search_policy")
    assert allowed is True
    assert reason == "allowed"


def test_guest_cannot_lookup_fan_profile():
    allowed, reason = is_tool_allowed("guest", "lookup_fan_profile")
    assert allowed is False
    assert reason == "role_not_allowed"


def test_content_editor_can_search_content():
    allowed, reason = is_tool_allowed("content_editor", "search_content")
    assert allowed is True


def test_fan_support_agent_can_search_tickets():
    allowed, reason = is_tool_allowed("fan_support_agent", "search_ticket_options")
    assert allowed is True


def test_ticketing_manager_can_request_ticket_hold():
    allowed, reason = is_tool_allowed("ticketing_manager", "request_ticket_hold")
    assert allowed is True


def test_fan_support_agent_cannot_request_ticket_hold():
    allowed, reason = is_tool_allowed("fan_support_agent", "request_ticket_hold")
    assert allowed is False
    assert reason == "role_not_allowed"


def test_unknown_tool_is_rejected():
    allowed, reason = is_tool_allowed("admin", "delete_everything")
    assert allowed is False
    assert reason == "unknown_tool"
