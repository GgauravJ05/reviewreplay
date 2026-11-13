# 03 — Approximate-line matching (Roadmap 1.4)

**Goal:** a finding that names the right file and describes the bug, but cites lines a little
outside the ±3 tolerance or as approximations ("~212"), reaches the judge instead of being scored as a miss.

**Why:** in real-002 a reviewer described the bug correctly with lines "~212, ~265, ~345" and was
graded as missing it. The location gate should filter wrong places, not imprecise line numbers.

**Depends on:** 01 (multi-judge changes `grade.py`; build on it to avoid conflicts).

## Context

- `reviewreplay/grade.py`: `TOLERANCE = 3`, `overlaps(finding, file, start, end, tol)`,
  `candidates(finding, spots, *, no_line_same_file=False)`. Bugs are already matched with
  `no_line_same_file=True` (findings with no line can match any bug in the same file).
- The extractor (`reviewreplay/prompts/extractor.md`) turns reviews into findings with
  `file`, `line_start`, `line_end`; check how it records "~212" today (look in
  `results/m2-real-pilot/findings/` and `results/m2-compare/findings/` for real-002).
- The judge decides "same defect"; the gate only decides who reaches it.

## Steps

1. Find the real-002 findings that were scored as misses and record how their lines were extracted.
2. Design the rule. Suggested: for **bugs only** (not decoy traps), if no spot overlaps within ±3,
   a finding in the same file whose line is within a wider window (e.g. ±15, or inside the
   enclosing function of a spot) becomes a candidate; record `match: "approx"` on the grade.
   Optionally let the extractor mark approximate lines (`line_approx: true`).
3. Implement in `grade.py` with a named constant; keep decoy/precision behaviour unchanged.
4. Tests in `tests/test_scoring.py`: the real-002 "~212" case reaches the judge; a finding in the
   same file 200 lines away does not; decoys are unaffected.
5. Show how many existing findings would change status (dry analysis over committed `findings/`;
   no regrading). Note it in the PR.

## Done when

- [ ] Tests cover the real-002 case and the negative cases; `python3.13 -m pytest` passes.
- [ ] PR explains the rule and lists which committed findings it would affect.
- [ ] `docs/PLAN.md` grading section mentions the rule.

## Your part

- If the change affects committed results, run the regrade command the PR gives (it uses your login),
  then commit the results in a separate PR.

## Don't

- Don't widen the window for decoys or `known_ok` spots; that would hide false alarms.
- Don't change the judge prompt in the same PR.
