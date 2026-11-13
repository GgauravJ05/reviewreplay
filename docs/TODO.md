# What's left to do

Start here when you come back to ReviewReplay. The *why* and the full plan are in
[ROADMAP.md](ROADMAP.md); this file is the short, current checklist. Tick items off as they land.

**Working with Claude:** each section has a task brief in [tasks/](tasks/README.md). Paste
`Read CLAUDE.md and docs/tasks/<brief>.md, then do the task.` Project rules for every session are in
[CLAUDE.md](../CLAUDE.md).

Last updated: 2026-11-13.

## Where things stand

- Public repo, site live at https://ggauravj05.github.io/reviewreplay/, PR rules on `main`.
- 12 real bugs from 9 projects (`cases/real/real-001` … `real-012`), 162 reviews in
  `results/m2-compare` and `results/m2-real-more`.
- Latest numbers (code-checked, on branch `feat/verify-unsure`, not on `main` yet): precision
  **72% without vs 82% with code-review-skill**, paired +10 pts [+1, +16]; serious false alarms 13 vs 10.
  `real-011` (black) and `real-012` (peft) were missed in every run.

## 1. Land the open PRs (do this first)

Brief: [01](tasks/01-land-open-prs.md)

- [ ] **PR #5** (multi-judge grading): it has merge conflicts with `main`. Update it from `main`,
      fix the conflicts, then review and squash-merge.
- [ ] **PR #7** (`reviewreplay verify`): stacked on #5. After #5 merges, change its base to `main`,
      update it, then merge it.
- [ ] Close issues #4 and #6 once their PRs are in.
- [ ] Check that the site and README show the 72% vs 82% numbers after the merge.

## 2. Fix the numbers already published

Brief: [02](tasks/02-correct-published-numbers.md)

- [ ] Post a short update on awesome-skills/code-review-skill#32 with the code-checked numbers
      (the comment there has the older ones).
- [ ] LinkedIn: short repost with the corrected numbers (the live post has the older ones).

## 3. Roadmap Phase 1 — finish trustworthy grading

Brief: [03](tasks/03-approximate-line-matching.md), [04](tasks/04-contested-findings.md)

- [x] 1.1 `reviewreplay compare` (PR #3)
- [ ] 1.2 Multi-judge grading — PR #5
- [ ] 1.3 `unsure` checker (`reviewreplay verify`) — PR #7
- [ ] 1.4 Approximate-line matching: a finding with the right file and bug, but lines slightly outside
      ±3 (real-002's "~212, ~265"), should reach the judge. Add tests.
- [ ] Look at the real-012 finding the judge graded both ways; list any finding that is still
      contested in a short "help label these" issue.

## 4. Roadmap Phase 2 — more real bugs (target: 20+ cases, 3+ languages)

Brief: [05](tasks/05-mine-real-cases.md), [06](tasks/06-language-support.md), [07](tasks/07-run-and-grade.md)

- [ ] Mine 8–10 more cases. Include **JS/TS and Go** from permissively licensed repos:
      `reviewreplay mine <repo-url> --since 2024-01-01 --limit 40 --json out.json`
- [ ] For each candidate: read the fix and the introducing commit; keep only behaviour bugs the
      introducing commit really added (skip typing, docs, lint, CI, refactor and "missing feature"
      fixes). Follow [ADDING_A_CASE.md](ADDING_A_CASE.md); `reviewreplay check` must pass.
- [ ] Make sure export, prompts and grading work on one JS/TS and one Go case end to end.
- [ ] Run, grade and verify the new cases (your Claude login, in a plain terminal tab):
      `reviewreplay run --out results/<name> --subjects baseline,code-review-skill-invoked --runs 3`,
      then `extract`, `grade`, `verify`, `report`.

Lessons from mining so far: the miner's introducer is often wrong when message and blame don't
agree. In the last batch the drafter rejected 4 of 14 candidates and 2 more were dropped by hand,
so read every one.

## 5. Roadmap Phase 3 — more reviewers

Brief: [08](tasks/08-more-reviewers.md), [09](tasks/09-skill-verify-step.md)

- [ ] Install and log in to Codex CLI and Gemini CLI, then run one case each with
      `reviewreplay/subjects/examples/codex.json` and `gemini.json`.
- [ ] Try Claude Code `/code-review` (`examples/claude-code-review.json`) on one case.
- [ ] code-review-skill with the verify step from your PR awesome-skills/code-review-skill#34
      (pinned branch): first on real-011 and real-012, then all real cases.
- [ ] Write up "Codex vs Gemini vs Claude Code on 20 real bugs", the launch-sized post
      (see [LAUNCH.md](LAUNCH.md) for Show HN).

## 6. Roadmap Phase 4 — product

Brief: [10](tasks/10-github-action.md), [11](tasks/11-quickstart.md)

- [ ] GitHub Action: re-score a reviewer when its prompt or skill file changes and comment the
      scorecard on the PR. Example workflow, docs and a demo repo.
- [ ] Five-minute quickstart: clear errors (no `claude`, not logged in, usage limit), a `--dry-run`
      cost estimate, and `init` → `run` → `report` tested on a fresh clone of a popular repo.

## 7. Release and community

Brief: [12](tasks/12-release.md)

- [ ] Social preview image: upload it in GitHub → Settings → General (there's no API for it).
- [ ] 5–8 good-first-issues (add a case from X, a reviewer adapter, a language).
- [ ] v0.2.0: changelog, tag, release notes.
- [ ] PyPI (`pip install reviewreplay`) only when you decide to.

## Rules to keep

- Credit [code-review-skill](https://github.com/awesome-skills/code-review-skill) in the README and
  every results table, and pin the skill commit.
- Commit as `GgauravJ05 <ggauravj5@gmail.com>`, with no co-author trailers.
- Changes go through branch → PR → squash-merge (main is protected). Result runs are committed
  separately from code.
- Never run third-party code from cases; reviewers stay read-only.
- Never commit or paste API keys or tokens. Runs use your own `claude` login in your own terminal.
- Tests: `python3.13 -m pytest`.
