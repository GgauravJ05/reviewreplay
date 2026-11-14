# real-018 (cobra-a97f9fd4)

Source: [spf13/cobra](https://github.com/spf13/cobra), Apache-2.0 licence, Copyright The Cobra Authors.

Introduced in `6c3c1163c6df19860515103199e880122ba49e80`: feat: add CompletionFunc type to help with completions (#2220)
Fixed in `a97f9fd47b290016526c8af2dac0531fea5cd773`: fix CompletionFunc implementation (#2234)

Why this is a bug:
Before this commit, `Command.ValidArgsFunction` and `RegisterFlagCompletionFunc` used the
unnamed type `func(cmd *Command, args []string, toComplete string) ([]string, ShellCompDirective)`.
The commit introduced `type CompletionFunc func(...)`, a new defined type, and used it for both.
Go only allows assigning a named func type to an unnamed one with the same signature, not to a
different named type, so projects with their own named completion-function type stop compiling.

The fix message says "The new type CompletionFunc could lead to a regression" and makes it a type
alias "in case projects using Cobra have created their own similar type", with a compatibility
test. It does not name the commit; `git log -S'type CompletionFunc func'` finds 6c3c116 as the
only commit that added the declaration. (The miner first paired the fix with 8cb30f9, which only
changed `[]string` to the `Completion` alias inside the same line; that is not where the bug
came from.)

Signals: message reference=False, blame agrees=True (by `git log -S`).

No third-party code was run; the evidence is the diffs and the fix's message and test.
