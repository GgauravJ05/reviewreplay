"""Read audit logs: one tab-separated record per line (timestamp, actor, action, severity)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterator

from .models import SEVERITIES, Row


def parse_line(line: str) -> Row:
    at, actor, action, severity = line.rstrip("\n").split("\t")
    if severity not in SEVERITIES:
        raise ValueError(f"unknown severity {severity!r}")
    return Row(datetime.fromisoformat(at), actor, action, severity)


def read_rows(path: str | Path) -> Iterator[Row]:
    """Records in the file, skipping blank lines and # comments.

    Yields rows lazily: production logs reach several GB a day and no longer fit in memory.
    """
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip() and not line.startswith("#"):
                yield parse_line(line)
