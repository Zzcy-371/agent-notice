from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlencode

from agent_notice.models import Category, Item, SourceResult


def _value(record: Any, name: str, default: Any = None) -> Any:
    if isinstance(record, Mapping):
        return record.get(name, default)
    return getattr(record, name, default)


def _published_at(value: str | None, fallback: datetime) -> datetime:
    if not value:
        return fallback
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return fallback
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed


class GitHubSource:
    """Collect repositories matching the Agent topic from GitHub search."""

    def __init__(self, get_json: Callable[[str], Mapping[str, Any]]) -> None:
        self._get_json = get_json

    def fetch(self, now: datetime) -> SourceResult:
        query = urlencode(
            {"q": "agent in:name,description", "sort": "stars", "order": "desc"}
        )
        try:
            payload = self._get_json(f"https://api.github.com/search/repositories?{query}")
            items = tuple(self._item(repo, now) for repo in payload.get("items", ()))
            return SourceResult("GitHub", items)
        except Exception as error:
            return SourceResult("GitHub", (), str(error))

    @staticmethod
    def _item(repository: Mapping[str, Any], now: datetime) -> Item:
        return Item(
            title=repository["name"],
            url=repository["html_url"],
            source="GitHub",
            category=Category.GITHUB,
            published_at=_published_at(repository.get("updated_at"), now),
            summary=repository.get("description") or "",
            score=int(repository.get("stargazers_count") or 0),
        )


class RssSource:
    """Collect entries from an RSS feed using an injected parser."""

    def __init__(
        self,
        name: str,
        category: Category,
        url: str,
        parse_feed: Callable[[str], Any],
    ) -> None:
        self._name = name
        self._category = category
        self._url = url
        self._parse_feed = parse_feed

    def fetch(self, now: datetime) -> SourceResult:
        try:
            feed = self._parse_feed(self._url)
            entries = _value(feed, "entries", ())
            items = tuple(self._item(entry, now) for entry in entries)
            return SourceResult(self._name, items)
        except Exception as error:
            return SourceResult(self._name, (), str(error))

    def _item(self, entry: Any, now: datetime) -> Item:
        return Item(
            title=_value(entry, "title", ""),
            url=_value(entry, "link", ""),
            source=self._name,
            category=self._category,
            published_at=_published_at(
                _value(entry, "published") or _value(entry, "updated"), now
            ),
            summary=_value(entry, "description", "") or _value(entry, "summary", ""),
            score=0,
        )
