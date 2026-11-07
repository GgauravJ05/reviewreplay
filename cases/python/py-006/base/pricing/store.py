"""Read access to each tenant's pricing rules."""
from __future__ import annotations

from . import db
from .models import Rule


def load_rules(tenant_id: str) -> list[Rule]:
    """All active rules for a tenant, in the order they should be applied."""
    return [Rule(**row) for row in db.fetch_rules(tenant_id)]


def save_rules(tenant_id: str, rules: list[Rule]) -> None:
    db.put_rules(tenant_id, [r.__dict__ for r in rules])
