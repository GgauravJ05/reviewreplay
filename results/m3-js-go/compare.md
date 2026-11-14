# ReviewReplay comparison — m3-real-013, m3-real-014, m3-real-015, m3-real-016 · real cases only

| Subject | Cases | Reviews | Bug found | Recall | Precision (serious) | Serious false alarms | Unsure | Contested | Minor / review | Mean cost | Median cost |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 4 | 12 | 9 / 12 | 75% [25%–100%] | 95% (40/42) [87%–100%] | 2 | 0 | 4 | 1.2 | $0.055 | $0.054 |
| code-review-skill-invoked | 4 | 12 | 8 / 12 | 67% [25%–100%] | 77% (30/39) [71%–80%] | 7 | 2 | 4 | 1.0 | $0.078 | $0.075 |

## Paired difference vs. baseline

Bootstrapped over the cases both subjects share. An interval that includes 0 means no clear difference.

| Subject | Recall Δ | Precision Δ (pooled) | Shared cases |
|---|---|---|---|
| code-review-skill-invoked | -8 pts [-25, 0] | -18 pts [-22, -12] | 4 |

## Judge agreement

108 findings graded 4.0 times on average: 71 unanimous, 8 contested (no label with a strict majority).
Between `claude-sonnet-5-5` and `claude-opus-5-5` on 108 findings: 77% agreement, Cohen's kappa 0.64.

## Code checks of `unsure` findings

6 `unsure` findings checked against the code (`reviewreplay verify`): 6 confirmed (now another real problem), 0 refuted (now a false alarm), 0 still unsure. Pass `--ignore-verify` for the judges' labels alone.
