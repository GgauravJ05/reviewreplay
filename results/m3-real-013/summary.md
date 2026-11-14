# ReviewReplay results — `m3-real-013`

Model `claude-sonnet-5-5` · 2.1.319 (Claude Code) · 3 runs per case · 1 cases

Values are mean over cases (each case averaged over its runs) with a 95% bootstrap interval over cases.

| Subject | Reviews | Recall | Precision | Clean pass | Decoy trap | Skill used (natural) | Findings / review | Median est. cost | Median time |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 3 | 100% [100%–100%] | 92% [92%–92%] | — | — | — | 3.3 | $0.063 | 18s |
| code-review-skill-invoked | 3 | 67% [67%–67%] | 81% [81%–81%] | — | — | — | 3.3 | $0.083 | 17s |

## Paired difference vs. baseline

Positive = better than baseline for recall, clean pass and precision. An interval that includes 0 means no clear difference.

| Subject | Recall Δ | Clean pass Δ | Precision Δ |
|---|---|---|---|
| code-review-skill-invoked | -33 pts [-33, -33] | — | -11 pts [-11, -11] |

## Per case

| Subject | Case | Kind | Recall | Clean pass | Decoy trap | Skill used |
|---|---|---|---|---|---|---|
| baseline | real-013 | real | 100% | — | — | — |
| code-review-skill-invoked | real-013 | real | 67% | — | — | — |

## Subjects

- **baseline**. Prompt: `Review the uncommitted changes in this repository. Report any bugs you find, with file and line.`
- **code-review-skill-invoked** — https://github.com/awesome-skills/code-review-skill @ `4850184`. Prompt: `/code-review-skill Review the uncommitted changes in this repository. Report any bugs you find, with file and line.`. Credit: awesome-skills/code-review-skill (MIT). Invoked explicitly with /code-review-skill.
