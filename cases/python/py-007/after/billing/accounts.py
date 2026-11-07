"""Customer accounts and their billing settings."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Account:
    id: str
    name: str
    tz: str                      # IANA zone, e.g. "America/New_York"
    session_fee_cents: int       # flat fee per GPU session
    hourly_rate_cents: int       # price per GPU hour


ACCOUNTS = {
    "a-100": Account("a-100", "Initech", "America/New_York", 250, 180),
    "a-200": Account("a-200", "Umbrella", "Europe/Berlin", 250, 165),
}
