# real-019 (urfave-cli-bf96dc85)

Source: [urfave/cli](https://github.com/urfave/cli), MIT licence, Copyright (c) 2023 urfave/cli maintainers.

Introduced in `57bfb1c91f9087a60c6ffa8eef3a7d54e7983c0b`: fix: parallel running - remove globals used for splicing slices and maps (#2215)
Fixed in `bf96dc85cbd766b890bf23e22bec76e496923531`: fix: inherit SliceFlagSeparator in subcommands

Why this is a bug:
Before this commit, `setupDefaults` copied a command's `SliceFlagSeparator` into a package global,
so a separator set on the root applied to every subcommand. The commit removed the globals (to
make parallel runs safe) and passed each command's own field to its flags. A subcommand that
doesn't set the field now uses the default ",", so the root's separator stops applying, and
slice values are split on the wrong character without any error.

The fix message says "Since 57bfb1c9 (#2215, v3.6.0) a command splits slice flag values with
only its own SliceFlagSeparator, so a separator set on the root no longer reached subcommands",
and adds a lookup of the nearest ancestor that sets one, with an inheritance test.

How it was picked: `reviewreplay mine` (multi-language miner). The fix message names the commit
and blame agrees. Signals: message reference=True, blame agrees=True.

No third-party code was run; the evidence is the two diffs and the fix's message.
