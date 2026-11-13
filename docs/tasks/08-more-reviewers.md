# 08 — More reviewers: Codex, Gemini, Claude Code /code-review (Roadmap 3.1)

**Goal:** Codex CLI, Gemini CLI and Claude Code's `/code-review` each produce graded reviews on the
real cases, compared against the Claude Code baseline.

**Why:** "which reviewer should we use?" is the question users have. This is the launch-sized result.

**Depends on:** 07 (20+ real cases) for the full run; one case is enough to test adapters.

## Context

- Adapters: `reviewreplay/subjects/examples/codex.json` (`codex exec --sandbox read-only {prompt}`),
  `gemini.json` (`gemini -p {prompt}`), `claude-code-review.json` (`invoke_command: /code-review`).
  Copy one into `reviewreplay/subjects/` (or `./subjects/`) to enable it.
- Command subjects run via `runner.run_command(subject, ws)`; their stdout is the review. They have
  no cost accounting; record time and note the plan/tier used.
- Reviewers must be read-only. Check each CLI's sandbox flag really prevents writes.

## Steps

1. Claude checks each adapter's flags against the current CLI docs (read-only mode, non-interactive,
   no auto-approve of edits) and fixes the JSON.
2. **Your part:** install and log in to `codex` and `gemini` (free tiers may be enough).
3. Smoke test: one real case, one run per adapter (`--subjects codex --runs 1`). Claude inspects the
   raw output, extraction and grade; fixes adapter or extractor issues.
4. Full run on all real cases, 3 runs each (your part: the commands Claude gives).
5. Claude writes `results/m4-reviewers/README.md`: recall, precision, false alarms, time (and cost
   where known), with paired intervals vs baseline via `compare`.

## Done when

- [ ] Each adapter verified read-only and committed under `reviewreplay/subjects/` with credits.
- [ ] Graded results for all three on all real cases; README table.
- [ ] README "Supported reviewers" updated.

## Don't

- Don't use any mode that lets a reviewer edit files or run arbitrary commands.
- Don't compare reviewers run on different case sets.
