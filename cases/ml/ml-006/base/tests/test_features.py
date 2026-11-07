import pandas as pd

from forecast.features import build_features


def frame(n=10, store="s1"):
    dates = pd.date_range("2026-01-01", periods=n, freq="D")
    return pd.DataFrame({"date": dates, "store_id": store, "sales": range(100, 100 + n),
                         "promo": 0, "holiday": 0})


def test_calendar_features():
    out = build_features(frame())
    assert out.loc[0, "dow"] == 3      # 2026-01-01 is a Thursday
    assert out.loc[0, "month"] == 1
