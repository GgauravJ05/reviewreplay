# ReviewBench results — `smoke`

Model `claude-sonnet-5-5` · 2.1.309 (Claude Code) · 1 runs per case · 5 cases

Values are mean over cases (each case averaged over its runs) with a 95% bootstrap interval over cases.

| Subject | Reviews | Recall | Precision | Clean pass | Decoy trap | Skill used (natural) | Findings / review | Median est. cost | Median time |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 5 | 100% [100%–100%] | 100% [100%–100%] | 100% [100%–100%] | 0% [0%–0%] | — | 1.6 | $0.036 | 12s |
| code-review-skill-invoked | 5 | 100% [100%–100%] | 100% [100%–100%] | 100% [100%–100%] | 0% [0%–0%] | — | 1.8 | $0.059 | 13s |
| code-review-skill-natural | 5 | 100% [100%–100%] | 83% [50%–100%] | 100% [100%–100%] | 0% [0%–0%] | 0% [0%–0%] | 1.4 | $0.038 | 10s |

## Paired difference vs. baseline

Positive = better than baseline for recall, clean pass and precision. An interval that includes 0 means no clear difference.

| Subject | Recall Δ | Clean pass Δ | Precision Δ |
|---|---|---|---|
| code-review-skill-invoked | +0 pts [+0, +0] | +0 pts [+0, +0] | +0 pts [+0, +0] |
| code-review-skill-natural | +0 pts [+0, +0] | +0 pts [+0, +0] | -17 pts [-50, +0] |

## Per case

| Subject | Case | Kind | Recall | Clean pass | Decoy trap | Skill used |
|---|---|---|---|---|---|---|
| baseline | py-001 | planted | 100% | — | — | — |
| baseline | py-002 | planted | 100% | — | — | — |
| baseline | py-003 | decoy | — | 100% | 0% | — |
| baseline | py-004 | clean | — | 100% | — | — |
| baseline | py-005 | planted | 100% | — | — | — |
| code-review-skill-invoked | py-001 | planted | 100% | — | — | — |
| code-review-skill-invoked | py-002 | planted | 100% | — | — | — |
| code-review-skill-invoked | py-003 | decoy | — | 100% | 0% | — |
| code-review-skill-invoked | py-004 | clean | — | 100% | — | — |
| code-review-skill-invoked | py-005 | planted | 100% | — | — | — |
| code-review-skill-natural | py-001 | planted | 100% | — | — | 0% |
| code-review-skill-natural | py-002 | planted | 100% | — | — | 0% |
| code-review-skill-natural | py-003 | decoy | — | 100% | 0% | 0% |
| code-review-skill-natural | py-004 | clean | — | 100% | — | 0% |
| code-review-skill-natural | py-005 | planted | 100% | — | — | 0% |

## Subjects

- **baseline**. Prompt: `Review the uncommitted changes in this repository. Report any bugs you find, with file and line.`
- **code-review-skill-invoked** — https://github.com/awesome-skills/code-review-skill @ `4850184`. Prompt: `/code-review-skill Review the uncommitted changes in this repository. Report any bugs you find, with file and line.`. Credit: awesome-skills/code-review-skill (MIT). Invoked explicitly with /code-review-skill.
- **code-review-skill-natural** — https://github.com/awesome-skills/code-review-skill @ `4850184`. Prompt: `Review the uncommitted changes in this repository. Report any bugs you find, with file and line.`. Credit: awesome-skills/code-review-skill (MIT). Installed; Claude decides whether to use it.
