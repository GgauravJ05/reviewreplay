"""Model features for next-day store sales."""
from __future__ import annotations

import pandas as pd

FEATURES = ["dow", "month", "promo", "holiday"]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["dow"] = out["date"].dt.dayofweek
    out["month"] = out["date"].dt.month
    return out
