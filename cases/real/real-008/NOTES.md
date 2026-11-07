# real-008 (rich-30e5ed61)

Introduced in `7a38204cb51dee761792a6b086784602899f06df`: fix for panel title
Fixed in `30e5ed61a6064220fe2ff40f4713463488ee6d07`: fix(panel): fix title missing panel background

Why this is a bug (drafted by claude-sonnet-5-5):
Commit B reverts A's change, which caused panel titles/subtitles to lose the panel's background style (issue #3569).

Reviewed by hand against the upstream fix `30e5ed61a6064220fe2ff40f4713463488ee6d07` (https://github.com/Textualize/rich/issues/3569). Signals: message reference=True, blame agrees=True. No third-party code was run; the evidence is the fix commit, its tests and the linked issue.
