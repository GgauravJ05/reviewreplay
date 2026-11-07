# ReviewBench results — `m2-hard-pilot`

Model `claude-sonnet-5-5` · 2.1.319 (Claude Code) · 3 runs per case · 5 cases

Values are mean over cases (each case averaged over its runs) with a 95% bootstrap interval over cases.

| Subject | Reviews | Recall | Precision | Clean pass | Decoy trap | Skill used (natural) | Findings / review | Median est. cost | Median time |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 15 | 100% [100%–100%] | 100% [100%–100%] | 100% [100%–100%] | 0% [0%–0%] | — | 2.8 | $0.051 | 14s |

## Per case

| Subject | Case | Kind | Recall | Clean pass | Decoy trap | Skill used |
|---|---|---|---|---|---|---|
| baseline | ml-006 | planted | 100% | — | — | — |
| baseline | py-006 | planted | 100% | — | — | — |
| baseline | py-007 | planted | 100% | — | — | — |
| baseline | py-008 | planted | 100% | — | — | — |
| baseline | py-009 | decoy | — | 100% | 0% | — |

## Subjects

- **baseline**. Prompt: `Review the uncommitted changes in this repository. Report any bugs you find, with file and line.`
