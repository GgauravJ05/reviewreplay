# real-020 (logrus-f42291d3)

Source: [sirupsen/logrus](https://github.com/sirupsen/logrus), MIT licence, Copyright (c) 2014 Simon Eskildsen.

Introduced in `78f838918da24e1487e8341227d48cc80bb73966`: fix race condition for SetFormatter and properly fix SetReportCaller race as well
Fixed in `f42291d3f9146a01a496abaa9fd438ca5a228f4c`: fix: resolve deadlock when formatting triggers reentrant logging

Why this is a bug:
The commit moved `entry.Logger.mu.Lock()` from just before `Out.Write` to before
`Formatter.Format(entry)`, to stop a race with `SetFormatter`. Formatting calls user code on field
values (for example `MarshalJSON` in the JSON formatter). When that code logs through the same
logger, the nested call blocks on the mutex its own goroutine already holds, and the program
hangs.

The fix message says "This fixes a deadlock introduced in commit 78f8389, which moved the lock to
before Format() to fix a data race on Logger.Formatter", and links issues #1448 and #1440. It
copies the formatter under the lock and formats outside it.

The change is 4 lines in `entry.go` plus a test, so this case tests whether a reviewer thinks about
what runs while a lock is held, not just the race being fixed.

How it was picked: `reviewreplay mine` (multi-language miner). The fix message names the commit
and blame agrees. Signals: message reference=True, blame agrees=True.

No third-party code was run; the evidence is the two diffs and the fix's message.
