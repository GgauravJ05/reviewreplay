"""Cross-validated evaluation of the readmission model."""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import average_precision_score
from sklearn.model_selection import StratifiedKFold

from .data import FEATURES, TARGET, load


def cross_validate(path: str, folds: int = 5, seed: int = 0) -> list[float]:
    df = load(path)
    X, y = df[FEATURES].to_numpy(), df[TARGET].to_numpy()
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    scores = []
    for train_idx, test_idx in cv.split(X, y):
        model = GradientBoostingClassifier(random_state=seed)
        model.fit(X[train_idx], y[train_idx])
        proba = model.predict_proba(X[test_idx])[:, 1]
        scores.append(average_precision_score(y[test_idx], proba))
    print(f"PR-AUC: {np.mean(scores):.3f} ± {np.std(scores):.3f}")
    return scores
