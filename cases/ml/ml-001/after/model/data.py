"""Load the churn dataset. One row per customer."""
from __future__ import annotations

import pandas as pd

NUMERIC = ["tenure_months", "monthly_spend", "support_tickets"]
TARGET = "churned"


def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df.dropna(subset=[TARGET])
