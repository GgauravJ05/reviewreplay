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


def test_lag_features():
    out = build_features(frame(n=20))
    first = out.iloc[0]
    assert first["date"] == pd.Timestamp("2026-01-08")       # first 7 days dropped
    assert first["sales_lag1"] == first["sales"] - 1
    assert first["sales_lag7"] == first["sales"] - 7
    assert first["sales_mean7"] == first["sales"] - 4         # mean of the previous 7 days
