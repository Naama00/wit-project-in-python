"""
HistoryStore – persists push records so the line chart can show trends over time.

Records are stored in a simple JSON file (.wit/push_history.json) on the server's
working directory.  The store is intentionally lightweight: no database, no ORM.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List


HISTORY_FILE = Path("push_history.json")


@dataclass
class PushRecord:
    """One entry per /analyze call."""
    timestamp: str          # ISO-8601 string, e.g. "2024-05-01T14:23:00"
    total_issues: int
    filenames: List[str]    # files that were analysed in this push


class HistoryStore:
    """
    Reads and writes push history to a local JSON file.

    Thread-safety: not guaranteed; suitable for single-process development use.
    """

    def __init__(self, path: Path = HISTORY_FILE) -> None:
        self._path = path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append(self, record: PushRecord) -> None:
        """Appends *record* to the history file, creating it if necessary."""
        records = self._load()
        records.append(record)
        self._save(records)

    def all_records(self) -> List[PushRecord]:
        """Returns all push records in chronological order."""
        return self._load()

    def clear(self) -> None:
        """Deletes all stored history (useful for tests)."""
        if self._path.exists():
            self._path.unlink()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load(self) -> List[PushRecord]:
        if not self._path.exists():
            return []
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            return [PushRecord(**item) for item in raw]
        except (json.JSONDecodeError, TypeError, KeyError):
            return []

    def _save(self, records: List[PushRecord]) -> None:
        data = [asdict(r) for r in records]
        self._path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
