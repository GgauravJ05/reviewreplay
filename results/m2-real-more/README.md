# Eight more real bugs: baseline vs code-review-skill

Run: 8 new real cases × 2 reviewers × 3 runs = **48 reviews**, `claude-sonnet-5-5`, Claude Code
2.1.319, same setup as [m2-compare](../m2-compare/README.md): Claude Code with no skill
(**baseline**) and with [code-review-skill](https://github.com/awesome-skills/code-review-skill) at
`4850184`, invoked explicitly (**skill**). Every case is a real bug-fix pair from a public
repository, replayed in the full project with no git history.

| Case | Repository | Fix |
|---|---|---|
| real-005 | pallets/werkzeug | multipart parsing of empty fields (#2639) |
| real-006 | python-attrs/attrs | attribute order checks after the field transformer (#1401) |
| real-007 | python-attrs/attrs | `__getstate__`/`__setstate__` as a dict (#1009) |
| real-008 | Textualize/rich | panel title |
| real-009 | python-jsonschema/jsonschema | `RefResolver` resolution in new drafts |
| real-010 | psf/black | blank line after a nested class in stubs (#3564) |
| real-011 | psf/black | f-string tokenization (#4332) |
| real-012 | huggingface/peft | Conv3d in LoRA and IA3 (#2082) |

## These 8 cases

| | Baseline | Skill |
|---|---|---|
| Bug found | 15 / 24 | 15 / 24 |
| Precision (serious findings) | 52% (15/29) | 60% (15/25) |
| False alarms (serious) | 4 | 3 |
| Unverifiable claims (`unsure`) | 10 | 7 |
| Minor remarks per review | 1.1 | 1.3 |
| Mean cost per review | $0.066 | $0.096 |

## All 12 real bugs (this run plus m2-compare's 4)

Nine projects: click, datasets, accelerate, werkzeug, attrs, rich, jsonschema, black and peft.
36 reviews per reviewer.

| | Baseline | Skill | Paired difference (95% CI, bootstrap over cases) |
|---|---|---|---|
| Bug found | 26 / 36 (72%) | 27 / 36 (75%) | +3 pts [−6, +11] |
| Precision (serious findings) | 56% (30/54) | **71%** (40/56) | **+16 pts [+4, +24]** |
| False alarms (serious) | 7 | **3** | |
| Unverifiable claims (`unsure`) | 17 | 13 | |
| Minor remarks per review | 1.2 | 1.1 | |
| Mean cost per review | $0.065 | $0.097 | about **1.5×** |

Reproduce this table with `reviewreplay compare results/m2-compare results/m2-real-more --kind real`.
Every finding is graded by four judges (three `claude-sonnet-5-5` votes and one `claude-opus-5-5`)
and takes the majority label; see [Four-judge re-grade](#four-judge-re-grade) for what changed. The
first single-judge grading gave 26/36 found for both, 57% vs 71% precision, 7 vs 4 false alarms and
+14 pts [0, +24]. "Serious" means a finding the reviewer rated blocking or important.
Precision counts hits and other real problems over all serious findings, `unsure` included.

## What changed

**Recall isn't solved.** With 4 real bugs, Claude Code found the bug 23 times in 24. With 12, it
found it 26 times in 36 without the skill and 27 with it, and **both missed two bugs in every
run**:

- **real-011 (black):** the new f-string state machine compares the state to
  `STATE_NOT_FSTRING`, so a continued string inside f-string braces (`STATE_IN_BRACES`) goes down
  the f-string branch. All six reviews traced the new state machine and reported no bugs. One
  skill run executed Black on extra inputs, and none of them hit the case.
- **real-012 (peft):** LoRA's `lora_A` conv is built from the base layer's kernel size, stride and
  padding, but drops `dilation` and `padding_mode`. All six reviews found other Conv3d issues (a 2D-only
  1×1 shortcut, a wrong error message) but not this one.

The misses are genuine: the graded reviews never mention the defect. Werkzeug (real-005) was found
in 1 of 3 baseline runs and 2 of 3 skill runs.

**The skill's precision edge holds, but it's smaller than on the first 4 bugs.** On 12 bugs the
skill's serious findings were right 71% of the time against 56%, with 3 serious false alarms against
7. After the four-judge re-grade the paired interval is +16 pts [+4, +24], clear of zero, and it
stays clear with contested findings left out (+17 pts [+1, +30]). On the 8 new cases alone the gap was 8
points, and the "half the minor noise" seen on the first 4 bugs didn't repeat (1.1 vs 1.3).

## Four-judge re-grade

A single judge call flip-flopped on one real-012 finding ("the Conv3d error message says Conv2d"),
so every real-bug finding in m2-compare and m2-real-more was graded three more times: twice more
by `claude-sonnet-5-5` and once by `claude-opus-5-5` (`grade --judges 3 --second-judge
claude-opus-5-5`). Each finding takes the majority label; with no strict majority it's
**contested**.

| | |
|---|---|
| Findings graded 4 times | 195 |
| All four votes agree | 150 (77%) |
| The three Sonnet votes agree | 175 (90%) |
| First single verdict = majority | 189 (97%) |
| Contested (no strict majority) | 12 (3 baseline, 9 skill) |
| Sonnet majority vs Opus | 81% agreement, Cohen's κ 0.74 |

What moved: a skill review of werkzeug (real-005 run 2) is now a hit (three of four judges), a
skill false alarm on real-005 became a contested `unsure`, and a baseline real-003 finding went
from another real problem to `unsure`. The two Conv3d error-message findings settle as false alarms
by majority (both were minor, so precision doesn't move).

Reproduce with or without contested findings:
`reviewreplay compare results/m2-compare results/m2-real-more --kind real [--drop-contested]`.

| Without contested findings | Baseline | Skill | Paired difference |
|---|---|---|---|
| Bug found | 25 / 36 | 27 / 36 | +6 pts [−6, +17] |
| Precision (serious) | 57% (29/51) | 74% (37/50) | +17 pts [+1, +30] |

## Grader caveats

- **Model agreement isn't human agreement.** Sonnet and Opus agree at κ 0.74, below the 0.8 target
  set for hand labels, and both are Claude models. The verdicts are checked across models, not by
  people.
- 17 baseline and 13 skill claims are `unsure` (library behaviour the judge can't check from the
  repository). They count against precision until they're scored.
- The earlier κ 0.93 was a separate check against a second model rater on the M1 pilot.

## Next

1. Score `unsure` claims against library source (roadmap 1.3).
2. A short yes/no review of the 12 contested findings, by a person or contributors.
3. Test the skill's verify-before-reporting change (awesome-skills/code-review-skill#34), and
   Claude Code's `/code-review`, on the two cases nobody caught.
