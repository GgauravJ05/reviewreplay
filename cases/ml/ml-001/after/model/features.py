"""Feature engineering."""
from __future__ import annotations

import pandas as pd

from .data import NUMERIC


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["spend_per_month_of_tenure"] = out["monthly_spend"] / out["tenure_months"].clip(lower=1)
    # Standardize numeric columns so the logistic regression converges faster.
    cols = NUMERIC + ["spend_per_month_of_tenure"]
    out[cols] = (out[cols] - out[cols].mean()) / out[cols].std()
    return out
