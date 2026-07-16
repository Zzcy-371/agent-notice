from datetime import datetime, timedelta

from agent_notice.filtering import select_daily_items, select_items
from agent_notice.models import Category, Item
from agent_notice.state import NoticeState


NOW = datetime(2026, 7, 13, 12, 0, 0)


def make_item(
    title: str,
    *,
    category: Category = Category.GITHUB,
    score: int = 0,
    published_at: datetime = NOW,
    url: str | None = None,
    summary: str = "",
    created_at: datetime | None = None,
) -> Item:
    return Item(
        title=title,
        url=url or f"https://example.com/{title.replace(' ', '-')}",
        source="test",
        category=category,
        published_at=published_at,
        summary=summary,
        score=score,
        created_at=created_at,
    )


def test_select_items_returns_empty_list_for_empty_collection() -> None:
    assert select_items([], NOW) == []


def test_select_items_excludes_item_with_nonmatching_title() -> None:
    item = make_item("Weekly database update")

    assert select_items([item], NOW) == []


def test_select_items_removes_duplicates_and_ranks_github_before_research() -> None:
    github = make_item("Hot agent repo", score=1)
    duplicate = make_item("Hot agent repo", score=99, url=github.url)
    research = make_item(
        "Agent paper", category=Category.RESEARCH, score=100
    )

    selected = select_items([research, duplicate, github], NOW)

    assert [item.title for item in selected] == ["Hot agent repo", "Agent paper"]


def test_select_items_respects_limit_after_sorting() -> None:
    newest = make_item("agent newest", score=5, published_at=NOW)
    older = make_item(
        "agent older", score=5, published_at=NOW - timedelta(hours=1)
    )

    assert select_items([older, newest], NOW, limit=1) == [newest]


def test_select_items_returns_empty_list_for_nonpositive_limit() -> None:
    item = make_item("agent repo")

    assert select_items([item], NOW, limit=0) == []
    assert select_items([item], NOW, limit=-1) == []


def test_select_items_excludes_items_older_than_report_day_window() -> None:
    stale = make_item("agent yesterday", published_at=NOW - timedelta(days=1, seconds=1))
    current = make_item("agent today", published_at=NOW - timedelta(days=1))

    assert select_items([stale, current], NOW) == [current]


def test_select_daily_items_reserves_four_mature_and_two_emerging() -> None:
    mature = [make_item(f"agent mature {index}", score=1000 - index) for index in range(4)]
    emerging = [make_item(f"agent emerging {index}", score=100 - index, created_at=NOW - timedelta(days=10)) for index in range(3)]

    selected = select_daily_items(mature + emerging, NOW, NoticeState())

    assert len(selected) == 6
    assert len({item.key for item in selected}) == 6
