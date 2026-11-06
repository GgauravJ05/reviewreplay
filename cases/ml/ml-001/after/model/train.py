"""Train and evaluate the churn model."""
from __future__ import annotations

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from .data import NUMERIC, TARGET, load
from .features import build_features

FEATURES = NUMERIC + ["spend_per_month_of_tenure"]


def main(path: str) -> float:
    df = build_features(load(path))
    train, test = train_test_split(df, test_size=0.2, stratify=df[TARGET], random_state=0)
    model = LogisticRegression(max_iter=1000)
    model.fit(train[FEATURES], train[TARGET])
    auc = roc_auc_score(test[TARGET], model.predict_proba(test[FEATURES])[:, 1])
    print(f"test AUC: {auc:.3f}")
    return auc
