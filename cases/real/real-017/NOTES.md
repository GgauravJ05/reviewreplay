# real-017 (cobra-e1ded5cd)

Source: [spf13/cobra](https://github.com/spf13/cobra), Apache-2.0 licence, Copyright The Cobra Authors.

Introduced in `fb8031162c2ffab270774f13c6904bb04cbba5a7`: perf(bash-v2): speed up filtering entries with descriptions (#1689)
Fixed in `e1ded5cd9480aa9921a8cb0f646b6b569ac1b9d8`: fix(bash-v2): skip empty completions when filtering descriptions (#1691)

Why this is a bug:
The bash completion script is a Go string template. The introducing commit replaced
`comp=$(compgen -W "$comp" -- "$cur")` plus an emptiness check with a plain prefix match,
`[[ $comp == "$cur"* ]] || continue`, to avoid a subshell per candidate. The loop reads lines
from `printf "%s\n" "$out"`, so its last read is an empty line. `compgen` dropped that line; the
prefix match keeps it when `$cur` is empty, adding an empty completion.

The fix message says "`read` gives a last null value following a trailing newline" and
"Regression from fb8031162c2ffab270774f13c6904bb04cbba5a7"; it adds one line that skips empty
entries.

Severity is minor (a cosmetic extra candidate), but the change is 3 lines, so this case tests
whether a reviewer reads shell code embedded in Go carefully.

How it was picked: `reviewreplay mine` (multi-language miner). The fix message names the commit
and blame agrees. Signals: message reference=True, blame agrees=True.

No third-party code was run; the evidence is the two diffs and the fix's message.
