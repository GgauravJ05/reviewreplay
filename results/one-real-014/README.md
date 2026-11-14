# real-014 (gin-gonic/gin, Go): end-to-end check

This is the first run on a Go case, to show that export, review, extraction and grading work
outside Python. It is **1 run per reviewer, graded by one judge, with no code checks**, so it
isn't comparable to the 12-bug results. It only shows that the pipeline works.

`claude-sonnet-5-5`, Claude Code 2.1.319. Reviewers: baseline, and
[code-review-skill](https://github.com/awesome-skills/code-review-skill) at `4850184` invoked explicitly.

- **Both reviewers found the bug.**
- Precision: baseline 3 serious findings, all correct; skill 3, all correct. See [summary.md](summary.md).

Reproduce: `reviewreplay run --out results/one-real-014 --cases cases/real/real-014 --subjects baseline,code-review-skill-invoked --runs 1`,
then `extract`, `grade` and `report`.
