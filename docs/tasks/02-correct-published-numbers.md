# 02 — Correct the numbers already published

**Goal:** every public place that quotes ReviewReplay results shows the current, code-checked numbers.

**Why:** the comment on awesome-skills/code-review-skill#32 and the LinkedIn post carry older
numbers (single-judge and four-judge). Keeping published claims honest is the project's core promise.

**Depends on:** 01 (numbers on `main`).

## Context

- Current headline (from `results/` after 01): on 12 real bugs, precision **72% without vs 82% with**
  code-review-skill, paired +10 pts [+1, +16] (dropping contested findings: +9 [0, +17]); serious
  false alarms 13 vs 10; `real-011` (black) and `real-012` (peft) missed in every run; skill costs ~1.5×.
- #32 comment: issuecomment-6711864115 on awesome-skills/code-review-skill.
- Drafts live in the git-ignored `docs/drafts/`.

## Steps

1. Read the merged `results/*/README.md` and write down the exact headline numbers with their source files.
2. Draft a short follow-up comment for #32: what changed in the method (multiple judges, code
   checks of `unsure` claims), the new numbers, a link to the results README. Plain, no hype.
3. Draft a short LinkedIn repost with the same numbers and a link to the site.
4. Save both drafts in `docs/drafts/` (not committed) and show them to the author.

## Done when

- [ ] Both drafts written, every number traced to a file under `results/`.
- [ ] Author has posted them (or decided not to).

## Your part

- Post the #32 comment and the LinkedIn update yourself. Claude must not post publicly for you.

## Don't

- Don't round numbers into stronger claims ("the skill is better"): the interval includes values near 0.
- Don't edit the original #32 comment silently; post a follow-up.
