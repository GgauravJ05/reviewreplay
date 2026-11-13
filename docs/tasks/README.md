# Task briefs

Each file here is a self-contained brief for one piece of upcoming work, written so you can hand it
to Claude (or a contributor) and get the intended result without re-explaining the project.

## How to use a brief with Claude

Open Claude Code in the repository and paste:

```text
Read CLAUDE.md and docs/tasks/<file>.md, then do the task. Work on a new branch, open a PR,
and stop before anything marked "Your part".
```

Claude does the code, docs and analysis. Anything that spends model usage (reviews, grading) or
needs your accounts is listed under **Your part**: you run those commands in a plain terminal tab.
When a brief is done, tick it in [../TODO.md](../TODO.md) and set its status below.

## Order and status

| # | Brief | Phase | Depends on | Status |
|---|---|---|---|---|
| 01 | [Land the open PRs](01-land-open-prs.md) | housekeeping | — | todo |
| 02 | [Correct published numbers](02-correct-published-numbers.md) | housekeeping | 01 | todo |
| 03 | [Approximate-line matching](03-approximate-line-matching.md) | 1 grading | 01 | todo |
| 04 | [Contested findings](04-contested-findings.md) | 1 grading | 01 | todo |
| 05 | [Mine more real cases](05-mine-real-cases.md) | 2 cases | — | todo |
| 06 | [JS/TS and Go support](06-language-support.md) | 2 cases | 05 (one case each) | todo |
| 07 | [Run and grade new cases](07-run-and-grade.md) | 2 cases | 05, 06 | todo |
| 08 | [More reviewers](08-more-reviewers.md) | 3 reviewers | 07 | todo |
| 09 | [Skill with the verify step](09-skill-verify-step.md) | 3 reviewers | 01 | todo |
| 10 | [GitHub Action](10-github-action.md) | 4 product | 01 | todo |
| 11 | [Five-minute quickstart](11-quickstart.md) | 4 product | — | todo |
| 12 | [Release and community](12-release.md) | 5 release | 07, 08 | todo |

New brief? Copy [_TEMPLATE.md](_TEMPLATE.md).
