# Contested real-bug findings

The four-judge regrade of the 12 real bugs ([m2-real-more](../m2-real-more/README.md#four-judge-re-grade))
left **12 of 195 findings contested**: no label had a strict majority. Each one is settled here with
quoted code, or left open. Judge votes in `grades/` are unchanged; the verdicts are in
[`verdicts.json`](verdicts.json).

| # | Case | Reviewer, review | Finding | Votes | Verdict | How |
|---|---|---|---|---|---|---|
| 1 | real-004 | baseline, run2 | fp32 upcast before the move to meta spikes CPU RAM | unsure ×2, false alarm ×2 | real problem | code check |
| 2 | real-004 | baseline, run2 | frozen params stay bf16, mixed dtypes in an FSDP2 group | unsure ×2, false alarm ×2 | **open** | code check unsure |
| 3 | real-001 | skill, run2 | tests edited because empty prompts now abort | unsure ×2, real ×1, false ×1 | false alarm | read |
| 4 | real-001 | skill, run2 | same claim, second test | unsure ×2, real ×1, false ×1 | false alarm | read |
| 5 | real-002 | skill, run2 | `startswith(base)` without a separator (line 199) | real ×2, unsure ×2 | **the bug (b1)** | read |
| 6 | real-002 | skill, run2 | 7z `badlink` is never called | real ×2, hit ×1, unsure ×1 | real problem | read |
| 7 | real-003 | skill, run2 | fish shows a literal `\n` in help | real ×2, unsure ×2 | real problem | read |
| 8 | real-009 | baseline, run1 | scope pushed on every validator, never popped | hit ×2, unsure ×1, false ×1 | **open** | read |
| 9 | real-005 | skill, run1 | leading CRLF kept when `del_index` is 0 | unsure ×2, false ×1, real ×1 | real problem | code check |
| 10 | real-005 | skill, run3 | `LINE_BREAK_RE.match` can return None | unsure ×2, false alarm ×2 | false alarm | code check |
| 11 | real-012 | skill, run2 | `get_delta_weight` assumes 4D Conv2d weights | unsure ×2, real ×2 | real problem | code check |
| 12 | real-012 | skill, run3 | SVD merge only handles `Conv2d` | real ×2, unsure ×2 | real problem | read |

**10 settled, 2 open.** The settled verdicts don't change the published numbers (precision 72% vs
82%, paired +10 pts [+1, +16]):

- Finding 5 is the bug, but that review already caught it twice, so recall stays the same.
- Hit and real problem both count as correct in precision.
- Findings 3 and 4 are minor, so they don't count in serious precision.
- Findings 1, 9, 10 and 11 were already counted by their code checks.

Left out entirely, the contested findings give +9 pts [0, +17]
(`compare --drop-contested`).

The two open ones:

- **Finding 2:** whether FSDP2 rejects a group with mixed parameter dtypes needs torch's source,
  which is over the code checker's download cap. Today it counts as `unsure`, so it stays in the
  serious-precision denominator but not in the correct count.
- **Finding 8:** the review names the exact lines the change added and blames them for wrong `$ref`
  resolution. Its mechanism, though, is a push that is never popped, while the fixed bug is a
  `None` id being pushed. It counts as a hit today. If it isn't the same bug, baseline recall drops
  from 26 to 25 of 36.

Both are open for outside labelling in [#17](https://github.com/GgauravJ05/reviewreplay/issues/17).
