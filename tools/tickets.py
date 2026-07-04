"""Tickets tool: search fake ticket inventory and simulate holds."""
from typing import List

from tools import load_data


def search_ticket_options(event_id: str, seat_count: int = 2) -> List[dict]:
    """Return available ticket options for an event with enough seats.

    Filters the fake inventory to ``available`` listings for the given event
    that have at least ``seat_count`` seats.
    """
    tickets = load_data("tickets.json")
    return [
        t
        for t in tickets
        if t.get("event_id") == event_id
        and t.get("status") == "available"
        and t.get("available_seats", 0) >= seat_count
    ]


def request_ticket_hold(ticket_id: str, seat_count: int) -> dict:
    """Simulate a ticket hold action.

    In version 1 this does NOT modify ticket inventory. It returns a simulated
    action payload only. The governance layer is responsible for routing this
    high-risk action through human approval before it is considered executed.
    """
    return {
        "action": "request_ticket_hold",
        "ticket_id": ticket_id,
        "seat_count": seat_count,
        "simulated": True,
        "note": "Simulated hold. No real inventory was modified.",
    }
