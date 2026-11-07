"""Read access to each tenant's pricing rules."""
from __future__ import annotations

from functools import lru_cache

from . import db
from .models import Rule


# Rules change a few times a month but are read on every quote, and the DB round trip
# dominated quote latency. Cache per tenant; writes go through save_rules, which invalidates.
@lru_cache(maxsize=1024)
def load_rules(tenant_id: str) -> list[Rule]:
    """All active rules for a tenant, in the order they should be applied."""
    return [Rule(**row) for row in db.fetch_rules(tenant_id)]


def save_rules(tenant_id: str, rules: list[Rule]) -> None:
    db.put_rules(tenant_id, [r.__dict__ for r in rules])
    load_rules.cache_clear()
