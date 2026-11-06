"""Revenue by customer segment."""
from __future__ import annotations

import pandas as pd


def revenue_by_segment(orders: pd.DataFrame, segments: pd.DataFrame) -> pd.DataFrame:
    """Total revenue (cents) per customer segment."""
    merged = orders.merge(segments[["customer_id", "segment"]], on="customer_id", how="inner")
    return (merged.groupby("segment", as_index=False)["amount_cents"].sum()
                  .rename(columns={"amount_cents": "revenue_cents"}))
