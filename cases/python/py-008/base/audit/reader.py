"""Read audit logs: one tab-separated record per line (timestamp, actor, action, severity)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from .models import SEVERITIES, Row


def parse_line(line: str) -> Row:
    at, actor, action, severity = line.rstrip("\n").split("\t")
    if severity not in SEVERITIES:
        raise ValueError(f"unknown severity {severity!r}")
    return Row(datetime.fromisoformat(at), actor, action, severity)


def read_rows(path: str | Path) -> Iterable[Row]:
    """All records in the file, skipping blank lines and # comments."""
    with open(path, encoding="utf-8") as fh:
        return [parse_line(line) for line in fh if line.strip() and not line.startswith("#")]
