"""Value types shared by the pricing package."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    """One pricing rule. `kind` is "percent_off" (value = percent) or "flat_off" (value = cents)."""
    name: str
    kind: str
    value: int
    min_subtotal_cents: int = 0


@dataclass(frozen=True)
class LineItem:
    sku: str
    unit_cents: int
    qty: int

    @property
    def total_cents(self) -> int:
        return self.unit_cents * self.qty


@dataclass(frozen=True)
class Quote:
    subtotal_cents: int
    discount_cents: int
    applied: tuple[str, ...]

    @property
    def total_cents(self) -> int:
        return self.subtotal_cents - self.discount_cents
