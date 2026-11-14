# real-014 (gin-d9307dbc)

Source: [gin-gonic/gin](https://github.com/gin-gonic/gin), MIT licence, Copyright (c) 2014 Manuel Martínez-Almeida.

Introduced in `e46bd521859fdfc83c508f1d42c92cb7f91e9fcb`: refactor(context): add an optional permission parameter to the SaveUploadedFile method (#4068) (#4088)
Fixed in `d9307dbcbbe796a64d9e0ef23452da888dd7f904`: fix(context): skip chmod on pre-existing dirs in SaveUploadedFile (#4702)
Issue: https://github.com/gin-gonic/gin/issues/4622 ("SaveUploadedFile: unexpected chmod on existing directories (breaks /tmp usage)")

Why this is a bug:
Before this commit, `SaveUploadedFile` only called `os.MkdirAll(filepath.Dir(dst), 0o750)`, which
does nothing to a directory that already exists. This commit added an optional `perm` and an
unconditional `os.Chmod(filepath.Dir(dst), perm[0])` after `MkdirAll`. Saving into a directory
the process does not own, such as `/tmp`, now fails with "operation not permitted", and saving into
a directory it does own silently changes that directory's mode.

The fix stats the directory before `MkdirAll` and calls `os.Chmod` only when the directory did not
exist. Its regression test checks that a pre-existing directory's permissions are unchanged. The
fix message says it "restores the behaviour from v1.10.1".

How it was picked: mined with `reviewreplay mine` (language-aware miner, PR #16). The miner blamed
`a4baac6e` ("Avoid using filepath.Dir twice"), a later refactor that only moved the
`filepath.Dir` call. `git log -S'os.Chmod(' -- context.go` shows the chmod was added in
`e46bd521`, so that is the introducing commit used here. Signals: message reference=False,
blame agrees=False.

No third-party code was run; the evidence is the fix commit, its test and the linked issue.
