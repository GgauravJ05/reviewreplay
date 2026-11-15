# ReviewReplay comparison — m3-real-013, m3-real-014, m3-real-015, m3-real-016, m3-real-017, m3-real-018, m3-real-019, m3-real-020 · real cases only

| Subject | Cases | Reviews | Bug found | Recall | Precision (serious) | Serious false alarms | Unsure | Contested | Minor / review | Mean cost | Median cost |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 8 | 24 | 18 / 24 | 75% [38%–100%] | 90% (47/52) [71%–100%] | 5 | 0 | 8 | 1.5 | $0.054 | $0.049 |
| code-review-skill-invoked | 8 | 24 | 15 / 24 | 62% [29%–88%] | 77% (40/52) [71%–82%] | 10 | 2 | 6 | 1.3 | $0.078 | $0.074 |

## Paired difference vs. baseline

Bootstrapped over the cases both subjects share. An interval that includes 0 means no clear difference.

| Subject | Recall Δ | Precision Δ (pooled) | Shared cases |
|---|---|---|---|
| code-review-skill-invoked | -12 pts [-33, 0] | -13 pts [-20, +3] | 8 |

## Judge agreement

172 findings graded 4.0 times on average: 123 unanimous, 14 contested (no label with a strict majority).
Between `claude-sonnet-5-5` and `claude-opus-5-5` on 172 findings: 82% agreement, Cohen's kappa 0.75.

## Code checks of `unsure` findings

13 `unsure` findings checked against the code (`reviewreplay verify`): 13 confirmed (now another real problem), 0 refuted (now a false alarm), 0 still unsure. Pass `--ignore-verify` for the judges' labels alone.
