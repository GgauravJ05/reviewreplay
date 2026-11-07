# real-007 (attrs-c9150d27)

Introduced in `89a890a3262273514619d1881c6a8b0fe26c66ac`: Change __getstate__ and __setstate__ to use a dict (#1004) (#1009)
Fixed in `c9150d278ced32056d73c239ff64034e5056bcb6`: Fix backward compatibility with pickles before v22.2.0 (#1085)

Why this is a bug (drafted by claude-sonnet-5-5):
Commit B fixes a regression: the new __setstate__ only handles dict state, so slotted instances pickled by older attrs (tuple state) cannot be restored.

Reviewed by hand against the upstream fix `c9150d278ced32056d73c239ff64034e5056bcb6` (https://github.com/python-attrs/attrs/pull/1085). Signals: message reference=True, blame agrees=True. No third-party code was run; the evidence is the fix commit, its tests and the linked issue.
