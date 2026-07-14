import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


@dataclass
class DeliveryState:
    dates: set[str] = field(default_factory=set)

    @classmethod
    def load(cls, path: Path) -> "DeliveryState":
        return cls(set(json.loads(path.read_text(encoding="utf-8")))) if path.exists() else cls()

    def was_delivered(self, day: date) -> bool:
        return day.isoformat() in self.dates

    def mark_delivered(self, day: date) -> None:
        self.dates.add(day.isoformat())

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(sorted(self.dates)), encoding="utf-8")
