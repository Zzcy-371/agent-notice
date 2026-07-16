import argparse
import json
import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

import feedparser

from agent_notice.config import Settings
from agent_notice.deepseek import DeepSeekClient, fallback_brief
from agent_notice.delivery_state import DeliveryState
from agent_notice.filtering import select_daily_items
from agent_notice.mailer import send_email
from agent_notice.models import Category
from agent_notice.reports import render_daily, render_email, render_weekly
from agent_notice.sources import GitHubSource, RssSource
from agent_notice.state import NoticeState, should_notify


ROOT = Path(__file__).parents[1]


def get_json(url: str) -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return json.load(response)


def post_json(url: str, body: dict, headers: dict) -> dict:
    request = Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def sources() -> list:
    config = json.loads((ROOT / "config" / "sources.json").read_text(encoding="utf-8"))
    result = [GitHubSource(get_json)]
    for source in config["rss_sources"]:
        result.append(RssSource(source["name"], Category(source["category"]), source["url"], feedparser.parse))
    return result


def run_daily(day: date, output_root: Path, settings: Settings) -> Path:
    delivery_path = output_root / "delivery.json"; delivery = DeliveryState.load(delivery_path)
    if delivery.was_delivered(day):
        return output_root / "daily" / f"{day.isoformat()}.md"
    now = datetime.combine(day, datetime.min.time(), UTC)
    results = [source.fetch(now) for source in sources()]
    if results and all(result.error for result in results):
        raise RuntimeError("All sources failed")
    state_path = output_root / "state.json"; state = NoticeState.load(state_path)
    items = select_daily_items((item for result in results for item in result.items), now, state)
    client = DeepSeekClient(os.environ.get("DEEPSEEK_API_KEY", ""), post_json) if os.environ.get("DEEPSEEK_API_KEY") else None
    briefs = {}
    for item in items:
        try: briefs[item.key] = client.brief(item) if client else fallback_brief(item)
        except Exception: briefs[item.key] = fallback_brief(item)
    report = render_daily(day, items, [result.error for result in results if result.error], briefs)
    path = output_root / "daily" / f"{day.isoformat()}.md"
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(report, encoding="utf-8")
    send_email(settings, f"Agent 技术日报 · {day.isoformat()}", render_email("Agent 技术日报", report))
    state.record(items, day); state_path.write_text(json.dumps(state.entries, ensure_ascii=False, indent=2), encoding="utf-8")
    delivery.mark_delivered(day); delivery.save(delivery_path)
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
