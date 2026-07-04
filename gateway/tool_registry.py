"""Registry of tools the agent is allowed to call, with governance metadata.

Each tool declares its risk level, whether it requires human approval, and the
set of roles permitted to call it. This registry is the single source of truth
for the permission and risk layers.
"""
from typing import Dict

TOOLS: Dict[str, dict] = {
    "get_schedule": {
        "description": "Get the upcoming fake game schedule.",
        "risk_level": "low",
        "requires_approval": False,
        "allowed_roles": [
            "guest",
            "fan_support_agent",
            "ticketing_manager",
            "admin",
        ],
    },
    "search_policy": {
        "description": "Search fake venue policies (bag, parking, accessibility).",
        "risk_level": "low",
        "requires_approval": False,
        "allowed_roles": ["guest", "fan_support_agent", "admin"],
    },
    "search_content": {
        "description": "Search the fake content library.",
        "risk_level": "low",
        "requires_approval": False,
        "allowed_roles": ["content_editor", "admin"],
    },
    "lookup_fan_profile": {
        "description": "Look up a fake fan profile by id.",
        "risk_level": "medium",
        "requires_approval": False,
        "allowed_roles": ["fan_support_agent", "ticketing_manager", "admin"],
    },
    "search_ticket_options": {
        "description": "Search available ticket options for a fake event.",
        "risk_level": "medium",
        "requires_approval": False,
        "allowed_roles": ["fan_support_agent", "ticketing_manager", "admin"],
    },
    "draft_fan_response": {
        "description": "Draft a fan support response using deterministic templates.",
        "risk_level": "medium",
        "requires_approval": False,
        "allowed_roles": ["fan_support_agent", "admin"],
    },
    "request_ticket_hold": {
        "description": "Request a hold on tickets. High-risk, requires approval.",
        "risk_level": "high",
        "requires_approval": True,
        "allowed_roles": ["ticketing_manager", "admin"],
    },
}


def get_tool(tool_name: str) -> dict:
    """Return metadata for a tool, or ``None`` if it is not registered."""
    return TOOLS.get(tool_name)


def list_tools() -> Dict[str, dict]:
    """Return the full tool registry."""
    return TOOLS
