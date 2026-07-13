from collections.abc import Iterable
from datetime import datetime, timedelta

from agent_notice.models import Category, Item


_KEYWORDS = ("agent", "agentic", "multi-agent", "mcp", "tool use", "tool-use")
_CATEGORY_PRIORITY = {
    Category.GITHUB: 0,
    Category.RESEARCH: 1,
    Category.OFFICIAL: 2,
}
_REPORT_DAY = timedelta(days=1)


def select_items(items: Iterable[Item], now: datetime, limit: int = 15) -> list[Item]:
    """Return recent, relevant items ranked for a daily report."""
    if limit <= 0:
        return []

    cutoff = now - _REPORT_DAY
    relevant_items = [
        item
        for item in items
        if item.published_at >= cutoff
        and any(keyword in f"{item.title} {item.summary}".lower() for keyword in _KEYWORDS)
    ]
    ranked = sorted(
        relevant_items,
        key=lambda item: (
            _CATEGORY_PRIORITY[item.category],
            -item.score,
            -item.published_at.timestamp(),
        ),
    )

    selected: list[Item] = []
    seen_keys: set[str] = set()
    for item in ranked:
        if item.key not in seen_keys:
            selected.append(item)
            seen_keys.add(item.key)
        if len(selected) == limit:
            break
    return selected
