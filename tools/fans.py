"""Fans tool: look up fake fan profiles."""
from typing import Optional

from tools import load_data


def lookup_fan_profile(fan_id: str) -> Optional[dict]:
    """Return a fake fan profile by id, or ``None`` if not found."""
    fans = load_data("fans.json")
    for fan in fans:
        if fan.get("fan_id") == fan_id:
            return fan
    return None
