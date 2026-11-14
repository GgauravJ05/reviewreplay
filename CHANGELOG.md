# Changelog

All notable changes to ReviewReplay. Numbers quoted here come from the committed runs in
[`results/`](results/).

## 0.2.0 (unreleased)

### Added

- **Multi-judge grading** (#5): several judges vote on each finding, split votes are kept as
  *contested*, and the report shows judge agreement (`grade --judges 3 --second-judge <model>`).
- **`reviewreplay verify`** (#7): checks findings the judges marked `unsure` against the code,
  read-only, and records the verdict next to the grade.
- **`reviewreplay compare`** (#3): pools several runs into one table, paired against a baseline,
  with bootstrap intervals; `--drop-contested` and `--ignore-verify` for sensitivity checks.
- **Approximate line matching** (#13): a bug finding within ±15 lines of the answer (outside the
  exact ±3 gate) reaches the judge as `match: approx`, so a slightly wrong line number no longer
  hides a real catch.
- **`reviewreplay doctor` and `--dry-run`** (#15, #21): checks the setup, and estimates the number
  of reviews, cost and time for `run` and `init` before spending anything.
- **Multi-language miner** (#16): `mine` and `init` find fixes in JavaScript, TypeScript, Go, Rust
  and Java, not only Python, with each language's test-file conventions.
- **GitHub Action** (#23): `uses: GgauravJ05/reviewreplay@v0.2.0` scores reviewers on your cases
  in CI and posts the scorecard as one PR comment; `dry-run: true` needs no secret.
  `reviewreplay comment` builds that comment.

### Cases

- **real-013** axios (first JavaScript case, #18), **real-014** gin (first Go case, #19),
  **real-015** testify (Go, #24), **real-016** axios (JavaScript, #25). 16 real bugs from 12
  projects in 3 languages.

### Results

- `results/contested-real` (#14): 10 of the 12 findings the judges split on are settled by hand;
  2 stay open in issue #17.
- `results/one-real-013`, `results/one-real-014` (#20): first JavaScript and Go smoke runs
  (1 run each, not yet in the headline).

### Fixed

- Short dry-run estimates show seconds instead of "0 min" (#21).
- The results scorecard fits on phones (#11).

### Docs

- Roadmap (#1), `CLAUDE.md`, `docs/TODO.md` and task briefs (#9, #12, #22), GitHub Action guide
  (`docs/github-action.md`), this changelog.

## 0.1.0 (2026-11-07)

First public release.

- SZZ miner: finds fix commits, then the commit that introduced each bug (message reference and
  `git blame`).
- Replays each change in a clean copy of the full project and asks each reviewer to review it.
- Grading: a ±3-line location gate, then an LLM judge; recall, precision, false alarms and cost
  per reviewer, with 95% bootstrap intervals.
- 12 real Python bugs (`real-001` … `real-012`), plus planted, clean and decoy cases.
- Tests [code-review-skill](https://github.com/awesome-skills/code-review-skill) (MIT, pinned at
  `4850184`) against a plain Claude Code baseline.
