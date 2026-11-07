"""Audit log records."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

SEVERITIES = ("low", "medium", "high")


@dataclass(frozen=True)
class Row:
    at: datetime
    actor: str
    action: str
    severity: str
