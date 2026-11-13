# Baseline vs code-review-skill — findings

Run: 19 cases (6 ML + 9 Python planted/clean/decoy, 4 real bugs in full repositories) × 2 reviewers
× 3 runs = **114 reviews**, `claude-sonnet-5-5`, Claude Code 2.1.319, 2026-11-07.
Reviewers: Claude Code with no skill (**baseline**) and with
[code-review-skill](https://github.com/awesome-skills/code-review-skill) at `4850184`, invoked
explicitly (**skill**). Usage ≈ $6.70 for reviews, plus extraction and grading.

> **Re-graded 2026-11-08:** the real-bug findings now carry four judge votes; see
> [m2-real-more](../m2-real-more/README.md#four-judge-re-grade). On these 4 bugs the baseline's
> precision is 60% (15/25) by majority vote; the skill's numbers are unchanged. The tables below are the
> original single-judge grading.
>
> **Code-checked 2026-11-08:** the serious `unsure` claims on these 4 bugs were then checked against the
> code ([m2-real-more](../m2-real-more/README.md#code-checks-of-unsure-claims)): precision is now 72%
> (18/25) for the baseline and 87% (27/31) for the skill, with 6 and 4 serious false alarms.

## Headline

| | Baseline | Skill | Difference (paired, 95% CI) |
|---|---|---|---|
| Recall, all cases | 98% | 100% | +2 pts |
| Precision, all cases | 91% | 95% | +4 pts, interval includes 0 |
| Clean pass / decoy trap | 100% / 0% | 100% / 0% | none |
| Median cost per review | $0.044 | $0.074 | **+68%** |

## Where they differ: real bugs (4 cases, 12 reviews each)

| | Baseline | Skill |
|---|---|---|
| Bug found | 11 / 12 | **12 / 12** |
| Precision (serious findings) | 64% (16/25) | **81%** (25/31) |
| False alarms (serious) | 3 | **0** |
| Unverifiable claims (`unsure`) | 6 | 6 |
| Minor remarks per review | 1.6 | **0.7** |
| Mean cost per review | $0.064 | $0.100 |

- The one baseline miss is genuine: real-004 (accelerate FSDP2 deadlock) run 2 discussed the
  upcast but not the stale `state_dict()` snapshot.
- On planted, clean and decoy cases both are at or near the ceiling (95% vs 100% precision).

**Reading:** on real code in full repositories, the skill-guided review was quieter and more
accurate: no serious false alarms and half the minor noise, and it never missed the bug, at about
1.6× the cost. With 4 real cases this is a **direction, not a conclusion**: the intervals are wide,
and the tested commit predates the verify-before-reporting change proposed in
awesome-skills/code-review-skill#34.

## Grader changes in this run

- Findings that name a file but **no line** may now match a known bug in that file (the judge's
  same-defect rule decides). This fixed a baseline review of real-002 that described the exact bug
  without a line number and had been scored as a miss. Unit-tested.
- real-004 was mined automatically, its answer key drafted by `init`, and confirmed against the
  upstream fix before use.

## Next

1. More real cases (the deciding factor); 10–20 before any public claim.
2. Score `unsure` claims (12 here) by checking them against the library source.
3. Test the skill with #34's verify step (pin the PR branch) and Claude Code's `/code-review`.
4. Share on awesome-skills/code-review-skill#32 before publishing.
