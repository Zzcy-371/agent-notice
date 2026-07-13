import argparse
import json
import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

import feedparser

from agent_notice.config import Settings
from agent_notice.filtering import select_items
from agent_notice.mailer import send_email
from agent_notice.models import Category
from agent_notice.reports import render_daily, render_email, render_weekly
from agent_notice.sources import GitHubSource, RssSource


ROOT = Path(__file__).parents[1]


def get_json(url: str) -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return json.load(response)


def sources() -> list:
    config = json.loads((ROOT / "config" / "sources.json").read_text(encoding="utf-8"))
    result = [GitHubSource(get_json)]
    for source in config["rss_sources"]:
        result.append(RssSource(source["name"], Category(source["category"]), source["url"], feedparser.parse))
    return result


def run_daily(day: date, output_root: Path, settings: Settings) -> Path:
    now = datetime.combine(day, datetime.min.time(), UTC)
    results = [source.fetch(now) for source in sources()]
    if results and all(result.error for result in results):
        raise RuntimeError("All sources failed")
    items = select_items((item for result in results for item in result.items), now)
    report = render_daily(day, items, [result.error for result in results if result.error])
    path = output_root / "daily" / f"{day.isoformat()}.md"
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(report, encoding="utf-8")
    send_email(settings, f"Agent 技术日报 · {day.isoformat()}", render_email("Agent 技术日报", report))
    return path


def run_weekly(day: date, output_root: Path, settings: Settings) -> Path:
    reports = {candidate: (output_root / "daily" / f"{candidate.isoformat()}.md").read_text(encoding="utf-8") for candidate in (day - timedelta(days=offset) for offset in range(7)) if (output_root / "daily" / f"{candidate.isoformat()}.md").exists()}
    week = f"{day.isocalendar().year}-W{day.isocalendar().week:02d}"
    report = render_weekly(week, reports); path = output_root / "weekly" / f"{week}.md"
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(report, encoding="utf-8")
    send_email(settings, f"Agent 技术周报 · {week}", render_email("Agent 技术周报", report)); return path


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=("daily", "weekly")); args = parser.parse_args()
    settings = Settings.from_env(os.environ); today = datetime.now(UTC).date(); output = ROOT / "reports"
    (run_daily if args.command == "daily" else run_weekly)(today, output, settings)


if __name__ == "__main__": main()
