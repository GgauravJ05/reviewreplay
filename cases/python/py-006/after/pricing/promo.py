"""Site-wide promotions layered on top of tenant rules."""
from __future__ import annotations

from datetime import datetime, timezone

from .models import Rule

# (start, end, rule): end is exclusive
_CAMPAIGNS = [
    (datetime(2026, 11, 27, tzinfo=timezone.utc), datetime(2026, 12, 1, tzinfo=timezone.utc),
     Rule(name="black-friday", kind="percent_off", value=10)),
]


def active_promos(now: datetime) -> list[Rule]:
    return [rule for start, end, rule in _CAMPAIGNS if start <= now < end]
