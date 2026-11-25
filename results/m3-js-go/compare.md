# ReviewReplay comparison — m3-real-013, m3-real-014, m3-real-015, m3-real-016, m3-real-017, m3-real-018, m3-real-019, m3-real-020, m3-real-021 · real cases only

| Subject | Cases | Reviews | Bug found | Recall | Precision (serious) | Serious false alarms | Unsure | Contested | Minor / review | Mean cost | Median cost |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 9 | 27 | 21 / 27 | 78% [44%–100%] | 91% (53/58) [75%–100%] | 5 | 0 | 8 | 1.4 | $0.053 | $0.046 |
| code-review-skill-invoked | 9 | 27 | 18 / 27 | 67% [37%–89%] | 79% (44/56) [73%–85%] | 10 | 2 | 6 | 1.3 | $0.076 | $0.071 |

## Paired difference vs. baseline

Bootstrapped over the cases both subjects share. An interval that includes 0 means no clear difference.

| Subject | Recall Δ | Precision Δ (pooled) | Shared cases |
|---|---|---|---|
| code-review-skill-invoked | -11 pts [-30, 0] | -13 pts [-19, +2] | 9 |

## Judge agreement

187 findings graded 4.0 times on average: 137 unanimous, 14 contested (no label with a strict majority).
Between `claude-sonnet-5-5` and `claude-opus-5-5` on 187 findings: 83% agreement, Cohen's kappa 0.77.

## Code checks of `unsure` findings

13 `unsure` findings checked against the code (`reviewreplay verify`): 13 confirmed (now another real problem), 0 refuted (now a false alarm), 0 still unsure. Pass `--ignore-verify` for the judges' labels alone.
