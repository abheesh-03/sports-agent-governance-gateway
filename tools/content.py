"""Content tool: search the fake content library."""
from typing import List

from tools import load_data


def search_content(query: str) -> List[dict]:
    """Search fake content records by keyword.

    Matches the query (case-insensitive) against the title, body, content type,
    and tags. An empty query returns all content records.
    """
    content = load_data("content_library.json")
    if not query:
        return list(content)

    q = query.lower()
    matches = []
    for record in content:
        haystack = " ".join(
            [
                record.get("title", ""),
                record.get("body", ""),
                record.get("content_type", ""),
                " ".join(record.get("tags", [])),
            ]
        ).lower()
        if q in haystack or any(term in haystack for term in q.split()):
            matches.append(record)
    return matches
