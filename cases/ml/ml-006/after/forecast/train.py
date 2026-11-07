"""Train the next-day sales model with a time-based holdout."""
from __future__ import annotations

import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

from .data import load_sales
from .features import FEATURES, build_features

TARGET = "sales"


def train(path: str, cutoff: str = "2026-09-01") -> tuple[HistGradientBoostingRegressor, float]:
    df = build_features(load_sales(path))
    train_df = df[df["date"] < pd.Timestamp(cutoff)]
    test_df = df[df["date"] >= pd.Timestamp(cutoff)]
    model = HistGradientBoostingRegressor(random_state=0)
    model.fit(train_df[FEATURES], train_df[TARGET])
    mae = mean_absolute_error(test_df[TARGET], model.predict(test_df[FEATURES]))
    return model, mae
