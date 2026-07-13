from collections.abc import Mapping, Sequence
from datetime import date

from agent_notice.deepseek import ChineseBrief
from agent_notice.models import Category, Item


ORDER = (Category.GITHUB, Category.RESEARCH, Category.OFFICIAL)


def render_daily(day: date, items: Sequence[Item], failures: Sequence[str] = (), briefs: Mapping[str, ChineseBrief] | None = None) -> str:
    lines = [f"# Agent 技术日报 · {day.isoformat()}", ""]
    for category in ORDER:
        lines.extend((f"## {category.value}", ""))
        section = []
        for item in items:
            if item.category is not category:
                continue
            brief = (briefs or {}).get(item.key)
            if brief:
                section.extend((f"### [{brief.title}]({item.url})", *(f"- {point}" for point in brief.bullets), ""))
            else:
                section.append(f"- [{item.title}]({item.url}) — {item.summary}")
        lines.extend(section or ["- No new items."])
        lines.append("")
    if failures:
        lines.extend((f"Source failures: {', '.join(failures)}", ""))
    return "\n".join(lines)


def render_weekly(week: str, daily_reports: Mapping[date, str]) -> str:
    lines = [f"# Agent 技术周报 · {week}", "", "## Daily report index", ""]
    if not daily_reports:
        lines.append("No daily reports found.")
    for day, report in sorted(daily_reports.items()):
        lines.extend((f"### {day.isoformat()}", "", report, ""))
    return "\n".join(lines)


def render_email(subject: str, report: str) -> str:
    items = [line for line in report.splitlines() if line.startswith("- [")]
    return f"{subject}\n\n" + "\n".join(items[:15])
