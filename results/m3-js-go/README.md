# Baseline vs code-review-skill on 9 JavaScript, TypeScript and Go bugs

Runs: [m3-real-013](../m3-real-013/summary.md) (axios), [m3-real-014](../m3-real-014/summary.md)
(gin), [m3-real-015](../m3-real-015/summary.md) (testify), [m3-real-016](../m3-real-016/summary.md)
(axios), [m3-real-017](../m3-real-017/summary.md) (cobra), [m3-real-018](../m3-real-018/summary.md)
(cobra), [m3-real-019](../m3-real-019/summary.md) (urfave/cli), [m3-real-020](../m3-real-020/summary.md)
(logrus), [m3-real-021](../m3-real-021/summary.md) (hono, TypeScript, added 2026-11-25).
9 cases × 2 reviewers × 3 runs = **54 reviews**, `claude-sonnet-5-5`, Claude Code 2.1.319,
2026-11-14 and 2026-11-25. Reviewers: Claude Code with no skill (**baseline**) and with
[code-review-skill](https://github.com/awesome-skills/code-review-skill) at `4850184`, invoked
explicitly (**skill**). Review usage about $3.50.

Every finding has four judge votes (Sonnet ×3 and Opus), and the serious `unsure` findings were
checked against the code with `reviewreplay verify` (13 checked, all confirmed). Pooled table:
[compare.md](compare.md).

## Headline

| | Baseline | Skill | Difference (paired, 95% CI) |
|---|---|---|---|
| Bug found | 21 / 27 | 18 / 27 | −11 pts [−30, 0] |
| Precision (serious findings) | **91%** (53/58) | 79% (44/56) | −13 pts [−19, +2] |
| Serious false alarms | **5** | 10 | |
| Median cost per review | $0.046 | $0.071 | about 1.5× |

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
| real-021 hono | TypeScript | 3 / 3 | 3 / 3 | 100% | 100% |

"—" means no serious findings to score.

## What it shows

- **The skill's precision was lower, but no longer clearly.** On the first 4 cases the gap was
  −18 pts [−22, −12]; with 9 it is −13 pts and the interval reaches +2. Of the 8 cases with serious
  findings to score, the skill was lower on 5, level on two and higher on one (real-020). The Python result went the other way
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

- **The first TypeScript case was easy.** real-021 (hono): a refactor made the compress middleware
  skip the `Accept-Encoding` check whenever an `encoding` option is set. All 6 reviews found it, and
  5 also flagged the duplicate in `deno_dist/`. Four minor findings noted that `includes()` treats
  `gzip;q=0` as accepted; the judges called them false alarms because the old regex had the same
  flaw.

## Caveats

- **A correct finding graded as a false alarm.** On real-019 the skill's run 2 described the
  answer-key bug exactly (subcommands no longer inherit the root's separator) but cited the call
  site, `command.go:354-356`, not line 452. Two judges labelled it a false alarm only because it
  couldn't be matched to the key; two called it valid. The tie went to false alarm. Counted as
  valid, the skill's precision is 80%. The judge instructions should be fixed so a finding
  outside the location gate is never a false alarm for that reason alone.
- **A trivial claim judged as a false alarm.** On real-015, three findings (1 baseline, 2 skill)
  say a `*Mock` passed directly now prints a spurious deprecation log. That is true but only a
  log line. Counted as valid, precision is 93% vs 82%.
- **Contested findings.** 14 of 187 findings had no majority label. Leaving them out gives 94% vs
  82%, −12 pts [−17, −5].
- The two judge models agreed on 83% of findings (Cohen's kappa 0.77). Grading is checked across
  models, not yet by people. Nine cases is still a small sample.

## Reproduce

```bash
for c in real-013 real-014 real-015 real-016 real-017 real-018 real-019 real-020 real-021; do
  python3 -m reviewreplay run --out results/m3-$c --cases cases/real/$c --subjects baseline,code-review-skill-invoked --runs 3
  python3 -m reviewreplay extract results/m3-$c
  python3 -m reviewreplay grade results/m3-$c --cases cases/real/$c --judges 3 --second-judge claude-opus-5-5
  python3 -m reviewreplay verify results/m3-$c --cases cases/real/$c
done
python3 -m reviewreplay compare results/m3-real-01{3,4,5,6,7,8,9} results/m3-real-02{0,1} --kind real
```
