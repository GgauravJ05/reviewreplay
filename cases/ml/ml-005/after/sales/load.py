from __future__ import annotations

import pandas as pd


def orders(path: str) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"order_id": str, "customer_id": str}, parse_dates=["created_at"])


def customer_segments(path: str) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"customer_id": str, "month": str})
