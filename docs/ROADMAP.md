# v0.2 roadmap

> Current checklist of what's left: [TODO.md](TODO.md).

Where v0.1 stands (2026-11-08): 12 real bugs from 9 projects, 162 reviews, two reviewers (Claude
Code with and without code-review-skill). Results: [m2-compare](../results/m2-compare/README.md),
[m2-real-more](../results/m2-real-more/README.md).

The order follows one rule: **make the numbers trustworthy before making more of them.** Each phase
ends in something publishable.

How work lands: each item is an issue, a branch and a squash-merged PR with tests (the repo's PR
rules apply to us too). Result runs are committed separately from code.

Who does what: code, mining and analysis are done here. Anything that spends model usage (reviews,
grading) runs on your Claude login in a plain terminal tab, one command per step, given in the PR.

---

## Phase 1: trustworthy grading (first, about a week)

Problem: the judge is checked only against another model, it graded one real-012 finding both ways,
and 28 `unsure` claims count against precision by default. There's no time for hand labels, so we
replace them with checks that need no person.

| # | Item | What it does | Done when |
|---|---|---|---|
| 1.1 | `reviewreplay compare` | Combines several run folders by subject and case kind, with paired bootstrap intervals. Replaces the one-off script behind the 12-bug table. | Reproduces the 12-bug table exactly from `m2-compare` + `m2-real-more`; unit-tested |
| 1.2 | Multi-judge grading | `grade --judges 3` grades each finding three times, and `--second-judge <model>` adds a different model. Each finding records its votes; a split vote is **contested**. `report` shows contested counts and headline numbers without them; `agreement` gives judge-vs-judge κ. | A rerun on the 12 real bugs states which verdicts are stable, and real-012's flip-flop shows up as contested |
| 1.3 | `unsure` checker | `reviewreplay verify` takes each `unsure` claim and has a read-only reviewer check it against the source of the library at the version the case pins (the source archive is read, never executed). The claim becomes true, false or still unsure, with a quote as evidence. | The 28 unsure claims are settled or left explicitly open, each with its quoted evidence |
| 1.4 | Approximate-line matching | A finding that names the right file and describes the bug, but cites lines a little outside ±3, can reach the judge (as findings without a line can today). | Tests cover the real-002 "~212, ~265, ~345" case |

**Your step:** one command that re-grades the 72 real-bug reviews with three votes plus a second
judge, then runs `verify`. It takes roughly two to three 5-hour usage windows on Claude Pro, and it
resumes if it stops.

**Publish:** updated 12-bug numbers, labelled "checked across models, not by people", in the
README, the site, and a short LinkedIn repost.

## Phase 2: more real bugs (about a week)

| # | Item | Done when |
|---|---|---|
| 2.1 | Mine 8–10 more real cases, including JS/TS and Go, from permissively licensed repositories (`reviewreplay mine`, answer keys checked against the upstream fix) | 20+ real cases, at least 3 languages |
| 2.2 | Language support check: case export, prompts and the grader on non-Python repos | One JS/TS and one Go case run end to end |

**Your step:** review and grade the new cases (one command).

**Publish:** a 20-bug table. If the skill's precision lead holds with an interval above zero, that's
the result; if it doesn't, that's the result too.

## Phase 3: more reviewers (about a week)

| # | Item | Done when |
|---|---|---|
| 3.1 | Test the Codex CLI, Gemini CLI and Claude Code `/code-review` subject files on one case each | Each produces a graded review |
| 3.2 | code-review-skill with the verify step from awesome-skills/code-review-skill#34 (pinned branch) | Run on the two always-missed bugs first, then all real cases |

**Your step:** install and log in to Codex CLI and Gemini CLI (their free tiers may be enough), then
one run command.

**Publish:** "Codex vs Gemini vs Claude Code on 20 real bugs". This is the launch-sized post, and
the moment for Show HN (docs/LAUNCH.md).

## Phase 4: product (about a week)

| # | Item | Done when |
|---|---|---|
| 4.1 | GitHub Action: re-scores a reviewer when its prompt or skill file changes and comments the scorecard on the PR | Example workflow and docs; works on a demo repo |
| 4.2 | Five-minute quickstart: clearer errors (no `claude`, not logged in, usage limit), a `--dry-run` cost estimate | `init` → `run` → `report` works on a fresh clone of a popular repo |

## Phase 5: community and release (ongoing)

| # | Item | Done when |
|---|---|---|
| 5.1 | 5–8 good-first-issues (add a case from X, add a reviewer adapter, add a language) | Issues labelled and scoped |
| 5.2 | v0.2.0 release: changelog, tag and release notes | Release published |
| 5.3 | PyPI (`pip install reviewreplay`) | **Only with your go-ahead** |

---

## Not planned

- Hand-labelling by the maintainer (no time). If a handful of findings stay contested after
  Phase 1, they go into a short yes/no sheet with evidence filled in, or a "help label these"
  issue for contributors.
- Running third-party code. Reviewers stay read-only; the `unsure` checker reads library source and
  never executes it.
