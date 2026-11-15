# What's left to do

Start here when you come back to ReviewReplay. The *why* and the full plan are in
[ROADMAP.md](ROADMAP.md); this file is the short, current checklist. Tick items off as they land.

**Working with Claude:** each section has a task brief in [tasks/](tasks/README.md). Paste
`Read CLAUDE.md and docs/tasks/<brief>.md, then do the task.` Project rules for every session are in
[CLAUDE.md](../CLAUDE.md).

Last updated: 2026-11-14.

## Where things stand

- Public repo, site live at https://ggauravj05.github.io/reviewreplay/, PR rules on `main`.
- 20 real bugs from 15 projects in 3 languages (`cases/real/real-001` … `real-020`): 12 Python,
  2 JavaScript (axios), 6 Go (gin, testify, cobra ×2, urfave/cli, logrus). v0.2.0 released.
- JS/Go result (8 bugs, `results/m3-js-go`): precision 90% without vs 77% with the skill, paired
  −13 pts [−20, +3], so lower but not clearly.
- Headline (12 Python bugs, `results/m2-compare` + `results/m2-real-more`, code-checked): precision
  **72% without vs 82% with code-review-skill**, paired +10 pts [+1, +16]; serious false alarms 13 vs 10.
  `real-011` (black) and `real-012` (peft) were missed in every run.
- Tooling: `doctor`, `--dry-run`, approximate line matching, multi-language miner, 10 of 12 contested
  findings settled (`results/contested-real`), 2 open in issue #17.

## Priority order

Work top to bottom. **(you)** marks steps that need the author: posting, logins, model usage,
settings, releases.

### 1. Correct the published numbers **(you)**

Brief: [02](tasks/02-correct-published-numbers.md). Drafts are in the git-ignored `docs/drafts/`.

- [ ] Post `02-code-review-skill-32-update.md` as a follow-up on awesome-skills/code-review-skill#32.
- [ ] Post `02-linkedin-repost.md`.

### 2. Full runs for the JS and Go cases **(you)**

Brief: [07](tasks/07-run-and-grade.md). About $0.70.

- [x] real-013 to real-020: 3 runs, four judges, code checks (`results/m3-js-go`).

### 3. More real bugs (target: 20+ cases, 3+ languages)

Brief: [05](tasks/05-mine-real-cases.md), [06](tasks/06-language-support.md), [07](tasks/07-run-and-grade.md)

- [x] real-015 testify (#24), real-016 axios (#25).
- [x] real-017 to real-020 (#28–#31): cobra ×2, urfave/cli, logrus. 20 cases reached.
- [ ] A TypeScript case (issue #35) and a Rust or Java case (issue #36). Tried and skipped: zod
      (guards away from the introducing change), ky (leak older than any one change), date-fns
      (358 changed lines, over the 300-line limit), chalk and chi (nothing usable).
      Read every candidate's fix and introducer; keep only behaviour bugs the introducer added.
- [x] **(you)** Run, grade and verify the new cases on your login (all in `results/m3-js-go`).
- [ ] Judge fix: a finding that describes the answer-key bug but cites a line outside the gate
      must not be labelled a false alarm (seen on real-019). Then **(you)** regrade.

Lessons: the miner's introducer is often wrong when message and blame disagree, and many fixes
are hardening, refactors or older bugs. Expect 1 usable case per 5–10 candidates.

### 4. More reviewers — the launch story

Brief: [08](tasks/08-more-reviewers.md), [09](tasks/09-skill-verify-step.md)

- [ ] **(you)** Install and log in to Codex CLI and Gemini CLI; run one case each with
      `reviewreplay/subjects/examples/codex.json` and `gemini.json`.
- [ ] **(you)** Claude Code `/code-review` (`examples/claude-code-review.json`) on one case.
- [ ] code-review-skill with the verify step from awesome-skills/code-review-skill#34: first on
      real-011 and real-012, then all real cases.
- [ ] Write up "Codex vs Gemini vs Claude Code on 20 real bugs" (see [LAUNCH.md](LAUNCH.md)).

### 5. Release v0.2.0

Brief: [12](tasks/12-release.md)

- [x] CHANGELOG, version bump to 0.2.0, release notes draft (`docs/drafts/12-release-notes.md`).
- [x] 7 good-first-issues drafted in `docs/drafts/12-good-first-issues.md`.
- [x] Good-first-issues posted (#32–#38).
- [x] Social preview image: `docs/media/social-preview.png`.
- [ ] **(you)** Upload it in GitHub → Settings → General → Social preview.
- [x] v0.2.0 tagged and released. PyPI only when you decide to.

### 6. GitHub Action

Brief: [10](tasks/10-github-action.md)

- [x] `action.yml`, docs and an example workflow; a dry run that needs no secret (#23).
- [ ] **(you)** A demo repository with the API key secret, showing a real PR comment.

### Optional

- [ ] **(you)** Regrade `results/m2-compare` so committed grades use approximate line matching
      (can't change published precision; at most one review's catch).
- [ ] Timed end-to-end quickstart on a fresh clone of a popular repo (brief [11](tasks/11-quickstart.md)).

## Done

- 2026-11-13: multi-judge grading (#5), `verify` (#7), new site (#10, #11), task briefs (#9).
- 2026-11-14: approximate line matching (#13), contested findings (#14, issue #17), `doctor` and
  `--dry-run` (#15, #21), multi-language miner (#16), first JS and Go cases and runs (#18–#20),
  GitHub Action (#23), real-015 and real-016 (#24, #25), v0.2.0 prep.

## Rules to keep

- Credit [code-review-skill](https://github.com/awesome-skills/code-review-skill) in the README and
  every results table, and pin the skill commit.
- Commit as `GgauravJ05 <ggauravj5@gmail.com>`, with no co-author trailers.
- Changes go through branch → PR → squash-merge (main is protected). Result runs are committed
  separately from code.
- Never run third-party code from cases; reviewers stay read-only.
- Never commit or paste API keys or tokens. Runs use your own `claude` login in your own terminal.
- Tests: `python3.13 -m pytest`.
