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
| Bug found | 15 / 24 | 14 / 24 |
| Precision (serious findings) | 52% (15/29) | 60% (15/25) |
| False alarms (serious) | 4 | 4 |
| Unverifiable claims (`unsure`) | 10 | 6 |
| Minor remarks per review | 1.1 | 1.3 |
| Mean cost per review | $0.066 | $0.096 |

## All 12 real bugs (this run plus m2-compare's 4)

Nine projects: click, datasets, accelerate, werkzeug, attrs, rich, jsonschema, black and peft.
36 reviews per reviewer.

| | Baseline | Skill | Paired difference (95% CI, bootstrap over cases) |
|---|---|---|---|
| Bug found | 26 / 36 (72%) | 26 / 36 (72%) | 0 pts [−8, +8] |
| Precision (serious findings) | 57% (31/54) | **71%** (40/56) | +14 pts [0, +24] |
| False alarms (serious) | 7 | **4** | |
| Unverifiable claims (`unsure`) | 16 | 12 | |
| Minor remarks per review | 1.2 | 1.1 | |
| Mean cost per review | $0.065 | $0.097 | about **1.5×** |

Reproduce this table with `reviewreplay compare results/m2-compare results/m2-real-more --kind real`.
The m2-compare rows reproduce exactly from its grade files (16/25 and 25/31), so the two runs add up
on the same definitions. "Serious" means a finding the reviewer rated blocking or important.
Precision counts hits and other real problems over all serious findings, `unsure` included.

## What changed

**Recall isn't solved.** With 4 real bugs, Claude Code found the bug 23 times in 24. With 12, it
found it 26 times in 36 with or without the skill, and **both missed two bugs in every run**:

- **real-011 (black):** the new f-string state machine compares the state to
  `STATE_NOT_FSTRING`, so a continued string inside f-string braces (`STATE_IN_BRACES`) goes down
  the f-string branch. All six reviews traced the new state machine and reported no bugs. One
  skill run executed Black on extra inputs, and none of them hit the case.
- **real-012 (peft):** LoRA's `lora_A` conv is built from the base layer's kernel size, stride and
  padding, but drops `dilation` and `padding_mode`. All six reviews found other Conv3d issues (a 2D-only
  1×1 shortcut, a wrong error message) but not this one.

The misses are genuine: the graded reviews never mention the defect. Werkzeug (real-005) was found
in only 1 of 3 runs by each reviewer.

**The skill's precision edge holds, but it's smaller.** On 12 bugs the skill's serious findings
were right 71% of the time against 57%, with 4 false alarms against 7. The paired interval just
touches zero, so this is a lead to test, not a result. On the 8 new cases alone the gap was 8
points, and the "half the minor noise" seen on the first 4 bugs didn't repeat (1.1 vs 1.3).

## Grader caveats

- **Judge inconsistency:** the same finding in real-012 ("the Conv3d error message says Conv2d")
  was graded as another real problem in 3 reviews and a false alarm in 3. Precision moves by a few
  points depending on which call is right. This is the strongest case yet for the human-label
  sample.
- 16 baseline and 12 skill claims are `unsure` (library behaviour the judge can't check from the
  repository). They count against precision until they're scored.
- κ 0.93 is agreement with a second model rater, not with people.

## Next

1. Human labels on a sample, starting with the inconsistent real-012 verdicts.
2. Score `unsure` claims against library source.
3. Test the skill's verify-before-reporting change (awesome-skills/code-review-skill#34), and
   Claude Code's `/code-review`, on the two cases nobody caught.
