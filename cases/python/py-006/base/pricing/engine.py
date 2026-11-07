"""Turn a cart into a quote by applying the tenant's rules, then any active promotions."""
from __future__ import annotations

from datetime import datetime, timezone

from .models import LineItem, Quote, Rule
from .promo import active_promos
from .store import load_rules


def _discount(rule: Rule, running_cents: int) -> int:
    if rule.kind == "percent_off":
        return running_cents * rule.value // 100
    if rule.kind == "flat_off":
        return min(rule.value, running_cents)
    raise ValueError(f"unknown rule kind {rule.kind!r}")


def price_quote(tenant_id: str, items: list[LineItem], now: datetime | None = None) -> Quote:
    now = now or datetime.now(timezone.utc)
    subtotal = sum(i.total_cents for i in items)
    rules = load_rules(tenant_id)
    rules += active_promos(now)
    running, applied = subtotal, []
    for rule in rules:
        if subtotal < rule.min_subtotal_cents:
            continue
        off = _discount(rule, running)
        if off:
            running -= off
            applied.append(rule.name)
    return Quote(subtotal_cents=subtotal, discount_cents=subtotal - running, applied=tuple(applied))
