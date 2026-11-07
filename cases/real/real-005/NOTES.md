# real-005 (werkzeug-f0a1733f)

Introduced in `67d870b9039e69df6e7ff4e8b9f6bdb51189b004`: Correctly implement multipart parsing for empty fields (#2639)
Fixed in `f0a1733f52a7241f51cc519593233e8be6aeaa0e`: Fix the parsing of large multipart bodies

Why this is a bug (drafted by claude-sonnet-5-5):
Commit B fixes the no-boundary path in _parse_data introduced in A: last_newline used the whole buffer, which starts with a newline in DATA_START, and the boundary shortcut was dropped, causing slow parsing.

Reviewed by hand against the upstream fix `f0a1733f52a7241f51cc519593233e8be6aeaa0e` (https://github.com/pallets/werkzeug/issues/2658). Signals: message reference=True, blame agrees=True. No third-party code was run; the evidence is the fix commit, its tests and the linked issue.
