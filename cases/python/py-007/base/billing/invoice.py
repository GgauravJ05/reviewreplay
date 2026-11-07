"""Monthly invoice lines for GPU usage."""
from __future__ import annotations

from dataclasses import dataclass

from .accounts import ACCOUNTS
from .sessions import Session


@dataclass(frozen=True)
class Line:
    description: str
    amount_cents: int


def session_charge_cents(session: Session) -> int:
    return ACCOUNTS[session.account_id].session_fee_cents


def invoice_lines(sessions: list[Session]) -> list[Line]:
    lines = []
    for s in sorted(sessions, key=lambda s: s.start):
        when = f"{s.start:%Y-%m-%d %H:%M %Z} to {s.end:%H:%M %Z}"
        lines.append(Line(f"GPU {s.gpu}, {when}", session_charge_cents(s)))
    return lines


def invoice_total_cents(sessions: list[Session]) -> int:
    return sum(line.amount_cents for line in invoice_lines(sessions))
