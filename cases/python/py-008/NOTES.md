Generator consumed twice. The change is only in `reader.py`; the double iteration is in unchanged
`report.py` (`any(...)` then `for r in rows`). With a list this was fine. Verified by execution: the
summary drops from "2 high-severity events out of 3" to "1 ... out of 2", losing the first high event.
`export.py` iterates once and is fine. Tests only test the reader. Fix: `rows = list(read_rows(path))`
in summarize, or a single pass.
