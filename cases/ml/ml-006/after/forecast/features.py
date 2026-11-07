"""Model features for next-day store sales."""
from __future__ import annotations

import pandas as pd

FEATURES = ["dow", "month", "promo", "holiday", "sales_lag1", "sales_lag7", "sales_mean7"]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["dow"] = out["date"].dt.dayofweek
    out["month"] = out["date"].dt.month
    # Recent history is the strongest signal for tomorrow's sales.
    out["sales_lag1"] = out["sales"].shift(1)    # the store's sales yesterday
    out["sales_lag7"] = out["sales"].shift(7)    # same weekday last week
    out["sales_mean7"] = out["sales"].shift(1).rolling(7).mean()
    # The first week has no history; drop it rather than impute.
    return out.dropna(subset=["sales_lag1", "sales_lag7", "sales_mean7"]).reset_index(drop=True)
