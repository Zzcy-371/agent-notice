from datetime import UTC, date, datetime

from agent_notice.models import Category, Item
from agent_notice.state import NoticeState, should_notify


def test_existing_item_without_star_growth_is_suppressed(tmp_path):
    item = Item("Agent", "https://example.test/a", "GitHub", Category.GITHUB, datetime(2026, 7, 13, tzinfo=UTC), "agent tools", 10)
    state = NoticeState.load(tmp_path / "state.json")
    state.record([item], date(2026, 7, 13))
    assert not should_notify(item, state)


def test_small_star_growth_does_not_repeat_a_project(tmp_path):
    original = Item("Agent", "https://example.test/a", "GitHub", Category.GITHUB, datetime(2026, 7, 13, tzinfo=UTC), "agent tools", 100)
    updated = Item("Agent", "https://example.test/a", "GitHub", Category.GITHUB, datetime(2026, 7, 14, tzinfo=UTC), "agent tools", 800)
    state = NoticeState.load(tmp_path / "state.json")
    state.record([original], date(2026, 7, 13))
    assert not should_notify(updated, state)
