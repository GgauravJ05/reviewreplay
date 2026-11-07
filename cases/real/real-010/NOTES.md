# real-010 (black-dba3c269)

Introduced in `d7a28dd78631fb962da95fb2d2de0e18ca6754a4`: Enforce a blank line after a nested class in stubs (#3564)
Fixed in `dba3c2695c59fdb11825dbdf8f3b0ab6e0b368b2`: Fix bug introduced in #3564. (#3615)

Why this is a bug (drafted by claude-sonnet-5-5):
The fix changes the truthiness check on a Line object into a check of its depth, correcting a bug introduced when previous_defs changed from ints to Lines.

Reviewed by hand against the upstream fix `dba3c2695c59fdb11825dbdf8f3b0ab6e0b368b2` (https://github.com/psf/black/pull/3615). Signals: message reference=True, blame agrees=False. No third-party code was run; the evidence is the fix commit, its tests and the linked issue.
