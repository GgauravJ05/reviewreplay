from datetime import datetime, timezone

from pricing.engine import price_quote
from pricing.models import LineItem

JULY = datetime(2026, 7, 1, tzinfo=timezone.utc)


def test_percent_rule():
    q = price_quote("acme", [LineItem("a", 10_000, 1)], now=JULY)
    assert q.discount_cents == 500
    assert q.applied == ("acme-loyalty",)


def test_bulk_rule_needs_minimum():
    q = price_quote("acme", [LineItem("a", 10_000, 6)], now=JULY)
    assert q.applied == ("acme-loyalty", "acme-bulk")


def test_unknown_tenant_has_no_rules():
    assert price_quote("nobody", [LineItem("a", 100, 1)], now=JULY).discount_cents == 0
