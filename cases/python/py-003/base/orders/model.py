"""Order aggregate.

Invariant: an order always has at least one event. `created` is recorded in __post_init__,
and events are append-only (nothing ever removes them).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class Event:
    kind: str
    at: datetime


@dataclass
class Order:
    id: str
    events: list[Event] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.events.append(Event("created", datetime.now(timezone.utc)))

    def record(self, kind: str) -> None:
        self.events.append(Event(kind, datetime.now(timezone.utc)))
