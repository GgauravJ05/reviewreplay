# ReviewReplay

**Would your AI code reviewer have caught the bugs you already shipped?**

ReviewReplay benchmarks AI code reviewers — Claude Code, Codex, Gemini CLI, your own review
prompts and skills — on **the real bugs from your own repository's history**. It finds commits
that introduced a bug (using the later fix), replays each one as an uncommitted change in the full
project, asks every reviewer to review it, and scores what each one catches, what it gets wrong,
and what it costs.

[![ReviewReplay replays a real click bug to Claude Code and grades every finding: same bug, two other real problems, two false alarms](docs/media/reviewreplay-demo.gif)](docs/media/reviewreplay-launch.mp4)

<sub>▶ [Watch the 21-second launch video, with sound](docs/media/reviewreplay-launch.mp4): a real bug from
pallets/click, rewound to the commit that caused it and replayed to Claude Code.</sub>

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![No dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)
![Status: alpha](https://img.shields.io/badge/status-alpha-orange)

> **v0.1, built in public.** The method and the tool work; the results are early (4 graded real
> bugs so far, 8 more being graded, judge agreement checked against a second model, not yet a
> person). Read the numbers as a direction. Progress, new cases and corrections land here as they
> happen, and [contributions are welcome](CONTRIBUTING.md).

```bash
pip install git+https://github.com/GgauravJ05/reviewreplay
cd your-repo
reviewreplay init                     # mine your fixed bugs into draft test cases
reviewreplay run --cases .reviewreplay/cases --out .reviewreplay/results --include-drafts
reviewreplay report .reviewreplay/results
```

## Why

Teams are adopting AI code review on faith. Public benchmarks test reviewers on shared,
public pull requests: useful, but not *your* code, your conventions or your kinds of bugs, and
public code may already be in the model's training data. ReviewReplay answers the question
each team actually has:

- **Which reviewer should we use?** Compare tools on bugs from your codebase, side by side.
- **Did our new review prompt or skill help?** Measure before and after, with confidence intervals.
- **What does it cost?** Dollars, time and noise (false alarms) per review.

## How it works

```mermaid
flowchart LR
  A[Your git history] -->|fix commits| B[Mine: fix → bug-introducing commit<br/>message reference + git blame]
  B --> C[Draft answer key<br/>LLM reads fix + bug diffs]
  C --> D[You confirm each case]
  D --> E[Replay the buggy change<br/>in a clean copy of the repo]
  E --> F[Every reviewer reviews it<br/>read-only, isolated, 3 runs]
  F --> G[Extract findings → grade<br/>location gate + LLM judge]
  G --> H[Scorecard: recall, precision,<br/>false alarms, cost, 95% CIs]
```

- **Mining** pairs each fix commit with the commit that introduced the bug, using two signals:
  the commit or PR the fix message names, and `git blame` of the lines the fix rewrites (the SZZ
  method). Both agreeing is the strongest evidence.
- **Replay** exports the project at the parent commit with no git history (so the later fix can't
  leak) and applies the buggy change as uncommitted edits — what a reviewer sees in a real PR.
- **Reviewers run read-only.** Claude Code runs with an allow-list (read files, `git diff/log/show`).
  Any other reviewer is a command that prints a review (see `subjects/examples/`).
- **Grading** turns each free-text review into findings, matches them to the known bug by
  location, and an LLM judge decides whether each finding is the same bug, another real problem,
  or a false alarm. Grader agreement is checked against independent labels (Cohen's κ).

## What it measures

| Metric | Meaning |
|---|---|
| Recall | Share of known bugs the reviewer found |
| Precision | Share of serious findings that are real problems |
| Clean pass | Correct changes the reviewer left alone |
| Decoy trap | Correct-but-suspicious code wrongly flagged as a bug |
| Cost / time | Per review, from the tool's own accounting |

Each result is a mean over cases with a 95% bootstrap interval; comparisons to a baseline are
paired by case. Every review, extraction and grade is saved, so any number can be audited.

## Results so far

Early pilots with Claude Code (`claude-sonnet-5-5`) as the reviewer:

| Pilot | Cases | Recall | Precision | Finding |
|---|---|---|---|---|
| Planted bugs | 10 | 100% | 100% | Small planted bugs are too easy for current models |
| Harder cross-file bugs | 5 | 100% | 100% | Still at the ceiling |
| Real bugs, full repositories | 3 | ~100% | 56% | **The difference is precision**: many claims can't be verified |

**Baseline vs a review skill** (19 cases, 114 reviews): on 4 real bugs in full repositories, Claude
Code with [code-review-skill](https://github.com/awesome-skills/code-review-skill) found the bug
12/12 times vs 11/12, with 81% vs 64% precision, **zero serious false alarms vs 3**, and half the
minor noise — at 1.6× the cost. Small sample; a direction, not a verdict
([details](results/m2-compare/README.md)).

So "does it find the bug?" is no longer the interesting question for strong models. **How much
of what it says is right, and at what cost** is. Details: [results/](results/).

## Supported reviewers

| Reviewer | How |
|---|---|
| Claude Code (any model) | built in |
| Claude Code + a skill (e.g. a review skill), natural or invoked | `subjects/*.json` with `skill` |
| Claude Code `/code-review` | `subjects/examples/claude-code-review.json` |
| Codex CLI, Gemini CLI, any CLI | `subjects/examples/*.json` (`"command": [...]`) |

## Using the built-in benchmark

The repository also ships a curated benchmark (planted, clean, decoy and real cases in Python and
ML code) for comparing reviewers on shared ground:

```bash
reviewreplay check                    # validate cases
reviewreplay run --out results/mine --subjects baseline --runs 3
reviewreplay extract results/mine && reviewreplay grade results/mine && reviewreplay report results/mine
```

Adding cases: [docs/ADDING_A_CASE.md](docs/ADDING_A_CASE.md). Design and methodology:
[docs/PLAN.md](docs/PLAN.md).

## Roadmap

- [x] Isolated, read-only reviewer runs; resumable; per-run and total budgets
- [x] Grading with location gate + LLM judge; κ check; bootstrap CIs
- [x] Real bugs in full repositories; mining from fix commits
- [x] `init`: build a benchmark from any repository's own history
- [ ] GitHub Action: re-score your reviewer setup when its prompt or skill changes
- [ ] Verify claims about third-party libraries (score "unsure" findings)
- [ ] Public leaderboard on the shared benchmark

## Author

Created and maintained by **Gaurav Jadhav** ([@GgauravJ05](https://github.com/GgauravJ05)).
If you use ReviewReplay in research or a write-up, please cite it ([CITATION.cff](CITATION.cff)).

## Acknowledgements

The project began from an open question on
[awesome-skills/code-review-skill#32](https://github.com/awesome-skills/code-review-skill/issues/32):
does a code-review skill measurably improve reviews? Thanks to the
[code-review-skill](https://github.com/awesome-skills/code-review-skill) maintainers (MIT), whose
skill is one of the reviewers tested here; it is fetched at a pinned commit at run time, not
copied. Real cases reference public commits from their original repositories (e.g. pallets/click,
huggingface/datasets) under those projects' licenses; no third-party code is stored here.

## License

[MIT](LICENSE) © 2026 Gaurav Jadhav
