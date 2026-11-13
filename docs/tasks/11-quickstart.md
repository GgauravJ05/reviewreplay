# 11 — Five-minute quickstart (Roadmap 4.2)

**Goal:** a new user goes from `pip install` to a scorecard on their own repo in about five
minutes, with clear errors and a cost estimate before spending anything.

**Why:** first-run friction decides whether people use a tool after starring it.

**Depends on:** nothing.

## Context

- Entry points: `reviewreplay init`, `run`, `report` (`reviewreplay/cli.py`).
- `claude.py` already detects fatal account errors (`FATAL_MARKERS`: usage limit, auth failures)
  and raises `AccountError`.
- README quickstart uses `.reviewreplay/cases` and `.reviewreplay/results`.

## Steps

1. Preflight check (`reviewreplay doctor`, also run at the start of `init`/`run`): git present,
   `claude` on PATH, logged in (a tiny no-cost call or `claude --version` + auth status), Python
   version, cache dir writable. Each failure prints one line with the fix.
2. `--dry-run` for `init` and `run`: number of candidates/cases × subjects × runs, estimated cost
   from previous medians (~$0.04–0.10 per review), and estimated time. Spends nothing.
3. Friendly messages for: no candidates found (suggest `--since`/`--pattern`), usage limit hit
   (resume later; runs are resumable), case export failures.
4. Test the flow on a fresh clone of a popular permissively licensed repo end to end, timing each
   step; fix anything confusing. Update README quickstart with the real timings.
5. Tests for `doctor` and `--dry-run` (mock subprocess).

## Done when

- [ ] `reviewreplay doctor` and `--dry-run` exist with tests.
- [ ] README quickstart matches a real timed run.

## Your part

- Run the final end-to-end on your machine (uses your login) and confirm the timings.

## Don't

- Don't add runtime dependencies; stay standard-library only.
