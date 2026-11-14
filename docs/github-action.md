# Use ReviewReplay in CI

The ReviewReplay action re-scores your AI code reviewer whenever its subject file (its skill
version or command) or your cases change. It posts the scorecard on the pull request, so you can see whether the change
helped on bugs your team already fixed.

## 1. Make your cases once

On your machine, in your repository:

```bash
pip install git+https://github.com/GgauravJ05/reviewreplay
reviewreplay init --dry-run      # which fixed bugs it would use; spends nothing
reviewreplay init                # drafts cases under .reviewreplay/cases
```

Confirm each draft (see its `NOTES.md`), then commit `.reviewreplay/cases`.

## 2. Describe your reviewer

Put a subject file in `subjects/`. A Claude Code skill, pinned to a commit, for example
`subjects/our-reviewer.json`:

```json
{
  "name": "our-reviewer",
  "skill": {"name": "our-review-skill",
            "repo": "https://github.com/acme/review-skills",
            "commit": "4850184"},
  "invoke": true,
  "credit": "acme/review-skills"
}
```

Or any command-line reviewer, which runs read-only in a throwaway copy:

```json
{
  "name": "codex",
  "command": ["codex", "exec", "--sandbox", "read-only", "{prompt}"],
  "credit": "OpenAI Codex CLI"
}
```

A command reviewer needs its own CLI and login on the runner. Install it in a step before the action.

`baseline` (plain Claude Code) is built in. Run it next to yours to get a paired difference. When
you change the skill, bump `commit` in the subject file. That change triggers the workflow and
scores the new version. More examples are in
[`reviewreplay/subjects`](../reviewreplay/subjects).

## 3. Add the workflow

`.github/workflows/reviewreplay.yml`:

```yaml
name: ReviewReplay

on:
  pull_request:
    paths:
      - "subjects/**"
      - ".reviewreplay/cases/**"

permissions:
  contents: read
  pull-requests: write

jobs:
  scorecard:
    # Secrets are not given to pull requests from forks; skip them instead of failing.
    if: github.event.pull_request.head.repo.full_name == github.repository
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: GgauravJ05/reviewreplay@main   # pin a release tag or commit SHA
        with:
          subjects: baseline,our-reviewer
          runs: "1"
          budget: "2"
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

Add the `ANTHROPIC_API_KEY` secret under Settings → Secrets and variables → Actions. You can use
a `claude setup-token` token instead: pass it as `claude-code-oauth-token`.

## Inputs

| Input | Default | What it does |
|---|---|---|
| `cases` | `.reviewreplay/cases` | Folder of cases |
| `subjects` | `baseline` | Comma-separated reviewers to run |
| `runs` | `1` | Runs per case and reviewer; 3 gives steadier numbers |
| `budget` | `2` | Stop starting new reviews after this estimated spend (US$) |
| `model` | `claude-sonnet-5-5` | Model for reviews, extraction and grading |
| `include-drafts` | `false` | Also run cases still marked draft |
| `dry-run` | `false` | Only print reviews, cost and time; needs no secret |
| `comment` | `true` | Post or update the scorecard comment |
| `anthropic-api-key` | | API key, from a secret |
| `claude-code-oauth-token` | | Or a `claude setup-token` token, from a secret |
| `claude-code-version` | `2.1.325` | Claude Code CLI version to install |
| `results` | `.reviewreplay/ci-results` | Where results are written |

Outputs: `scorecard` (the comment's markdown file) and `results` (the results folder). The
scorecard also goes to the job summary. To keep every review and grade, upload `results` with
`actions/upload-artifact`.

## Cost

A run costs about $0.06 per review in CI (the median of 186 committed reviews), plus a smaller
amount for extraction and grading. Ten cases × two reviewers × one run is 20 reviews, about $1.20.
Set `dry-run: "true"` to see the estimate for your cases first.

## Safety

- The workflow runs on `pull_request` only, never `pull_request_target`, so code from forks never
  sees your secret. The `if:` above skips fork pull requests.
- Permissions are read-only, except for writing the pull-request comment.
- Reviewers run read-only: they can read and search the code and run `git diff/log/show/status`,
  nothing else.
- The secret reaches `claude` through an environment variable only. It is never printed and never
  on a command line. ReviewReplay drops every other `ANTHROPIC_*` variable before a run.
