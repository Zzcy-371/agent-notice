import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from agent_notice.models import Item


def _fingerprint(item: Item) -> str:
    return hashlib.sha256(f"{item.title}\n{item.summary}".encode()).hexdigest()


@dataclass
class NoticeState:
    entries: dict[str, dict] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "NoticeState":
        return cls(json.loads(path.read_text(encoding="utf-8"))) if path.exists() else cls()

    def record(self, items: list[Item]) -> None:
        for item in items:
            self.entries[item.key] = {"score": item.score, "fingerprint": _fingerprint(item)}


def should_notify(item: Item, state: NoticeState, star_delta: int = 5000) -> bool:
    previous = state.entries.get(item.key)
    return previous is None or item.score - previous["score"] >= star_delta or previous["fingerprint"] != _fingerprint(item)
