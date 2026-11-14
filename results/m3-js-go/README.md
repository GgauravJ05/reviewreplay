# Baseline vs code-review-skill on 4 JavaScript and Go bugs

Runs: [m3-real-013](../m3-real-013/summary.md) (axios), [m3-real-014](../m3-real-014/summary.md)
(gin), [m3-real-015](../m3-real-015/summary.md) (testify), [m3-real-016](../m3-real-016/summary.md)
(axios). 4 cases × 2 reviewers × 3 runs = **24 reviews**, `claude-sonnet-5-5`, Claude Code 2.1.319,
2026-11-14. Reviewers: Claude Code with no skill (**baseline**) and with
[code-review-skill](https://github.com/awesome-skills/code-review-skill) at `4850184`, invoked
explicitly (**skill**). Review usage about $1.60.

Every finding has four judge votes (Sonnet ×3 and Opus), and the serious `unsure` findings were
checked against the code with `reviewreplay verify` (6 checked, all confirmed). Pooled table:
[compare.md](compare.md).

## Headline

| | Baseline | Skill | Difference (paired, 95% CI) |
|---|---|---|---|
| Bug found | 9 / 12 | 8 / 12 | −8 pts [−25, 0] |
| Precision (serious findings) | **95%** (40/42) | 77% (30/39) | −18 pts [−22, −12] |
| Serious false alarms | **2** | 7 | |
| Median cost per review | $0.054 | $0.075 | about 1.4× |

| Case | Language | Bug found, baseline | Bug found, skill | Precision, baseline | Precision, skill |
|---|---|---|---|---|---|
| real-013 axios | JavaScript | 3 / 3 | 2 / 3 | 92% | 81% |
| real-014 gin | Go | 3 / 3 | 3 / 3 | 100% | 81% |
| real-015 testify | Go | 3 / 3 | 3 / 3 | 83% | 67% |
| real-016 axios | JavaScript | 0 / 3 | 0 / 3 | 100% | 86% |

## What it shows

- **On these 4 cases the skill did worse, not better.** Its precision was lower on every case.
  This is the opposite of the 12 Python bugs (72% → 82% with the skill). Four cases is a small
  sample, and it says nothing yet about languages in general.
- **The skill's extra false alarms repeat across runs.** On real-013 it twice flagged that header
  values are now trimmed of spaces and tabs (the baseline made the same claim once); on real-014 it
  twice flagged that the `perm` argument applies to the directory rather than the file. The judges
  rejected both.
- **real-016 was missed in all 6 reviews.** #5558 made `AxiosError` a native `Error`, which turned
  `message` non-enumerable, so `Object.keys(err)` and `{...err}` lost it. Every review noticed
  enumerability changes on the same lines (`isAxiosError`, `cause`, `__CANCEL__`), but none
  noticed `message`, the one that broke users.

## Caveats

- **A trivial claim judged as a false alarm.** On real-015, three findings (1 baseline, 2 skill)
  say a `*Mock` passed directly now prints a spurious deprecation log. That is true in the code,
  but only a log line; the judges marked it a false alarm. Counted as valid, precision is 98% vs
  82%, about −16 pts. The direction holds.
- **Contested findings.** 8 of 108 findings had no majority label. Leaving them out gives 95% vs
  80%, −15 pts [−20, −10].
- The two judge models agreed on 77% of findings (Cohen's kappa 0.64). Grading is checked across
  models, not yet by people.

## Reproduce

```bash
for c in real-013 real-014 real-015 real-016; do
  python3 -m reviewreplay run --out results/m3-$c --cases cases/real/$c --subjects baseline,code-review-skill-invoked --runs 3
  python3 -m reviewreplay extract results/m3-$c
  python3 -m reviewreplay grade results/m3-$c --cases cases/real/$c --judges 3 --second-judge claude-opus-5-5
  python3 -m reviewreplay verify results/m3-$c --cases cases/real/$c
done
python3 -m reviewreplay compare results/m3-real-01{3,4,5,6} --kind real
```
