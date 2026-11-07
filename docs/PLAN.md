# ReviewBench — Design Plan

Status: planning · Repo: private until launch · Written 2026-11-06

ReviewBench measures whether an AI code reviewer actually helps. It runs a reviewer
(Claude with no skill, Claude with a review skill, Claude Code's built-in `/code-review`, …)
on code changes where the right answer is already known, then scores what the reviewer
caught, what it got wrong, and what it cost.

It started from an open question on
[awesome-skills/code-review-skill#32](https://github.com/awesome-skills/code-review-skill/issues/32):
*did anyone measure whether the skill helps?* Nobody had.

---

## 1. Goals and non-goals

**Goals**

1. Give a **fair, repeatable number** for "does reviewer X find real bugs, and how often
   does it raise false alarms?"
2. Compare reviewers **on the same cases**, under the same conditions, with spread shown.
3. Make every number auditable: raw reviewer output, extracted findings, and the grade for
   each one are saved.
4. Make it easy to add a case or a reviewer without touching the core code.

**Non-goals (v1)**

- Not a general coding benchmark (no "write the fix" tasks; reviewing only).
- Not a leaderboard of models. The model stays fixed; the reviewer setup is what varies.
- No executing case code in v1. Reviewers read code; they don't run it (see §9 for v2).

---

## 2. Core ideas

| Idea | Why |
|---|---|
| **Known answers** | Every case has an answer key, so "caught it" is checkable, not opinion. |
| **Clean and decoy cases** | A reviewer that flags everything must lose. Decoys (correct code that *looks* buggy) test whether it checks before accusing. |
| **Isolated runs** | Each reviewer runs in a fresh, empty setup with only its own skill. Otherwise whatever skills happen to be installed leak into results. |
| **Natural output, uniform extraction** | Reviewers answer in their own style. A separate extractor turns every answer into the same findings format, so no reviewer is handicapped by a forced format. |
| **Two-stage grading** | Location matching is done by code (deterministic). Only "is this the same bug?" goes to an AI judge, which is checked against hand labels. |
| **Repeated runs** | Each case runs 3× per reviewer; results are reported with spread, never as one lucky run. |

---

## 3. Test cases

### 3.1 Kinds

| Kind | What it is | Measures | Share (v1) |
|---|---|---|---|
| **planted** | A realistic feature change (40–150 lines) we write, containing exactly one known bug | Recall without training-data contamination | ~50% |
| **real** | A real bug-introducing commit from an open-source repo (found from its fix commit, see §3.4) | Recall on bugs people actually shipped | 0% in M1, ~20% from M3 |
| **clean** | A correct change with no bug | False alarms | ~20% |
| **decoy** | A correct change that looks suspicious (e.g. "missing" null check the caller already guards, an intentional broad `except` with a re-raise) | False alarms under temptation; whether the reviewer verifies | ~10–20% |

### 3.2 Coverage for the first 40 cases

| Track | Cases | Example bug classes |
|---|---|---|
| Python | 10 | mutable defaults, off-by-one, wrong exception handling, resource leaks, missing auth check |
| TypeScript / React | 10 | stale closure in `useEffect`, missing deps, unhandled promise, wrong key, XSS via `dangerouslySetInnerHTML` |
| ML / data | 10 | scaler fit before split, SMOTE before CV, group leakage, chained assignment, `(n,1)` vs `(n,)` broadcast, double softmax |
| Mixed (Go / Java / SQL) | 10 | ignored `err`, goroutine leak, N+1, SQL injection, `Optional.get()` without check |

### 3.3 Case format

> **Implemented (M1):** metadata is `case.json` (not YAML: the package has no dependencies), cases keep an `after/` copy, and answer-key locations are anchors + spans. The current format is in [ADDING_A_CASE.md](ADDING_A_CASE.md); the sketch below is the original proposal.

```
cases/python/py-007/
  case.yaml        # metadata
  base/            # the code before the change (a small, self-contained project)
  change.patch     # the change under review (applied on top of base/)
  truth.json       # the answer key
  NOTES.md         # optional: why the bug is a bug, source credit
```

`case.yaml`
```yaml
id: py-007
kind: planted            # planted | real | clean | decoy
track: python
title: "Add retry to payment client"
source: original         # original | <repo url>@<commit>  (credited in NOTES.md)
license: MIT             # license of base/ code
added: 2026-11-10
```

`truth.json`
```json
{
  "bugs": [
    {
      "id": "b1",
      "file": "payments/client.py",
      "lines": [41, 47],
      "class": "error-handling",
      "severity": "blocking",
      "summary": "Retries on every exception, including 4xx, so a declined card is charged up to 3 times.",
      "trigger": "Gateway returns 402 on the first attempt"
    }
  ],
  "known_ok": [
    { "file": "payments/client.py", "lines": [20, 24], "note": "Bare re-raise is intentional (decoy)." }
  ]
}
```

Clean and decoy cases have `"bugs": []`. `known_ok` lists the tempting spots, so the grader
can tell a decoy hit apart from an ordinary false alarm.

### 3.4 Where cases come from

- **Planted (M1–M2):** written by us. Each one gets a second check (a second person, or a separate
  model pass) confirming the bug is real, reachable, and the *only* bug in the change.
- **Real (M3):** pick a bug-fix commit in an MIT/Apache/BSD repo → `git blame` the fixed lines to find
  the commit that introduced the bug (the SZZ method) → that introducing commit is the change under review.
  Candidate sources: BugsInPy (Python), Defects4J (Java), plus hand-picked fixes. Check each source's
  license before including it.
- **Contamination:** real bugs from popular repos may be in the model's training data.
  Report **real** and **planted** scores separately, always.

### 3.5 Quality gates for a case (enforced by `reviewbench check`)

- `change.patch` applies cleanly to `base/`.
- Every `truth.json` line range exists in the post-change file.
- `case.yaml` fields are valid; license is set; `source` is credited.
- Size limits: change ≤ 300 changed lines, `base/` ≤ 2,000 lines (keeps cost bounded).

---

## 4. Reviewers ("subjects")

A subject is one reviewer setup, declared in YAML:

```yaml
# subjects/code-review-skill.yaml
name: code-review-skill
kind: skill
source: https://github.com/awesome-skills/code-review-skill
commit: 4850184            # always pinned; recorded in results
prompt: "Review the uncommitted changes in this repository. Report any bugs you find, with file and line."
credit: "awesome-skills/code-review-skill (MIT)"
```

First subjects:

| Subject | What it is |
|---|---|
| `baseline` | Claude with no skill, same prompt |
| `code-review-skill` | upstream at a pinned commit |
| `code-review-skill-pr34` | upstream + the verify-step change (PR #34 branch commit) |
| `code-review-skill-pr37` | upstream + the ML guide (PR #37 branch commit) |
| `builtin-code-review` | Claude Code's built-in `/code-review` |

The **model is pinned** (e.g. `claude-sonnet-5-5`) for every subject in a run, and recorded.
Changing models is a different experiment.

Skills are **fetched at the pinned commit at run time**, not copied into this repo, so their
work stays theirs and every result points to an exact version.

---

## 5. Pipeline

```
 case + subject
      │
  ① build ──► fresh temp workspace: git repo of base/, change.patch applied as uncommitted changes,
      │        skill installed (or not), nothing else
  ② run ────► claude -p "<prompt>" in that workspace → raw review text + cost/tokens/time
      │
  ③ extract ► same extractor for every subject → findings.json (fixed schema)
      │
  ④ grade ──► location match (code) → same-bug judgment (AI judge) → grades.json
      │
  ⑤ report ─► summary table + per-case details + plots
```

### ① Build (isolation)

- Each run gets a new temp directory: `base/` copied in, `git init` + commit, then `change.patch`
  applied **uncommitted**, so `git diff` shows exactly the change. All subjects see identical files.
- Isolation from your machine's setup: Claude Code runs with `--bare`, which skips hooks, plugins,
  auto-memory and CLAUDE.md discovery, plus `--strict-mcp-config` (no MCP servers) and
  `--no-session-persistence`.
- The skill under test is provided explicitly (as a plugin dir via `--plugin-dir`, or placed in the
  workspace's `.claude/skills/`, whichever M0 proves isolates correctly).
  **M0 result:** `.claude/skills/` (excluded from git) with `flags` mode and the normal login isolates
  cleanly; see [spikes/m0/RESULTS.md](../spikes/m0/RESULTS.md). Each skill subject runs in two
  conditions — **natural** (plain prompt) and **invoked** (`/<skill> …`) — because in M0 the skill
  did not trigger by itself.
- `--bare` authenticates **only** with `ANTHROPIC_API_KEY` (not the Claude subscription login).
  Runs are billed to that API key. The key is read from your environment; it is never stored in the repo.

### ② Run

```bash
claude -p "$PROMPT" --bare --output-format json \
  --model "$MODEL" --strict-mcp-config --no-session-persistence \
  --allowedTools "Read,Grep,Glob,Bash(git diff:*),Bash(git log:*),Bash(git show:*)" \
  --disallowedTools "Edit,Write,NotebookEdit,WebFetch,WebSearch" \
  --max-budget-usd 1.00
```

- Read-only tools only; no network; reviewers can't edit the case.
- `--max-budget-usd` caps a runaway run.
- Saved per run: raw output, `total_cost_usd`, token usage, duration, number of turns, exit status,
  CLI version, model id, subject commit.

### ③ Extract

A fixed extractor prompt + `--json-schema` turns each raw review into:

```json
{ "findings": [
  { "file": "payments/client.py", "line_start": 41, "line_end": 47,
    "severity": "blocking", "summary": "...", "evidence": "..." } ] }
```

- Severity is normalized to `blocking | important | minor | note` (each subject's own labels map here).
- The extractor never adds or judges findings; it only restructures. 10% of extractions are hand-checked.

### ④ Grade

1. **Location match (code):** a finding *hits* a truth bug if same file and line ranges overlap
   (±3 lines tolerance).
2. **Same-bug check (AI judge):** for each location hit, the judge sees the truth `summary` +
   `trigger` and the finding, and answers `same_bug: yes/no`. A hit only counts if `yes`.
3. **Other findings:** every finding at `important` or above that doesn't match a truth bug is
   judged `valid_other | invalid | unsure`. `valid_other` findings are queued for a human. If a human
   confirms a real unplanned bug, the case's `truth.json` is updated and the case re-graded
   (and the change is logged).
4. **Judge calibration:** in M1, every grade is also hand-labeled. Agreement is reported
   (Cohen's κ). The AI judge is only trusted for later runs if κ ≥ 0.8; after that, 20% are
   hand-checked per run.

### ⑤ Report

Per subject, per track, per case kind:

| Metric | Definition |
|---|---|
| **Recall** | bug cases where ≥1 finding is a confirmed hit ÷ bug cases |
| **Precision** | confirmed hits ÷ all findings at `important`+ on bug cases (`valid_other` counts as correct) |
| **Clean pass rate** | clean + decoy cases with zero `important`+ findings ÷ clean + decoy cases |
| **Decoy trap rate** | decoy cases where a finding lands on a `known_ok` spot ÷ decoy cases |
| **Cost** | median $ / tokens / seconds per review |

- Each metric: mean over 3 runs, with a 95% bootstrap confidence interval over cases.
- Comparisons between two subjects are **paired** (same cases); report the difference with its interval.
  A difference whose interval crosses 0 is reported as "no clear difference".
- Output: `results/<run-id>/summary.md`, `summary.json`, per-case pages, and two plots
  (recall vs. clean-pass-rate scatter; cost per subject).

---

## 6. Repository layout

```
reviewbench/
  README.md
  docs/
    PLAN.md                 # this file
    METHOD.md               # (M2) final methodology, written for readers of results
    ADDING_A_CASE.md        # (M1) how to write and check a case
    ADDING_A_SUBJECT.md     # (M2)
  cases/<track>/<id>/       # see §3.3
  subjects/<name>.json      # see §4 (JSON, implemented in M1)
  prompts/
    extractor.md            # fixed extraction prompt
    judge.md                # fixed judge rubric
  reviewbench/              # Python package
    cli.py                  # `reviewbench check | run | grade | report`
    cases.py                # load + validate cases
    workspace.py            # ① build isolated workspaces
    runner.py               # ② call the Claude CLI, capture outputs
    extract.py              # ③
    grade.py                # ④ location match + judge calls
    report.py               # ⑤ metrics, bootstrap, tables, plots
    schema.py               # JSON schemas (findings, truth, results)
  results/<run-id>/
    config.json             # model, CLI version, subject commits, date
    raw/ findings/ grades/
    summary.md  summary.json
  tests/                    # unit tests for matching, metrics, case validation
  pyproject.toml
```

Python 3.11+, standard library only (M1). `pytest` for tests; plots deferred.

Commands:

```bash
reviewbench check                                     # validate all cases
reviewbench run --subjects baseline,code-review-skill --cases cases/python --runs 3
reviewbench grade results/2026-11-20-a
reviewbench report results/2026-11-20-a
```

Runs resume: a run that stops halfway continues from the last finished review.

---

## 7. Milestones

| # | Milestone | Scope | Done when |
|---|---|---|---|
| **M0** | Isolation spike | Prove a `--bare` run sees *only* the intended skill (probe prompt: "list every skill and command you can use"); measure the cost of one review | Probe output saved for each subject; cost per review known |
| **M1** | Pilot | 10 cases (Python + ML; planted, clean, decoy) × 2 subjects (baseline, code-review-skill) × 3 runs = 60 reviews. Full pipeline end to end. **Every grade hand-labeled.** | First summary table; judge agreement κ measured; extractor checked. **Status 2026-11-07:** 90 reviews run (3 subjects incl. natural/invoked), all at ceiling; skill self-triggered 0/30; grader fixed; hand labels pending — see [results/m1-pilot/README.md](../results/m1-pilot/README.md) |
| **M2** | First real result | 40 cases × 5 subjects × 3 runs = 600 reviews | Results posted on code-review-skill#32; PR #34 / #37 effects measured; METHOD.md written **Status 2026-11-07:** difficulty pilot: 5 harder cross-file cases, baseline still 100% recall (15 reviews); small cases can't create difficulty, so real bugs at full-repo scale come next — see [results/m2-hard-pilot/README.md](../results/m2-hard-pilot/README.md) |
| **M3** | Real bugs | 10–20 real (SZZ) cases; real vs planted reported separately | Contamination comparison in the report |
| **M4** | Launch | Make repo public, ADDING_A_SUBJECT.md, results page | Public repo + launch post |

Rough timeline: M0 2 days · M1 1 week · M2 1–2 weeks · M3 1 week · M4 a few days.

**Before launch:** share results with the code-review-skill maintainers on #32 first, so they can
respond before anything is posted publicly.

---

## 8. Cost control

- Measure in M0, then estimate: `cases × subjects × runs × cost per review` + extraction + judging.
- Per-review cap with `--max-budget-usd`; a whole-run cap in the CLI (`--budget`) that stops cleanly.
- Pilot small (60 reviews) before the 600-review run.
- Cache: a (case, subject commit, model, prompt) combination that already has 3 runs is never re-run.

---

## 9. Risks and how they're handled

| Risk | Handling |
|---|---|
| Training-data contamination | Most v1 cases are planted; real cases reported separately |
| Lenient or biased AI judge | Location match is done by code; judge calibrated against hand labels (κ ≥ 0.8) and spot-checked every run |
| Unplanned real bugs counted as false alarms | `valid_other` category + human confirmation + truth update log |
| Isolation leaks (user skills, memory, hooks) | `--bare` + probe check in M0 and a probe run at the start of every run |
| Small sample → noisy conclusions | 3 runs, confidence intervals, paired comparisons; claims only where intervals exclude 0 |
| Reviewer can't verify by running code (v1 is read-only) | Stated as a limit. v2: optional sandboxed condition (container, no network) allowing `pytest` |
| Case licensing | Every case records license + source; only permissive licenses |
| Unfair to a subject (bad prompt, wrong install) | Subjects use their documented install and usage; maintainers can review their subject file |

---

## 10. Credit

- README credits **awesome-skills/code-review-skill** (MIT) and links issue #32 as the origin.
- Every subject in every results table is named with its source link and pinned commit.
- Skills are fetched at run time, not vendored. If a file is ever copied in, its LICENSE and
  copyright notice go with it.
- Real-bug cases credit their source repository and commits in `NOTES.md`.
- Planted cases inspired by a specific guide example cite that guide.

---

## 11. Open decisions

1. **Model for runs:** Sonnet (cheaper, more runs) vs Opus (stronger reviewer). Proposal: Sonnet for M1–M2, one Opus comparison later.
2. **License for ReviewBench at launch:** MIT for code, CC BY 4.0 for cases.
3. **Judge model:** same family as the reviewer (simpler) or different (less self-preference). Proposal: Claude for M1, measure agreement, revisit if κ is low.
4. **Where `builtin-code-review` fits:** ~~M0 decides~~ M0 showed the built-in skills are present in every run (they ship with Claude Code). `builtin-code-review` is run as an **invoked** subject (`/code-review`); every other run logs whether it was triggered.
