"""Load daily store sales."""
from __future__ import annotations

import pandas as pd

COLUMNS = ["date", "store_id", "sales", "promo", "holiday"]


def load_sales(path: str) -> pd.DataFrame:
    """One row per (date, store). Rows are ordered by date, then store, so each day's stores are
    contiguous; the regional dashboard reads the frame in this order."""
    df = pd.read_csv(path, parse_dates=["date"])
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    if df.duplicated(["date", "store_id"]).any():
        raise ValueError("duplicate (date, store_id) rows")
    return df.sort_values(["date", "store_id"]).reset_index(drop=True)[COLUMNS]
