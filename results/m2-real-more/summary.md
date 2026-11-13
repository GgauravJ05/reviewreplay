# ReviewReplay results — `m2-real-more`

Model `claude-sonnet-5-5` · 2.1.319 (Claude Code) · 3 runs per case · 8 cases

Values are mean over cases (each case averaged over its runs) with a 95% bootstrap interval over cases.

| Subject | Reviews | Recall | Precision | Clean pass | Decoy trap | Skill used (natural) | Findings / review | Median est. cost | Median time |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 24 | 62% [33%–92%] | 84% [71%–95%] | — | — | — | 2.3 | $0.059 | 19s |
| code-review-skill-invoked | 24 | 62% [33%–88%] | 83% [72%–94%] | — | — | — | 2.4 | $0.083 | 23s |

## Paired difference vs. baseline

Positive = better than baseline for recall, clean pass and precision. An interval that includes 0 means no clear difference.

| Subject | Recall Δ | Clean pass Δ | Precision Δ |
|---|---|---|---|
| code-review-skill-invoked | -0 pts [-12, +12] | — | +2 pts [-6, +10] |

## Per case

| Subject | Case | Kind | Recall | Clean pass | Decoy trap | Skill used |
|---|---|---|---|---|---|---|
| baseline | real-005 | real | 33% | — | — | — |
| baseline | real-006 | real | 67% | — | — | — |
| baseline | real-007 | real | 100% | — | — | — |
| baseline | real-008 | real | 100% | — | — | — |
| baseline | real-009 | real | 100% | — | — | — |
| baseline | real-010 | real | 100% | — | — | — |
| baseline | real-011 | real | 0% | — | — | — |
| baseline | real-012 | real | 0% | — | — | — |
| code-review-skill-invoked | real-005 | real | 67% | — | — | — |
| code-review-skill-invoked | real-006 | real | 67% | — | — | — |
| code-review-skill-invoked | real-007 | real | 100% | — | — | — |
| code-review-skill-invoked | real-008 | real | 67% | — | — | — |
| code-review-skill-invoked | real-009 | real | 100% | — | — | — |
| code-review-skill-invoked | real-010 | real | 100% | — | — | — |
| code-review-skill-invoked | real-011 | real | 0% | — | — | — |
| code-review-skill-invoked | real-012 | real | 0% | — | — | — |

## Subjects

- **baseline**. Prompt: `Review the uncommitted changes in this repository. Report any bugs you find, with file and line.`
- **code-review-skill-invoked** — https://github.com/awesome-skills/code-review-skill @ `4850184`. Prompt: `/code-review-skill Review the uncommitted changes in this repository. Report any bugs you find, with file and line.`. Credit: awesome-skills/code-review-skill (MIT). Invoked explicitly with /code-review-skill.
