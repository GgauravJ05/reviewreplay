"""GPU sessions reconstructed from start/stop events."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .accounts import ACCOUNTS
from .clock import parse_utc, to_local


@dataclass(frozen=True)
class Session:
    account_id: str
    gpu: str
    start: datetime   # in the account's local time zone (shown on invoices and the dashboard)
    end: datetime     # same zone as start


def sessions_from_events(events: list[dict]) -> list[Session]:
    """Pair each "start" event with the next "stop" for the same (account, gpu)."""
    open_: dict[tuple[str, str], datetime] = {}
    out: list[Session] = []
    for ev in sorted(events, key=lambda e: parse_utc(e["at"])):
        key = (ev["account_id"], ev["gpu"])
        tz = ACCOUNTS[ev["account_id"]].tz
        at = to_local(parse_utc(ev["at"]), tz)
        if ev["type"] == "start":
            open_[key] = at
        elif ev["type"] == "stop" and key in open_:
            out.append(Session(ev["account_id"], ev["gpu"], open_.pop(key), at))
    return out
