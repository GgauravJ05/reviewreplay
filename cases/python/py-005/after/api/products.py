"""Product listing endpoint."""
from __future__ import annotations

from .paging import paginate

PRODUCTS = [f"product-{i}" for i in range(1, 251)]


def list_products(page: int = 1, per_page: int = 20) -> dict:
    return {"page": page, "items": paginate(PRODUCTS, page, per_page)}


def list_products_by_offset(offset: int = 0, limit: int = 20) -> dict:
    """Offset/limit variant for the mobile app, which scrolls by item offset."""
    if offset < 0:
        raise ValueError("offset must be >= 0")
    page = offset // limit
    return {"offset": offset, "items": paginate(PRODUCTS, page, limit)}
