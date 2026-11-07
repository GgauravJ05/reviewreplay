Shared mutable cache value. The change only touches `store.py`; the in-place `+=` that corrupts the
cache is in unchanged `engine.py`. Before the change `load_rules` built a fresh list per call, so the
`+=` was harmless. Verified by execution: quotes on 2026-11-28 give 1450 then 2305 cents off; a July
quote afterwards gives 2305 (promo still applied twice). The tests pass because they never quote
during a promotion. Fix: return a tuple from the cached function, or `rules = [*load_rules(t), *promos]`.
