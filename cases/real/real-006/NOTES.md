# real-006 (attrs-3b0378dd)

Introduced in `e048efcb395443608d184a149c0adbca166cb833`: Perform attr order checks after field transformer. (#1401)
Fixed in `3b0378dd66d33ebddb52be85b8c4aac6a914b1a2`: Cope with `field_transformer` being a generator (#1417)

Why this is a bug (drafted by claude-sonnet-5-5):
Commit A moved the field_transformer call before code that iterates attrs multiple times, and kept the transformer's raw return value as attrs. A generator return is exhausted after the first pass, so later processing sees no attributes. Commit B fixes this by wrapping the result in tuple().

Reviewed by hand against the upstream fix `3b0378dd66d33ebddb52be85b8c4aac6a914b1a2` (https://github.com/python-attrs/attrs/pull/1417). Signals: message reference=True, blame agrees=True. No third-party code was run; the evidence is the fix commit, its tests and the linked issue.
