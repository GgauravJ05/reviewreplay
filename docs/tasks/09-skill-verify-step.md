# 09 — code-review-skill with the verify step (Roadmap 3.2)

**Goal:** measure whether the "verify findings before reporting" step from your PR
awesome-skills/code-review-skill#34 improves precision and catches the two always-missed bugs.

**Why:** the tested skill commit (`4850184`) predates #34. Both reviewers missed `real-011` (black
f-string tokenizer) and `real-012` (peft Conv LoRA dilation) in every run; a verify step is the kind
of change that could help, and the result is useful evidence for #34 itself.

**Depends on:** 01. Works best after 07 (more cases).

## Context

- #34 is open: head `GgauravJ05:feat/verify-findings-before-reporting`, commit `fc63a8eb32de`
  (re-check the latest head before running).
- Skill subjects pin a repo and commit, e.g. `reviewreplay/subjects/code-review-skill-invoked.json`:
  `{"skill": {"name": "code-review-skill", "repo": "...", "commit": "4850184"}, "invoke": true}`.
  Skills are cloned at run time into `~/.cache/reviewreplay/skills/`; check `subjects.py` for how
  the commit is fetched (a fork commit needs the fork URL).

## Steps

1. Add `reviewreplay/subjects/code-review-skill-verify.json` pinned to the #34 head commit on
   `https://github.com/GgauravJ05/code-review-skill` (your fork), invoked like the existing one.
   Credit both the skill and the PR.
2. Smoke test on `real-011` and `real-012`, 3 runs (your part: the command Claude gives).
3. Then all real cases, 3 runs; compare against `code-review-skill-invoked` and `baseline` with
   `reviewreplay compare` (same cases, model, prompts).
4. Write `results/m4-skill-verify/README.md`; if the result is informative, draft a comment for #34
   with the numbers (your part: post it).

## Done when

- [ ] Subject file committed with pinned commit and credit.
- [ ] Results for the two hard cases and all real cases, paired vs the current skill.
- [ ] Draft comment for #34 (if useful).

## Don't

- Don't vendor the skill's files into this repo.
- Don't present results from an unmerged PR as the skill's official behaviour; name the commit.
