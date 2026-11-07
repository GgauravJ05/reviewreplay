"""HTTP-facing handlers (framework glue omitted)."""
from __future__ import annotations

from .engine import price_quote
from .models import LineItem, Rule
from .store import load_rules, save_rules


def quote_handler(tenant_id: str, body: dict) -> dict:
    items = [LineItem(sku=i["sku"], unit_cents=int(i["unit_cents"]), qty=int(i["qty"]))
             for i in body["items"]]
    q = price_quote(tenant_id, items)
    return {"subtotal_cents": q.subtotal_cents, "discount_cents": q.discount_cents,
            "total_cents": q.total_cents, "applied": list(q.applied)}


def list_rules_handler(tenant_id: str) -> dict:
    return {"rules": [r.__dict__ for r in load_rules(tenant_id)]}


def replace_rules_handler(tenant_id: str, body: dict) -> dict:
    save_rules(tenant_id, [Rule(**r) for r in body["rules"]])
    return {"ok": True}
