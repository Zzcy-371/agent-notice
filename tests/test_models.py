from datetime import UTC, datetime

from agent_notice.models import Category, Item


NOW = datetime(2026, 7, 13, tzinfo=UTC)


def test_item_removes_fragment_from_url():
    item = Item(
        "Title",
        "https://example.test/a/#part",
        "GitHub",
        Category.GITHUB,
        NOW,
        "agent tools",
        5,
    )

    assert item.url == "https://example.test/a"
    assert item.key == "https://example.test/a"
