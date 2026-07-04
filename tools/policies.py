"""Policies tool: search fake venue policies."""
from typing import List

from tools import load_data


def search_policy(query: str) -> List[dict]:
    """Search fake venue policies by keyword.

    Matches the query (case-insensitive) against the policy category, title,
    and body. An empty query returns all policies.
    """
    policies = load_data("policies.json")
    if not query:
        return list(policies)

    q = query.lower()
    matches = []
    for policy in policies:
        haystack = " ".join(
            [
                policy.get("category", ""),
                policy.get("title", ""),
                policy.get("body", ""),
            ]
        ).lower()
        if q in haystack or any(term in haystack for term in q.split()):
            matches.append(policy)
    return matches
