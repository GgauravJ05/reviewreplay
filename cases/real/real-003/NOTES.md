Real bug from pallets/click (BSD-3-Clause). PR #3126 (19fd4d6, 2026-04-30) switched the fish
completion protocol to newline-separated fields; released in 8.4.0 and broke fish completion.
Fixed in b7e5fd4 (2026-05-23: "Fix regression introduced in 8.4.0 by #3126"). Seeing the bug needs
two facts outside the changed lines: complete() joins items with "\n", and fish splits command
substitution output on newlines. Evidence: upstream fix and issues; not executed locally.
