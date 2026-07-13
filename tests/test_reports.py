from datetime import UTC, date, datetime

from agent_notice.models import Category, Item
from agent_notice.reports import render_daily, render_email, render_weekly


NOW = datetime(2026, 7, 13, tzinfo=UTC)


def item(title: str, category: Category) -> Item:
    return Item(title, f"https://example.test/{title}", "test", category, NOW, "Agent update", 1)


def test_daily_groups_categories_in_priority_order():
    report = render_daily(date(2026, 7, 13), [item("official", Category.OFFICIAL), item("repo", Category.GITHUB)], ["OpenAI: timeout"])
    assert report.index("## GitHub projects") < report.index("## Official updates")
    assert "Source failures: OpenAI: timeout" in report


def test_weekly_and_email_preserve_report_links():
    report = render_weekly("2026-W28", {date(2026, 7, 13): "- [Repo](https://example.test/repo)"})
    assert "# Agent 技术周报 · 2026-W28" in report
    assert "https://example.test/repo" in render_email("Weekly", report)
