"""Visit-level dataset for readmission prediction.

Each row is one hospital visit. Patients usually have several visits, so the same
`patient_id` appears on many rows; per-patient features (age, chronic conditions)
repeat across a patient's visits.
"""
from __future__ import annotations

import pandas as pd

FEATURES = ["age", "n_chronic", "length_of_stay", "n_prior_visits", "discharge_to_home"]
TARGET = "readmitted_30d"


def load(path: str) -> pd.DataFrame:
    return pd.read_parquet(path)
