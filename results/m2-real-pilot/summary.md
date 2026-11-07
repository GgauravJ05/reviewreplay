# ReviewBench results — `m2-real-pilot`

Model `claude-sonnet-5-5` · 2.1.319 (Claude Code) · 3 runs per case · 3 cases

Values are mean over cases (each case averaged over its runs) with a 95% bootstrap interval over cases.

| Subject | Reviews | Recall | Precision | Clean pass | Decoy trap | Skill used (natural) | Findings / review | Median est. cost | Median time |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 9 | 89% [67%–100%] | 56% [39%–72%] | — | — | — | 4.1 | $0.058 | 18s |

## Per case

| Subject | Case | Kind | Recall | Clean pass | Decoy trap | Skill used |
|---|---|---|---|---|---|---|
| baseline | real-001 | real | 100% | — | — | — |
| baseline | real-002 | real | 67% | — | — | — |
| baseline | real-003 | real | 100% | — | — | — |

## Subjects

- **baseline**. Prompt: `Review the uncommitted changes in this repository. Report any bugs you find, with file and line.`
