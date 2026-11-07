# real-009 (jsonschema-52c24196)

Introduced in `90ea77961987da03188f5b9972631f89d20c4798`: Fix a regression with RefResolver-based resolution in newly created drafts
Fixed in `52c2419625e875e7e7c8124bcbfae8cde92bbda3`: Fix an additional regression with RefResolver and pointer resolution.

Why this is a bug (drafted by claude-sonnet-5-5):
Commit B fixes a regression in commit A: push_scope is called unconditionally with id_of(self.schema), which can be None, breaking pointer resolution.

Reviewed by hand against the upstream fix `52c2419625e875e7e7c8124bcbfae8cde92bbda3` (https://github.com/python-jsonschema/jsonschema/issues/1124). Signals: message reference=False, blame agrees=False. No third-party code was run; the evidence is the fix commit, its tests and the linked issue.
