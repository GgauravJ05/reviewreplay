"""Revenue by region."""
from __future__ import annotations

import pandas as pd


def revenue_by_region(orders: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    """Total revenue (cents) and order count per region. Orders whose customer is
    missing from `customers` are reported under region "unknown"."""
    merged = orders.merge(customers[["customer_id", "region"]], on="customer_id",
                          how="left", validate="many_to_one")
    merged["region"] = merged["region"].fillna("unknown")
    out = (merged.groupby("region", as_index=False)
                 .agg(revenue_cents=("amount_cents", "sum"), orders=("order_id", "count")))
    return out.sort_values("revenue_cents", ascending=False, ignore_index=True)
