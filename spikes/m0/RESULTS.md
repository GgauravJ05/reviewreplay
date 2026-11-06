# M0 — Isolation spike: results

Goal (from [docs/PLAN.md](../../docs/PLAN.md) §7): prove a headless review run sees **only** the
skill under test, and measure what one review costs.

Status (2026-11-06): **done.** Decisions are at the bottom.

## What's here

| File | Purpose |
|---|---|
| `probe.py` | Builds an isolated workspace, runs `claude -p` (stream-json), records tool calls and skills invoked, scans the answer for leaks, saves a record to `out/` |
| `toy_case/` | One tiny case: `base/cart.py`, `change.patch` (planted mutable-default bug + a correct decoy), `truth.json` |
| `out/*.json` | One record per run: prompt, command, answer, tool calls, cost, tokens, time |

Setups tested:

| Mode | Isolation | Auth |
|---|---|---|
| `bare` | `--bare` + `--strict-mcp-config` | `ANTHROPIC_API_KEY` only |
| `flags` | `--setting-sources project` + `--strict-mcp-config` + `--no-session-persistence` | normal `claude` login |

| Skill install | How |
|---|---|
| `none` | nothing (baseline) |
| `project` | copied to `<workspace>/.claude/skills/code-review-skill/`, hidden from `git status` |
| `plugin` | wrapped as a plugin, passed with `--plugin-dir` |

The skill comes from the local code-review-skill clone at pinned commit `4850184` via `git archive`
(no network); `.hive/`, `.github/` and the landing pages are left out. Every `CLAUDE*`, `ANTHROPIC_*`
and `MCP_*` variable is removed before launching a run, so the run can't attach to the host session.

**Leak detection:** the inventory probe asks the model to list its skills, commands, instructions and
extra tools. The answer is checked for names that exist only on the host machine (user skills like
`impeccable`, plugin namespaces like `ecc:`, memory topics like `Kokoro`). Answers were also read in full.

## Results

All runs: model `claude-sonnet-5-5`, Claude Code 2.1.309, subscription login. `cost` is the CLI's
API-equivalent estimate; on a subscription it counts against usage limits, not money.

| Run | Exit | Time | Est. cost | Leaks | Notes |
|---|---|---|---|---|---|
| `bare` · none · inventory | 1 | 0.9 s | $0 | — | No API key → refuses to start, as expected |
| `flags` · none · inventory | 0 | 7.3 s | $0.069 | **none** | Sees only Claude Code's built-in skills; no user skills, plugins, memory or CLAUDE.md |
| `flags` · project · inventory | 0 | 9.2 s | $0.031 | **none** | `code-review-skill` listed |
| `flags` · plugin · inventory | 0 | 7.7 s | $0.031 | **none** | listed as `code-review-skill:code-review-skill` |
| `flags` · none · review | 0 | 14.8 s | $0.031 | none | ✅ found the bug at `cart.py:19`; decoy correctly judged fine |
| `flags` · project · review | 0 | 15.8 s | $0.033 | none | ✅ same result; **skill never invoked** (no `Skill` call, no extra tokens) |
| `flags` · project · review, `/code-review-skill` | 0 | 15.2 s | $0.054 | none | ✅ same result in the skill's format (`🔴 [blocking]`); +~5k prompt tokens = skill loaded |

## Findings

1. **`flags` mode isolates well enough.** With a normal login and only flags, no user-specific
   skill, plugin, MCP server, memory or CLAUDE.md reached the run. `--bare` (API key) isn't needed
   for the pilot.
2. **Claude Code's built-in skills are always present** (`code-review`, `security-review`, `simplify`,
   …). They're part of the product, not the host's setup, so they stay; but the built-in
   `code-review` can compete with the skill under test. Every run must log which skills were invoked.
3. **The skill did not trigger by itself.** With code-review-skill installed and a plain
   "review the uncommitted changes" prompt, Claude reviewed without loading it. Invoked explicitly
   (`/code-review-skill …`), it loaded (+~5k tokens, its severity format in the answer).
   One run is not a rate, but it changes the design: "is the skill installed?" and "is the skill
   used?" are different questions, so subjects need both conditions (see decisions).
   This is also relevant to issue #32 (impact) and #35 (trigger description).
4. **Detecting skill use:** a skill that triggers by itself shows up as a `Skill` tool call in
   stream-json. An explicit `/skill` call does not; for those, the prompt token jump and the run's
   prompt are the record.
5. **Cost:** a toy review takes ~15 s and ~$0.03 (no skill) to ~$0.05 (skill loaded), estimated.
   Real cases are 5–20× larger, so expect roughly $0.10–0.50 per review. M1's 60 reviews ≈ $6–30
   API-equivalent; on a subscription this is usage, not a bill.
6. **The toy case is too easy:** the baseline found the bug and handled the decoy. M1 cases must be
   harder (bugs that need cross-file reasoning, subtler decoys) or every subject will score 100%.

## Decisions for M1

| Decision | Choice |
|---|---|
| Auth / isolation | `flags` mode with the subscription login; `--bare` + API key kept as an option for public, reproducible runs |
| Skill install | `project` (`.claude/skills/<name>/`, excluded from git) — simplest name, no plugin wrapper |
| Trigger conditions | Each skill subject runs twice: **natural** (plain prompt; measures whether it's used) and **invoked** (`/<skill> …`; measures what it does when used) |
| Logging | stream-json for every run; record tool calls, `Skill` invocations, and token usage |
| Case difficulty | No single-function textbook bugs; aim for bugs a careful reader needs the surrounding code to see |

## Re-running

```bash
cd reviewbench
python3 spikes/m0/probe.py --mode flags --skill none
python3 spikes/m0/probe.py --mode flags --skill project --review
python3 spikes/m0/probe.py --mode flags --skill project --review --invoke
```

Requires a logged-in `claude` CLI (`claude auth status` → `"loggedIn": true`).
