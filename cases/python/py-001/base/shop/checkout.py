"""Checkout totals."""
from __future__ import annotations

from .cart import Cart


def total_cents(cart: Cart) -> int:
    return cart.subtotal_cents()
