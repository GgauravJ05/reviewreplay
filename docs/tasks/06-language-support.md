# 06 — JS/TS and Go support (Roadmap 2.2)

**Goal:** one JavaScript/TypeScript case and one Go case go end to end: mine → check → run → grade.

**Why:** "every developer" means more than Python. The pipeline is language-agnostic in principle,
but the miner currently only treats `.py` files as code.

**Depends on:** nothing; brief 05 can reuse it.

## Context

- `reviewreplay/mine.py: _is_code(path)` accepts only `.py` and excludes tests by Python naming
  (`test_*.py`, `*_test.py`, `tests/`, `conftest.py`).
- `reviewreplay/init.py: _track(path)` already maps `ts`, `js`, `go`, `rs`, `java` to track names.
- `FIX_PATTERN` is English regression wording; it should work across languages.
- Real cases are exported with `git archive` (`cases.py: _export`), language-independent.
- The extractor/judge prompts and the reviewer prompt don't assume Python; check them.

## Steps

1. Make `_is_code` language-aware: code extensions (`.py .js .jsx .ts .tsx .mjs .cjs .go .rs .java`),
   and test conventions per language (`*.test.ts`, `*.spec.js`, `__tests__/`, `*_test.go`,
   `testdata/`, `src/test/`). Exclude generated/vendored dirs (`node_modules`, `dist`, `build`,
   `vendor`, `*.min.js`, `*.d.ts`). Unit-test the classifier.
2. Read `prompts/extractor.md`, `prompts/judge.md` and the subject prompts for Python-only wording; fix it.
3. Mine one MIT/Apache JS/TS repo (e.g. a mid-sized library such as date-fns, zod, axios, chalk)
   and one Go repo (e.g. cobra, gin, chi, testify). Make one checked case from each (brief 05 rules).
4. `reviewreplay check` passes for both; add them as `real-0NN` with `"track": "typescript"` / `"go"`.
5. Update `docs/ADDING_A_CASE.md` with any language-specific notes; README "Supported languages".

## Done when

- [ ] Classifier tests pass for all listed conventions.
- [ ] One JS/TS and one Go case are ready and pass `check`.
- [ ] Prompts contain no Python-only assumptions.

## Your part

- Run the one-case review/grade command the PR gives to prove end to end (uses your login).

## Don't

- Don't install dependencies or run builds in the mined repos.
