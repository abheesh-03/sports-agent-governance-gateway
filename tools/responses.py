"""Responses tool: draft deterministic fan support replies.

No LLM is used in version 1. Drafts are assembled from simple templates using
whatever context the caller provides.
"""
from typing import Any, Dict


def draft_fan_response(context: Dict[str, Any]) -> dict:
    """Draft a fan support response from a context dictionary.

    The draft is deterministic and always flagged as needing human review
    before it is sent to a fan.
    """
    context = context or {}
    parts = ["Thanks for reaching out."]

    if context.get("ticket_options"):
        parts.append("I found some ticket options that match your request.")
    if context.get("policy_answer") or context.get("policy"):
        parts.append("I also matched the relevant venue policy for you.")
    if context.get("event") or context.get("schedule"):
        parts.append("Here are the upcoming event details you asked about.")

    if len(parts) == 1:
        # No specific context supplied; use a generic acknowledgement.
        parts.append(
            "A member of our fan support team will follow up with the details."
        )

    return {
        "draft": " ".join(parts),
        "needs_review": True,
    }
