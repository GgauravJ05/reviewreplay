"""Cart model. All money values are integer cents."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Line:
    sku: str
    unit_cents: int
    qty: int


@dataclass
class Cart:
    lines: list[Line] = field(default_factory=list)

    def add(self, sku: str, unit_cents: int, qty: int = 1) -> None:
        if qty <= 0:
            raise ValueError("qty must be positive")
        self.lines.append(Line(sku, unit_cents, qty))

    def subtotal_cents(self) -> int:
        return sum(line.unit_cents * line.qty for line in self.lines)
