"""Risk layer: classify a tool call's risk level and approval requirement."""
from gateway.tool_registry import get_tool


def get_tool_risk(tool_name: str) -> dict:
    """Return the risk metadata for a tool.

    Unknown tools are treated as high risk requiring approval, on the principle
    that anything not explicitly registered is not trusted.
    """
    tool = get_tool(tool_name)
    if tool is None:
        return {"risk_level": "high", "requires_approval": True}

    return {
        "risk_level": tool["risk_level"],
        "requires_approval": tool["requires_approval"],
    }
