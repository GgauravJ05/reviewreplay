# 01 — Land the open PRs (#5 and #7)

**Goal:** multi-judge grading (PR #5) and `reviewreplay verify` (PR #7) are on `main`, and the
README and site show the code-checked numbers.

**Why:** the most trustworthy numbers (precision 72% without vs 82% with code-review-skill, paired
+10 pts [+1, +16]) exist only on the `feat/verify-unsure` branch. Everything in Phase 1 builds on them.

**Depends on:** nothing.

## Context

- PR #5 `feat/multi-judge` → `main`: **has merge conflicts** with `main` (checks pass).
- PR #7 `feat/verify-unsure` → `feat/multi-judge`: stacked on #5. Its commits also update
  `results/`, `docs/`, `site/` and the README with the code-checked numbers.
- Issues #4 (multi-judge) and #6 (verify) track them.
- `main` rules: 1 approval from CODEOWNERS, threads resolved, squash only, linear history,
  required checks `test (Python 3.10)` and `test (Python 3.13)`.

## Steps

1. In a worktree on `feat/multi-judge`, rebase onto `origin/main` (or use GitHub's "Update branch").
   Resolve conflicts keeping both sides' intent; run `python3.13 -m pytest` and
   `python3 -m reviewreplay check`. Push with `--force-with-lease` (only to this feature branch).
2. After #5 is squash-merged, retarget #7 to `main` (`gh pr edit 7 --base main`), rebase it onto
   `origin/main`, drop commits that #5's squash already contains, re-run the tests, push.
3. Before merging #7, check every number in README.md, `site/` and `results/*/README.md` against
   `results/` (the code-checked run). Fix any that disagree.
4. Merge #7; close #4 and #6 with a link to the merged PRs.
5. After Pages redeploys, open https://ggauravj05.github.io/reviewreplay/ and confirm the numbers.

## Done when

- [ ] #5 and #7 merged; #4 and #6 closed.
- [ ] README and site show 72% vs 82% (+10 pts [+1, +16]) and match `results/`.
- [ ] Tests pass on `main`.

## Your part

- Approve and merge the PRs on GitHub (branch protection needs your approval; you're the code owner).

## Don't

- Don't force-push `main` or bypass the ruleset.
- Don't regrade or rerun anything; this is integration only.
