from collections.abc import Iterable
from datetime import datetime, timedelta

from agent_notice.models import Category, Item
from agent_notice.state import NoticeState, is_in_cooldown, should_notify


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


def select_daily_items(items: Iterable[Item], now: datetime, state: NoticeState) -> list[Item]:
    candidates = [item for item in select_items(items, now, limit=100) if should_notify(item, state) and not is_in_cooldown(item, state, now.date())]
    mature = [item for item in candidates if not item.created_at or item.created_at < now - timedelta(days=90)][:4]
    used = {item.key for item in mature}
    emerging = [item for item in candidates if item.key not in used and item.created_at and item.created_at >= now - timedelta(days=90)]
    emerging.sort(key=lambda item: (item.score - state.entries.get(item.key, {}).get("score", item.score), item.published_at.timestamp()), reverse=True)
    return mature + emerging[:2]
