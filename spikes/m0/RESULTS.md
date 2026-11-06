# M0 — Isolation spike: results

Goal (from [docs/PLAN.md](../../docs/PLAN.md) §7): prove a headless review run sees **only** the
skill under test, and measure what one review costs.

Status (2026-11-06): **tooling done; live probes blocked on authentication.**

## What's here

| File | Purpose |
|---|---|
| `probe.py` | Builds an isolated workspace, runs `claude -p`, scans the answer for leaks, saves a record to `out/` |
| `toy_case/` | One tiny case: `base/cart.py`, `change.patch` (planted mutable-default bug + a correct decoy), `truth.json` |
| `out/*.json` | Saved run records |

Setups the probe tests:

| Mode | Isolation | Auth |
|---|---|---|
| `bare` | `--bare` (no hooks, plugins, memory, CLAUDE.md) + `--strict-mcp-config` | `ANTHROPIC_API_KEY` only |
| `flags` | `--setting-sources project` + `--strict-mcp-config` + `--no-session-persistence` | normal `claude` login |

| Skill install | How |
|---|---|
| `none` | nothing (baseline) |
| `project` | copied to `<workspace>/.claude/skills/code-review-skill/`, hidden from `git status` |
| `plugin` | wrapped as a plugin, passed with `--plugin-dir` |

The skill is exported from the local code-review-skill clone at pinned commit `4850184` with
`git archive` (no network); `.hive/`, `.github/` and the landing pages are left out.

**Leak detection:** the probe asks the model to list its skills, commands, instructions and extra
tools, then checks the answer for names that exist only on the host machine (user skills such as
`impeccable` and `archify`, plugin namespaces such as `ecc:` and `hyperframes`, and memory topics
such as `Kokoro`). Any hit means the setup is not isolated.

**Environment scrubbing:** every `CLAUDE*`, `ANTHROPIC_*` and `MCP_*` variable is removed before
launching the child run. The host session exports ~35 of these (session tokens, a messaging socket,
`CLAUDE_CODE_SIMPLE`), and inheriting them would tie the test run to the host session.

## Results so far

| Check | Result |
|---|---|
| Workspace build: `none`, `project`, `plugin` | ✅ `git diff` shows exactly the case change; skill files present; `.hive` stripped |
| Installed skill hidden from `git status` | ✅ only `M cart.py` |
| Toy case patch applies; truth line numbers match | ✅ bug at `cart.py:19-22`, decoy at `25-29` |
| `bare` + no API key | ❌ as expected: exits in 0.9 s, $0, `Failed to authenticate` |
| `flags` + host login | ❌ `OAuth session expired and could not be refreshed`. The standalone CLI's stored login is expired; the desktop app's live login is not shared with child processes once the session variables are removed. |

## To unblock (pick one)

- **A. API key (planned path, cleanest isolation):** export `ANTHROPIC_API_KEY` in your own shell.
  Runs are billed to that key.
- **B. Subscription login:** run `claude` in a normal terminal and log in again (`/login`). This
  re-enables `flags` mode. Isolation must then be proven by the probes below, since `flags` mode
  still runs with your normal login.

## Remaining M0 runs

```bash
cd reviewbench
# isolation probes (cheap: no tools, one short answer each)
python3 spikes/m0/probe.py --mode bare  --skill none
python3 spikes/m0/probe.py --mode bare  --skill project
python3 spikes/m0/probe.py --mode bare  --skill plugin
python3 spikes/m0/probe.py --mode flags --skill none
python3 spikes/m0/probe.py --mode flags --skill project
python3 spikes/m0/probe.py --mode flags --skill plugin
# one real review per install, to measure cost and time
python3 spikes/m0/probe.py --mode <winner> --skill none    --review
python3 spikes/m0/probe.py --mode <winner> --skill project --review
```

M0 is done when: one mode shows **no leaked canaries** for `none`, shows `code-review-skill`
visible for at least one install method, and the two review runs give a cost per review.
