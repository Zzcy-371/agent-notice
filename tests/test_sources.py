from datetime import UTC, datetime

from agent_notice.models import Category
from agent_notice.sources import GitHubSource, RssSource


NOW = datetime(2026, 7, 13, tzinfo=UTC)


def test_github_source_maps_agent_repository():
    requested_urls: list[str] = []

    def get_json(url: str) -> dict:
        requested_urls.append(url)
        return {
            "items": [
                {
                    "name": "agent-kit",
                    "html_url": "https://github.com/a/agent-kit",
                    "description": "MCP agent tools",
                    "stargazers_count": 42,
                    "updated_at": "2026-07-13T00:00:00Z",
                    "language": "Python",
                    "license": {"spdx_id": "MIT"},
                }
            ]
        }

    result = GitHubSource(get_json).fetch(NOW)

    assert "agent" in requested_urls[0].lower()
    assert result.error is None
    assert result.source == "GitHub"
    assert len(result.items) == 1
    assert result.items[0].title == "agent-kit"
    assert result.items[0].url == "https://github.com/a/agent-kit"
    assert result.items[0].summary == "MCP agent tools"
    assert result.items[0].category is Category.GITHUB
    assert result.items[0].published_at == NOW
    assert result.items[0].score == 42


def test_github_source_isolates_api_failure():
    def get_json(url: str) -> dict:
        raise OSError("unavailable")

    result = GitHubSource(get_json).fetch(NOW)

    assert result.source == "GitHub"
    assert result.items == ()
    assert result.error == "unavailable"


def test_rss_source_maps_feed_entry():
    def parse_feed(url: str) -> dict:
        assert url == "https://rss.test/arxiv"
        return {
            "entries": [
                {
                    "title": "Agent Planning",
                    "link": "https://paper.test/1",
                    "description": "A multi-agent method",
                    "published": "2026-07-13T00:00:00Z",
                }
            ]
        }

    result = RssSource(
        "arXiv", Category.RESEARCH, "https://rss.test/arxiv", parse_feed
    ).fetch(NOW)

    assert result.error is None
    assert result.source == "arXiv"
    assert len(result.items) == 1
    assert result.items[0].title == "Agent Planning"
    assert result.items[0].url == "https://paper.test/1"
    assert result.items[0].summary == "A multi-agent method"
    assert result.items[0].category is Category.RESEARCH
    assert result.items[0].published_at == NOW


def test_rss_source_isolates_parser_failure():
    def parse_feed(url: str) -> dict:
        raise ValueError("invalid feed")

    result = RssSource(
        "arXiv", Category.RESEARCH, "https://rss.test/arxiv", parse_feed
    ).fetch(NOW)

    assert result.source == "arXiv"
    assert result.items == ()
    assert result.error == "invalid feed"
