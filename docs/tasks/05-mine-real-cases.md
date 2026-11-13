# 05 — Mine more real-bug cases (Roadmap 2.1)

**Goal:** 8–10 new checked real cases (`real-013` onward), so the benchmark has 20+ real bugs, with
at least two more ML projects. JS/TS and Go cases come after brief 06.

**Why:** 12 real bugs give wide intervals; the skill's precision lead (+10 pts [+1, +16]) needs more
cases to hold or fail clearly.

**Depends on:** nothing for Python; brief 06 for other languages.

## Context

- Miner: `python3 -m reviewreplay mine <url> --since 2023-01-01 --limit 40 --json out.json`
  (default pattern: regression wording; `--pattern` overrides). Signals: `referenced` (fix message
  names the commit/PR), `blamed` (git blame of the lines the fix rewrites), `agree` (both match).
- Drafting: `reviewreplay.init.draft_case(repo, url, Candidate, out, model)` writes a draft
  `case.json`/`truth.json`/`NOTES.md` (spends model usage: your part, or ask first).
- Limits: introducing change ≤ 300 lines (`MAX_CHANGED_LINES`).
- Cases so far come from click, datasets, accelerate, werkzeug, attrs, rich, jsonschema, black, peft.
  Already mined with few usable results: httpx, flask, jinja, more-itertools, marshmallow,
  sentence-transformers, torchmetrics, optuna, scikit-learn, xarray (mostly deprecations), evaluate.
- Lessons: when message and blame disagree, the introducer is often wrong. Last batch: 14
  candidates → drafter rejected 4, 2 more dropped by hand (a moved block; a missing feature).

## Steps

1. Pick ~10 permissively licensed (MIT/BSD/Apache) Python and ML repos not listed above, e.g.
   pandas-adjacent libs, transformers ecosystem (trl, diffusers, tokenizers' Python side), pytorch
   lightning, polars' Python layer, fastapi, pydantic-core's Python side, httpcore, starlette, typer.
   Mine each with `--json`; run mining in the background (big repos are slow).
2. Shortlist candidates with `agree` or `referenced`, ≤ 300 changed lines, whose fix is a behaviour
   bug (skip CI, typing, docs, lint, deprecations, "missing feature").
3. For each, read the fix diff and the introducing diff yourself (`git -C ~/.cache/reviewreplay/repos/<repo>.git show <sha>`).
   Keep it only if the introducing commit added the faulty line(s).
4. Draft answer keys (your part if it needs the model), then edit `truth.json` by hand: anchor on
   the faulty line or its function, span the block, `occurrence` for repeated lines, `also` for
   every copy of the bug, `related_valid` for other real problems a reviewer may fairly report.
   Follow [../ADDING_A_CASE.md](../ADDING_A_CASE.md).
5. Name them `real-013`, `real-014`, …; set `"status": "ready"`, licence, `issue`, and a
   `NOTES.md` that says what the evidence is (fix commit, its tests, issue).
6. `python3 -m reviewreplay check` → 0 failing. One PR per 3–5 cases, branch `case/real-013-…`.

## Done when

- [ ] 8–10 new ready cases, each checked against its upstream fix, `check` passes.
- [ ] At least 2 new ML cases (`"track": "ml"`).
- [ ] PR lists each case: project, introducer → fix, one-line bug, why it was kept.

## Your part

- Run the drafting step if Claude can't use your login from its session.
- Review and merge the case PRs.

## Don't

- Don't run any code from the mined repos (no tests, no imports). Evidence is the fix commit.
- Don't keep a case just to reach a number; a wrong answer key poisons every result.
