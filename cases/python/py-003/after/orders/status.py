"""Order status helpers used by the support dashboard."""
from __future__ import annotations

import logging

from .model import Order
from .notify import Mailer

log = logging.getLogger(__name__)


def latest_status(order: Order) -> str:
    return order.events[-1].kind


def notify_status(order: Order, mailer: Mailer, email: str) -> None:
    status = latest_status(order)
    try:
        mailer.send(email, f"Order {order.id}: {status}", f"Your order is now {status}.")
    except Exception:
        log.exception("status email failed for order %s", order.id)
        raise
