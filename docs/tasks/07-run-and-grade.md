# 07 — Run, grade and verify the new cases

**Goal:** a results folder for the new real cases with the same reviewers and method as before, and
updated pooled numbers across all real bugs.

**Why:** new cases count only once they're reviewed and graded the same way as the first 12.

**Depends on:** 05 (and 06 for other languages), 01 (multi-judge + verify on `main`).

## Context

- Previous runs: `results/m2-compare` (first 4 real + planted), `results/m2-real-more` (real-005…012).
  Same model (`claude-sonnet-5-5`), subjects `baseline` and `code-review-skill-invoked` (skill pinned
  at `4850184`), 3 runs each. Check each run's `config.json` and reuse its settings.
- `reviewreplay run --cases <dir>` takes a folder of cases; to run only new ones, copy their case
  folders into a scratch folder with the same `real/` layout.
- `reviewreplay compare results/a results/b …` pools runs with paired intervals.

## Steps

1. Claude prepares: the scratch cases folder, and the exact commands with the run name
   (e.g. `results/m3-real-20`), including `--total-budget`.
2. **Your part:** run in a plain terminal tab (it resumes if stopped):
   ```bash
   python3 -m reviewreplay run --out results/m3-real-20 --cases <scratch> --subjects baseline,code-review-skill-invoked --runs 3 --workers 3 --total-budget 15
   python3 -m reviewreplay extract results/m3-real-20
   python3 -m reviewreplay grade results/m3-real-20 --cases <scratch>   # plus the multi-judge flags from PR #5
   python3 -m reviewreplay verify results/m3-real-20                    # from PR #7
   python3 -m reviewreplay report results/m3-real-20
   ```
3. Claude reads the outputs, checks misses and false alarms by hand against the answer keys
   (fix grader or answer-key errors in separate PRs), and writes `results/m3-real-20/README.md`.
4. Pool all real-bug runs with `compare`; update README "Results so far", `site/`, `docs/PLAN.md`
   (M2/M3 rows) and `docs/TODO.md`.

## Done when

- [ ] Results folder committed (separate PR from code), README with numbers and caveats.
- [ ] Pooled real-bug table updated everywhere, every number traced to `results/`.

## Don't

- Don't change the model, prompts or skill commit between runs being compared; if you must, say so
  and don't pool them.
