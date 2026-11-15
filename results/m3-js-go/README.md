# Baseline vs code-review-skill on 8 JavaScript and Go bugs

Runs: [m3-real-013](../m3-real-013/summary.md) (axios), [m3-real-014](../m3-real-014/summary.md)
(gin), [m3-real-015](../m3-real-015/summary.md) (testify), [m3-real-016](../m3-real-016/summary.md)
(axios), [m3-real-017](../m3-real-017/summary.md) (cobra), [m3-real-018](../m3-real-018/summary.md)
(cobra), [m3-real-019](../m3-real-019/summary.md) (urfave/cli), [m3-real-020](../m3-real-020/summary.md)
(logrus). 8 cases × 2 reviewers × 3 runs = **48 reviews**, `claude-sonnet-5-5`, Claude Code 2.1.319,
2026-11-14. Reviewers: Claude Code with no skill (**baseline**) and with
[code-review-skill](https://github.com/awesome-skills/code-review-skill) at `4850184`, invoked
explicitly (**skill**). Review usage about $3.20.

Every finding has four judge votes (Sonnet ×3 and Opus), and the serious `unsure` findings were
checked against the code with `reviewreplay verify` (13 checked, all confirmed). Pooled table:
[compare.md](compare.md).

## Headline

| | Baseline | Skill | Difference (paired, 95% CI) |
|---|---|---|---|
| Bug found | 18 / 24 | 15 / 24 | −12 pts [−33, 0] |
| Precision (serious findings) | **90%** (47/52) | 77% (40/52) | −13 pts [−20, +3] |
| Serious false alarms | **5** | 10 | |
| Median cost per review | $0.049 | $0.074 | about 1.5× |

| Case | Language | Bug found, baseline | Bug found, skill | Precision, baseline | Precision, skill |
|---|---|---|---|---|---|
| real-013 axios | JavaScript | 3 / 3 | 2 / 3 | 92% | 81% |
| real-014 gin | Go | 3 / 3 | 3 / 3 | 100% | 81% |
| real-015 testify | Go | 3 / 3 | 3 / 3 | 83% | 67% |
| real-016 axios | JavaScript | 0 / 3 | 0 / 3 | 100% | 86% |
| real-017 cobra | Go (bash) | 3 / 3 | 3 / 3 | 100% | 100% |
| real-018 cobra | Go | 0 / 3 | 0 / 3 | — | — |
| real-019 urfave/cli | Go | 3 / 3 | 1 / 3 | 100% | 89% |
| real-020 logrus | Go | 3 / 3 | 3 / 3 | 0% | 58% |

"—" means no serious findings to score.

## What it shows

- **The skill's precision was lower, but no longer clearly.** On the first 4 cases the gap was
  −18 pts [−22, −12]; with 8 it is −13 pts and the interval reaches +3. Of the 7 cases with serious
  findings to score, the skill was lower on 5, level on one and higher on one (real-020). The Python result went the other way
  (72% → 82% with the skill), so language, or just these projects, may matter.
- **Two bugs were missed in every review.** real-016: an `Error` subclass made axios's `message`
  non-enumerable; reviews flagged enumerability changes on `isAxiosError`, `cause` and
  `__CANCEL__` on the same lines, never `message`. real-018: cobra's new named `CompletionFunc`
  type breaks callers that pass their own named func type; reviews noticed the type change and
  talked about reflection, but not that such code stops compiling.
- **Finding a bug is not the same as rating it.** On real-020 (logrus) the baseline found the
  deadlock in all 3 runs but rated it minor, so it doesn't count toward precision; its only
  serious finding per run was a disputed test complaint, hence 0%. The skill rated the deadlock
  important or blocking twice.

## Caveats

- **A correct finding graded as a false alarm.** On real-019 the skill's run 2 described the
  answer-key bug exactly (subcommands no longer inherit the root's separator) but cited the call
  site, `command.go:354-356`, not line 452. Two judges labelled it a false alarm only because it
  couldn't be matched to the key; two called it valid. The tie went to false alarm. Counted as
  valid, the skill's precision is 79%. The judge instructions should be fixed so a finding
  outside the location gate is never a false alarm for that reason alone.
- **A trivial claim judged as a false alarm.** On real-015, three findings (1 baseline, 2 skill)
  say a `*Mock` passed directly now prints a spurious deprecation log. That is true but only a
  log line. Counted as valid, precision is 92% vs 81%.
- **Contested findings.** 14 of 172 findings had no majority label. Leaving them out gives 93% vs
  81%, −13 pts [−18, −5].
- The two judge models agreed on 82% of findings (Cohen's kappa 0.75). Grading is checked across
  models, not yet by people. Eight cases is still a small sample.

## Reproduce

```bash
for c in real-013 real-014 real-015 real-016 real-017 real-018 real-019 real-020; do
  python3 -m reviewreplay run --out results/m3-$c --cases cases/real/$c --subjects baseline,code-review-skill-invoked --runs 3
  python3 -m reviewreplay extract results/m3-$c
  python3 -m reviewreplay grade results/m3-$c --cases cases/real/$c --judges 3 --second-judge claude-opus-5-5
  python3 -m reviewreplay verify results/m3-$c --cases cases/real/$c
done
python3 -m reviewreplay compare results/m3-real-01{3,4,5,6,7,8,9} results/m3-real-020 --kind real
```
