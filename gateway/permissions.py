"""Permission layer: decide whether a role may call a tool."""
from typing import Tuple

from gateway.tool_registry import get_tool


def is_tool_allowed(user_role: str, tool_name: str) -> Tuple[bool, str]:
    """Check whether ``user_role`` is permitted to call ``tool_name``.

    Returns a tuple of ``(allowed, reason)`` where reason is one of:
    ``allowed``, ``unknown_tool``, or ``role_not_allowed``.
    """
    tool = get_tool(tool_name)
    if tool is None:
        return False, "unknown_tool"

    if user_role in tool["allowed_roles"]:
        return True, "allowed"

    return False, "role_not_allowed"
