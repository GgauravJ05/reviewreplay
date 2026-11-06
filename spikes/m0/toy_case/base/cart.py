"""Shopping cart helpers. Prices are integer cents."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Item:
    name: str
    price_cents: int
    qty: int = 1


def subtotal(items: list[Item]) -> int:
    """Sum of price * quantity over all items, in cents."""
    return sum(i.price_cents * i.qty for i in items)
