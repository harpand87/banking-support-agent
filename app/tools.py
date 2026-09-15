from typing import Any

from app.knowledge import search


class ToolError(Exception):
    pass


def search_product_policy(query: str) -> dict[str, Any]:
    if not query.strip() or len(query) > 200:
        raise ToolError("query must be between 1 and 200 characters")
    items = search(query)
    return {"results": [{"source": item.source, "title": item.title, "text": item.text} for item in items]}


def find_support_route(topic: str) -> dict[str, str]:
    routes = {
        "fraud": "official fraud team through the authenticated bank channel",
        "dispute": "official dispute team through the authenticated bank channel",
        "general": "official customer support channel",
    }
    key = topic.lower().strip()
    if key not in routes:
        raise ToolError("unsupported support topic")
    return {"topic": key, "route": routes[key]}
