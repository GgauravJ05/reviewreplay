# real-013 (axios/axios, JavaScript): end-to-end check

This is the first run on a JavaScript case, to show that export, review, extraction and grading work
outside Python. It is **1 run per reviewer, graded by one judge, with no code checks**, so it
isn't comparable to the 12-bug results. It only shows that the pipeline works.

`claude-sonnet-5-5`, Claude Code 2.1.319. Reviewers: baseline, and
[code-review-skill](https://github.com/awesome-skills/code-review-skill) at `4850184` invoked explicitly.

- **Both reviewers found the bug.**
- Precision: baseline 3 serious findings, all correct (100%); skill 3 serious, 2 correct and one false alarm (67%). See [summary.md](summary.md).

Reproduce: `reviewreplay run --out results/one-real-013 --cases cases/real/real-013 --subjects baseline,code-review-skill-invoked --runs 1`,
then `extract`, `grade` and `report`.
