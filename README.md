# ReviewBench

**Does your AI code reviewer actually help?** ReviewBench runs code reviewers — Claude with
no skill, Claude with a review skill, Claude Code's built-in `/code-review` — on code changes
whose bugs are already known, and scores what each one catches, what it gets wrong, and what it costs.

> Status: **planning** (private). See the design plan: [docs/PLAN.md](docs/PLAN.md).

## What it measures

- **Recall:** did the reviewer find the known bug?
- **False alarms:** does it flag problems in correct code, including code that only *looks* wrong?
- **Cost:** dollars, tokens, and time per review.

Every reviewer runs in an isolated setup, on the same cases, several times, and every
result is saved so any single grade can be audited.

## Origin and credit

ReviewBench started from an open question on
[awesome-skills/code-review-skill#32](https://github.com/awesome-skills/code-review-skill/issues/32):
does a code-review skill measurably improve reviews? Thanks to the
[code-review-skill](https://github.com/awesome-skills/code-review-skill) maintainers and
contributors (MIT) for the skill and the question. Their skill is fetched at a pinned commit at
run time; it is not copied into this repository.
