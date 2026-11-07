"""Time helpers. Events arrive in UTC; everything customer-facing is in the account's zone."""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo


@lru_cache(maxsize=None)
def zone(name: str) -> ZoneInfo:
    return ZoneInfo(name)


def parse_utc(text: str) -> datetime:
    """Parse an ISO-8601 timestamp that must carry an offset (events are always UTC)."""
    ts = datetime.fromisoformat(text)
    if ts.tzinfo is None:
        raise ValueError(f"timestamp without offset: {text!r}")
    return ts


def to_local(ts: datetime, tz_name: str) -> datetime:
    return ts.astimezone(zone(tz_name))
