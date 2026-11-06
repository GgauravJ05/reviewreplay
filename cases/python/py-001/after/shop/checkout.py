"""Checkout totals."""
from __future__ import annotations

from .cart import Cart
from .config import FLAT_SHIPPING_CENTS, FREE_SHIPPING_THRESHOLD


def shipping_cents(cart: Cart) -> int:
    """Flat-rate shipping, waived for orders at or above the free-shipping threshold."""
    if not cart.lines:
        return 0
    if cart.subtotal_cents() >= FREE_SHIPPING_THRESHOLD:
        return 0
    return FLAT_SHIPPING_CENTS


def total_cents(cart: Cart) -> int:
    return cart.subtotal_cents() + shipping_cents(cart)
