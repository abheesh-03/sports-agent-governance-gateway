"""Schedule tool: read fake upcoming events."""
from typing import List, Optional

from tools import load_data


def get_schedule(event_id: Optional[str] = None) -> List[dict]:
    """Return the fake event schedule.

    If ``event_id`` is provided, only matching events are returned.
    """
    events = load_data("schedule.json")
    if event_id:
        return [e for e in events if e.get("event_id") == event_id]
    return list(events)
