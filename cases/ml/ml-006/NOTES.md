Lag features computed across the wrong axis. `data.py` (unchanged) documents and enforces date-then-
store ordering; the new `shift()` calls in `features.py` assume one store in date order. Verified by
execution with three stores. The test uses a single store, so it passes. Fix: sort by
`["store_id", "date"]` and use `groupby("store_id")["sales"].shift(k)` (and a grouped rolling mean).
