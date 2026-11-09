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
| Precision (serious findings) | 72% (21/29) | 76% (19/25) |
| False alarms (serious) | 7 | 6 |
| Still unverifiable (`unsure`) | 1 | 0 |
| Minor remarks per review | 1.1 | 1.3 |
| Mean cost per review | $0.066 | $0.096 |

## All 12 real bugs (this run plus m2-compare's 4)

Nine projects: click, datasets, accelerate, werkzeug, attrs, rich, jsonschema, black and peft.
36 reviews per reviewer.

| | Baseline | Skill | Paired difference (95% CI, bootstrap over cases) |
|---|---|---|---|
| Bug found | 26 / 36 (72%) | 27 / 36 (75%) | +3 pts [−6, +11] |
| Precision (serious findings) | 72% (39/54) | **82%** (46/56) | **+10 pts [+1, +16]** |
| False alarms (serious) | 13 | **10** | |
| Still unverifiable (`unsure`) | 2 | 0 | |
| Minor remarks per review | 1.2 | 1.1 | |
| Mean cost per review | $0.065 | $0.097 | about **1.5×** |

Reproduce this table with `reviewreplay compare results/m2-compare results/m2-real-more --kind real`.
Every finding is graded by four judges (three `claude-sonnet-5-5` votes and one `claude-opus-5-5`)
and takes the majority label, and the serious claims the judges couldn't settle were then checked
against the code; see [Four-judge re-grade](#four-judge-re-grade) and
[Code checks](#code-checks-of-unsure-claims). Before the code checks: 56% vs 71% precision, 7 vs 3
false alarms, +16 pts [+4, +24]. The first single-judge grading: 57% vs 71%, 7 vs 4, +14 pts [0, +24]. "Serious" means a finding the reviewer rated blocking or important.
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

**The skill's precision edge holds, but it's smaller than it first looked.** Once the unverifiable
claims are checked against the code, both reviewers are more often right than the judges alone
showed: on 12 bugs the skill's serious findings were right 82% of the time against 72%, with 10
serious false alarms against 13. The paired interval is +10 pts [+1, +16], just clear of zero; with
contested findings left out it touches zero (+9 pts [0, +17]). On the 8 new cases alone the gap is 4
points [−9, +13], and the "half the minor noise" seen on the first 4 bugs didn't repeat (1.1 vs 1.3).

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

## Code checks of `unsure` claims

The judges grade from text, so 30 serious claims stayed `unsure`, most about how a library or a
distant part of the project behaves. `reviewreplay verify` gave each one to a read-only checker
(`claude-sonnet-5-5` with Read, Grep and Glob only) holding the project after the change, the patch
and, where the claim depends on a library, that library's Python source from the last PyPI release
before the change. It must quote the code that decides the claim, and every quote is matched against
the file in code; a verdict with no matching quote counts as `unsure`.

| | Baseline | Skill |
|---|---|---|
| Checked | 17 | 13 |
| Confirmed (now another real problem) | 9 | 6 |
| Refuted (now a false alarm) | 6 | 7 |
| Still `unsure` | 2 | 0 |

All 30 verdicts had their quotes found in the files; none was downgraded. Cost: $1.38 in all, about
$0.05 a claim. Examples:

- **real-002 (py7zr):** five reviews claimed py7zr treats an empty `targets` list as "no filter".
  With py7zr 1.1.0's source the checker refuted all five: only `targets is None` turns the filter off.
- **real-012 (peft):** all six claims that the 1×1 shortcut in `get_delta_weight` is 2D-only were
  confirmed.
- **real-005 (werkzeug):** two skill claims that `LINE_BREAK_RE.match` can return `None` in
  `DATA_START` were refuted: the blank line's second line break is always still in the buffer.

Two stayed `unsure`, both because the deciding code wasn't available: real-004 needs torch's
source (over the download cap) and real-007 needs the standard library's pickle machinery. Reproduce:
`reviewreplay verify results/m2-real-more --kind real`, then `compare` as above;
`compare --ignore-verify` shows the judges' labels alone.

## Grader caveats

- **Model agreement isn't human agreement.** Sonnet and Opus agree at κ 0.74, below the 0.8 target
  set for hand labels, and both are Claude models. The verdicts are checked across models, not by
  people.
- Each code check is one model call, not a vote, and no person has audited them; three refutes
  were spot-checked against the source with Claude Code. A wrong refute turns a real problem into a
  false alarm, so the checks carry less weight than the four-judge labels.
- The earlier κ 0.93 was a separate check against a second model rater on the M1 pilot.

## Next

1. A short yes/no review of the 12 contested findings, by a person or contributors.
2. Test the skill's verify-before-reporting change (awesome-skills/code-review-skill#34), and
   Claude Code's `/code-review`, on the two cases nobody caught.
