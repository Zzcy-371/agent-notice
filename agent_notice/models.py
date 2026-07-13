from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from urllib.parse import urlsplit, urlunsplit


class Category(StrEnum):
    GITHUB = "GitHub projects"
    RESEARCH = "Research and engineering"
    OFFICIAL = "Official updates"


def normalize_url(url: str) -> str:
    """Remove a URL fragment and a non-root trailing slash."""
    parts = urlsplit(url)
    path = parts.path.rstrip("/") if parts.path != "/" else "/"
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, ""))


@dataclass(frozen=True)
class Item:
    title: str
    url: str
    source: str
    category: Category
    published_at: datetime
    summary: str
    score: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "url", normalize_url(self.url))

    @property
    def key(self) -> str:
        return self.url


@dataclass(frozen=True)
class SourceResult:
    source: str
    items: tuple[Item, ...]
    error: str | None = None
