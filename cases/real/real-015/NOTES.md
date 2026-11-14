# real-015 (testify-0bf6b946)

Source: [stretchr/testify](https://github.com/stretchr/testify), MIT licence, Copyright (c) 2012-2020 Mat Ryer, Tyler Bunnell and contributors.

Introduced in `b5ce16571001d6e96e1693ac891fed5c2510c651`: fixing panic in calls to assertion with nil m.mutex (#1212)
Fixed in `0bf6b946d985309f37a4364b0b1f01a92698730e`: mock.AssertExpectationsForObjects fix panic with wrong testObject type (#1795)
Issue: https://github.com/stretchr/testify/issues/1227

Why this is a bug:
`AssertExpectationsForObjects` accepted a `mock.Mock` passed by value: it matched
`obj.(Mock)`, logged a deprecation warning and checked the mock through `&m`. This commit
changed the assertion to `obj.(*Mock)` (as part of turning the mutex back into a value to satisfy
`go vet`). A `Mock` value no longer matches, so it reaches the unchecked
`obj.(assertExpectationser)`. `AssertExpectations` has a pointer receiver, so a value doesn't
implement the interface, and the call panics.

The fix message says the by-value form "worked ... and logged a warning. This was broken by
#1212". The fix keeps `*Mock` only, but replaces the panic with a checked assertion and a test
error. Its regression test passes `Mock{}` and expects one `Errorf`.

How it was picked: mined with `reviewreplay mine` (language-aware miner, PR #16). The fix message
names #1212, and blame on the changed lines points to the same commit. Signals: message
reference=True, blame agrees=True.

No third-party code was run; the evidence is the two diffs, the fix's test and the linked issue.
