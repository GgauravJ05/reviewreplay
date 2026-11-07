# M2 difficulty pilot — findings

Question: after M1 hit the ceiling, can hand-written "harder" cases separate reviewers?
Run: 5 new cases × baseline only × 3 runs = **15 reviews**, `claude-sonnet-5-5`, Claude Code 2.1.319,
2026-11-07. Usage ≈ $0.77 for reviews plus extraction and two grading passes.

## The new cases

Each bug needs a second, **unchanged** file to see, and each was verified by running the code.

| Case | Change | Bug | Where the evidence is |
|---|---|---|---|
| py-006 | `@lru_cache` on `load_rules` | cached list mutated by `rules += promos`; discounts stack and persist | `engine.py` (unchanged) |
| py-007 | bill per started hour | aware datetimes with the same `ZoneInfo` subtract by wall clock; DST sessions billed wrong | `sessions.py` (unchanged) |
| py-008 | `read_rows` becomes a generator | `summarize` iterates twice (`any()` then a loop); first high-severity event vanishes | `report.py` (unchanged) |
| ml-006 | lag features via `shift()` | frame is ordered date-then-store, so lags cross stores | `data.py` (unchanged) |
| py-009 | logout + purge (decoy) | none: backwards index deletion, `<=` expiry, swallowed `KeyError` are all correct | `models.py` docstring |

## Result

| | Recall | Precision | Decoy trap |
|---|---|---|---|
| baseline | **100%** (12/12) | 100% | 0% (0/3) |

Every review found the planted bug, each time for the right reason (checked by reading all 12 hits).
No review called the decoy's patterns wrong.

**Conclusion: small hand-written cases can't create difficulty for this model, even with cross-file
bugs.** With ~100–200 lines per case, the reviewer reads the whole project and connects the files.
Difficulty has to come from **scale** (projects too large to read in full, so the reviewer must choose
where to look) and from **real bugs** that real reviewers missed, not from cleverness at small scale.

## Grader fixes from this pilot

1. **Decoy trap only counts wrong claims.** The first grading showed a 33% trap rate: one review
   reported missing locking (a real, listed issue) near a decoy spot. A trap now requires a serious
   finding graded `false_alarm`/`unsure` at a known-ok spot. A test covers this.
2. **ml-006 answer key**: added "row shifts assume no missing days" to `related_valid`; two reviews
   raised it and it is a real risk (`load_sales` doesn't check for gaps).

After both: precision 100%, trap 0%. `summary-v1` was not kept; the first-pass numbers are in
`results/m2-hard-pilot.log`.

## What this changes in the plan

- Stop writing small planted cases for M2; the 10 + 5 existing ones stay as a sanity tier (every
  reviewer should pass them).
- Next: **real bugs from real repositories** (planned for M3, now pulled forward), reviewed in the
  **full repository at the parent commit**, so scale and realism both apply.
