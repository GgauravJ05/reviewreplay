"""Pagination helpers shared by all list endpoints."""
from __future__ import annotations

from typing import Sequence, TypeVar

T = TypeVar("T")

MAX_PER_PAGE = 100


def paginate(items: Sequence[T], page: int, per_page: int) -> list[T]:
    """Return one page of `items`. Pages are numbered from 1 (page=1 is the first page)."""
    if page < 1:
        raise ValueError("page starts at 1")
    per_page = max(1, min(per_page, MAX_PER_PAGE))
    start = (page - 1) * per_page
    return list(items[start:start + per_page])
