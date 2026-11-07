"""Tiny stand-in for the rules database (the real one is a network call)."""
from __future__ import annotations

QUERIES = 0

_RULES = {
    "acme": [
        {"name": "acme-loyalty", "kind": "percent_off", "value": 5},
        {"name": "acme-bulk", "kind": "flat_off", "value": 1000, "min_subtotal_cents": 50_000},
    ],
    "globex": [
        {"name": "globex-partner", "kind": "percent_off", "value": 12},
    ],
}


def fetch_rules(tenant_id: str) -> list[dict]:
    global QUERIES
    QUERIES += 1
    return [dict(r) for r in _RULES.get(tenant_id, [])]


def put_rules(tenant_id: str, rules: list[dict]) -> None:
    _RULES[tenant_id] = [dict(r) for r in rules]
