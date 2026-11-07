"""Daily security summary sent to the on-call channel."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .reader import read_rows


@dataclass
class Summary:
    total: int = 0
    by_actor: Counter = field(default_factory=Counter)
    high: list = field(default_factory=list)

    @property
    def quiet(self) -> bool:
        return not self.high


def summarize(path: str | Path) -> Summary:
    rows = read_rows(path)
    # Most days have no high-severity events; skip the per-actor breakdown then.
    if not any(r.severity == "high" for r in rows):
        return Summary()
    summary = Summary()
    for r in rows:
        summary.total += 1
        summary.by_actor[r.actor] += 1
        if r.severity == "high":
            summary.high.append(r)
    return summary


def render(summary: Summary) -> str:
    if summary.quiet:
        return "No high-severity audit events today."
    top = ", ".join(f"{a} ({n})" for a, n in summary.by_actor.most_common(3))
    lines = [f"{len(summary.high)} high-severity events out of {summary.total}. Most active: {top}."]
    lines += [f"- {r.at:%H:%M} {r.actor}: {r.action}" for r in summary.high]
    return "\n".join(lines)
