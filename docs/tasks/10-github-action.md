# 10 — GitHub Action: re-score a reviewer on change (Roadmap 4.1)

**Goal:** a reusable GitHub Action that, when a team's review prompt or skill file changes in a PR,
re-runs ReviewReplay on their cases and comments the scorecard (vs the base branch) on the PR.

**Why:** this turns a benchmark into a tool every team can keep in CI: "did our new review prompt
help or hurt?" on their own past bugs.

**Depends on:** 01. Benefits from 11 (clear errors, `--dry-run`).

## Context

- CLI flow: `reviewreplay init` (draft cases once, committed under `.reviewreplay/cases`),
  `run`, `extract`, `grade`, `report`, `compare`.
- Reviews need a model credential in CI: the action must read it from a repository secret
  (e.g. `ANTHROPIC_API_KEY`) that the user sets. ReviewReplay never stores it.
- Costs money per run: needs a budget input (`--total-budget`) and a cheap default (1 run, few cases).

## Steps

1. Design inputs: `cases` (path), `subjects` (path to subject files), `runs`, `budget`, `model`,
   `compare-to` (base branch results or a baseline subject). Outputs: scorecard markdown, JSON path.
2. Implement as a composite action in `action.yml` at the repo root (setup Python, `pip install`
   from the tag, install `claude` CLI, run, post comment with `gh pr comment` or
   `actions/github-script`). Pin every third-party action to a commit SHA.
3. Security: run only on `pull_request` from the same repo by default (no secrets to forks),
   `permissions:` minimal (`contents: read`, `pull-requests: write`), reviewers read-only.
4. Example workflow in `docs/github-action.md` and a demo repository (your part: create it) that
   shows a real PR comment.
5. Tests for the scorecard formatting; a dry-run mode that needs no secret.

## Done when

- [ ] `action.yml`, docs, example workflow; the dry run works without secrets.
- [ ] A demo PR shows a scorecard comment.
- [ ] README "Use it in CI" section.

## Your part

- Create the demo repo and add the secret there yourself. Claude never sees or sets secret values.

## Don't

- Don't run on `pull_request_target` with checkout of PR code.
- Don't print the secret or pass it on the command line.
