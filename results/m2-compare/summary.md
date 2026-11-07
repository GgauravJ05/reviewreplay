# ReviewBench results — `m2-compare`

Model `claude-sonnet-5-5` · 2.1.319 (Claude Code) · 3 runs per case · 18 cases

Values are mean over cases (each case averaged over its runs) with a 95% bootstrap interval over cases.

| Subject | Reviews | Recall | Precision | Clean pass | Decoy trap | Skill used (natural) | Findings / review | Median est. cost | Median time |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 57 | 98% [93%–100%] | 91% [81%–98%] | 100% [100%–100%] | 0% [0%–0%] | — | 2.6 | $0.044 | 11s |
| code-review-skill-invoked | 57 | 100% [100%–100%] | 95% [88%–100%] | 100% [100%–100%] | 0% [0%–0%] | — | 2.5 | $0.074 | 14s |

## Paired difference vs. baseline

Positive = better than baseline for recall, clean pass and precision. An interval that includes 0 means no clear difference.

| Subject | Recall Δ | Clean pass Δ | Precision Δ |
|---|---|---|---|
| code-review-skill-invoked | +2 pts [+0, +7] | +0 pts [+0, +0] | +4 pts [-3, +11] |

## Per case

| Subject | Case | Kind | Recall | Clean pass | Decoy trap | Skill used |
|---|---|---|---|---|---|---|
| baseline | ml-001 | planted | 100% | — | — | — |
| baseline | ml-002 | planted | 100% | — | — | — |
| baseline | ml-003 | decoy | — | 100% | 0% | — |
| baseline | ml-004 | clean | — | 100% | — | — |
| baseline | ml-005 | planted | 100% | — | — | — |
| baseline | ml-006 | planted | 100% | — | — | — |
| baseline | py-001 | planted | 100% | — | — | — |
| baseline | py-002 | planted | 100% | — | — | — |
| baseline | py-003 | decoy | — | 100% | 0% | — |
| baseline | py-004 | clean | — | 100% | — | — |
| baseline | py-005 | planted | 100% | — | — | — |
| baseline | py-006 | planted | 100% | — | — | — |
| baseline | py-007 | planted | 100% | — | — | — |
| baseline | py-008 | planted | 100% | — | — | — |
| baseline | py-009 | decoy | — | 100% | 0% | — |
| baseline | real-001 | real | 100% | — | — | — |
| baseline | real-002 | real | 100% | — | — | — |
| baseline | real-003 | real | 100% | — | — | — |
| baseline | real-004 | real | 67% | — | — | — |
| code-review-skill-invoked | ml-001 | planted | 100% | — | — | — |
| code-review-skill-invoked | ml-002 | planted | 100% | — | — | — |
| code-review-skill-invoked | ml-003 | decoy | — | 100% | 0% | — |
| code-review-skill-invoked | ml-004 | clean | — | 100% | — | — |
| code-review-skill-invoked | ml-005 | planted | 100% | — | — | — |
| code-review-skill-invoked | ml-006 | planted | 100% | — | — | — |
| code-review-skill-invoked | py-001 | planted | 100% | — | — | — |
| code-review-skill-invoked | py-002 | planted | 100% | — | — | — |
| code-review-skill-invoked | py-003 | decoy | — | 100% | 0% | — |
| code-review-skill-invoked | py-004 | clean | — | 100% | — | — |
| code-review-skill-invoked | py-005 | planted | 100% | — | — | — |
| code-review-skill-invoked | py-006 | planted | 100% | — | — | — |
| code-review-skill-invoked | py-007 | planted | 100% | — | — | — |
| code-review-skill-invoked | py-008 | planted | 100% | — | — | — |
| code-review-skill-invoked | py-009 | decoy | — | 100% | 0% | — |
| code-review-skill-invoked | real-001 | real | 100% | — | — | — |
| code-review-skill-invoked | real-002 | real | 100% | — | — | — |
| code-review-skill-invoked | real-003 | real | 100% | — | — | — |
| code-review-skill-invoked | real-004 | real | 100% | — | — | — |

## Subjects

- **baseline**. Prompt: `Review the uncommitted changes in this repository. Report any bugs you find, with file and line.`
- **code-review-skill-invoked** — https://github.com/awesome-skills/code-review-skill @ `4850184`. Prompt: `/code-review-skill Review the uncommitted changes in this repository. Report any bugs you find, with file and line.`. Credit: awesome-skills/code-review-skill (MIT). Invoked explicitly with /code-review-skill.
