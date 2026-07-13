from datetime import UTC, datetime

from agent_notice.models import Category, Item
from agent_notice.state import NoticeState, should_notify


def test_existing_item_without_star_growth_is_suppressed(tmp_path):
    item = Item("Agent", "https://example.test/a", "GitHub", Category.GITHUB, datetime(2026, 7, 13, tzinfo=UTC), "agent tools", 10)
    state = NoticeState.load(tmp_path / "state.json")
    state.record([item])
    assert not should_notify(item, state)
