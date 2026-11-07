"""Monthly invoice lines for GPU usage."""
from __future__ import annotations

import math
from dataclasses import dataclass

from .accounts import ACCOUNTS
from .sessions import Session


@dataclass(frozen=True)
class Line:
    description: str
    amount_cents: int


def billable_hours(session: Session) -> int:
    """GPU time is billed per started hour (a 61-minute session is 2 hours)."""
    seconds = (session.end - session.start).total_seconds()
    return max(1, math.ceil(seconds / 3600))


def session_charge_cents(session: Session) -> int:
    account = ACCOUNTS[session.account_id]
    return account.session_fee_cents + billable_hours(session) * account.hourly_rate_cents


def invoice_lines(sessions: list[Session]) -> list[Line]:
    lines = []
    for s in sorted(sessions, key=lambda s: s.start):
        when = f"{s.start:%Y-%m-%d %H:%M %Z} to {s.end:%H:%M %Z}"
        hours = billable_hours(s)
        lines.append(Line(f"GPU {s.gpu}, {when} ({hours} h)", session_charge_cents(s)))
    return lines


def invoice_total_cents(sessions: list[Session]) -> int:
    return sum(line.amount_cents for line in invoice_lines(sessions))
