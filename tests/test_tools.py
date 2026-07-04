from tools.content import search_content
from tools.fans import lookup_fan_profile
from tools.policies import search_policy
from tools.responses import draft_fan_response
from tools.schedule import get_schedule
from tools.tickets import request_ticket_hold, search_ticket_options


def test_get_schedule_returns_events():
    events = get_schedule()
    assert len(events) >= 3
    assert events[0]["home_team"] == "Northstar Foxes"


def test_get_schedule_filter_by_event():
    events = get_schedule(event_id="evt_1001")
    assert len(events) == 1
    assert events[0]["event_id"] == "evt_1001"


def test_search_policy_matches_bag():
    results = search_policy("bag")
    assert any(p["category"] == "bag_policy" for p in results)


def test_search_content_matches_sponsor():
    results = search_content("sponsor")
    assert any("sponsor" in r["tags"] for r in results)


def test_lookup_fan_profile_found_and_missing():
    fan = lookup_fan_profile("fan_001")
    assert fan is not None
    assert fan["name"] == "Jordan Lee"
    assert lookup_fan_profile("fan_999") is None


def test_search_ticket_options_filters_by_event_and_seats():
    options = search_ticket_options("evt_1001", seat_count=2)
    assert len(options) >= 1
    assert all(o["event_id"] == "evt_1001" for o in options)
    assert all(o["available_seats"] >= 2 for o in options)


def test_request_ticket_hold_is_simulated_only():
    result = request_ticket_hold("tix_5001", 2)
    assert result["simulated"] is True
    assert result["ticket_id"] == "tix_5001"


def test_draft_fan_response_needs_review():
    draft = draft_fan_response({"ticket_options": [{"section": "114"}]})
    assert draft["needs_review"] is True
    assert "ticket" in draft["draft"].lower()
