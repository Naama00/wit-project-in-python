"""
HistoryStore – lightweight persistence layer for the "issues over time" line chart.

Data is written to a JSON file on disk so it survives server restarts.
Thread safety is achieved with a simple threading.Lock; no external
dependencies are required.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import List

HISTORY_FILE = Path("graphs") / "history.json"


class PushRecord:
    """Represents one wit push event."""

    __slots__ = ("timestamp", "total_issues", "label")

    def __init__(self, timestamp: str, total_issues: int, label: str = "") -> None:
        self.timestamp = timestamp
        self.total_issues = total_issues
        self.label = label

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "total_issues": self.total_issues,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PushRecord":
        return cls(
            timestamp=data["timestamp"],
            total_issues=data["total_issues"],
            label=data.get("label", ""),
        )


class HistoryStore:
    """
    Appends a new :class:`PushRecord` on every push and provides the full
    history list for chart generation.

    Instantiate once and inject into the router / chart generator.
    """

    def __init__(self, history_file: Path = HISTORY_FILE) -> None:
        self._path = history_file
        self._lock = threading.Lock()

    def record(self, total_issues: int, label: str = "") -> None:
        """Appends a new push record to the history file."""
        entry = PushRecord(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            total_issues=total_issues,
            label=label,
        )
        with self._lock:
            records = self._load()
            records.append(entry.to_dict())
            self._save(records)

    def all_records(self) -> List[PushRecord]:
        """Returns all stored push records in chronological order."""
        with self._lock:
            return [PushRecord.from_dict(d) for d in self._load()]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load(self) -> list:
        if not self._path.exists():
            return []
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self, records: list) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
