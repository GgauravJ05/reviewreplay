"""Product listing endpoint."""
from __future__ import annotations

from .paging import paginate

PRODUCTS = [f"product-{i}" for i in range(1, 251)]


def list_products(page: int = 1, per_page: int = 20) -> dict:
    return {"page": page, "items": paginate(PRODUCTS, page, per_page)}
