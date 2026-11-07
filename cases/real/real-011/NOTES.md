# real-011 (black-455de770)

Introduced in `e4aaa8a9947d951eb1e69979c3c58e197adbe40f`: Fix incorrect f-string tokenization (#4332)
Fixed in `455de7703ea2c4144f8c1bb2c352974ac9b2403f`: Fix another f-string regression (#4339)

Why this is a bug (drafted by claude-sonnet-5-5):
Commit B changes the condition so that a multi-line string token is also yielded as a plain STRING when the state is STATE_IN_BRACES. Commit A only did this when the state was STATE_NOT_FSTRING, so it handled the in-braces case wrongly.

Reviewed by hand against the upstream fix `455de7703ea2c4144f8c1bb2c352974ac9b2403f` (https://github.com/psf/black/pull/4339). Signals: message reference=False, blame agrees=False. No third-party code was run; the evidence is the fix commit, its tests and the linked issue.
