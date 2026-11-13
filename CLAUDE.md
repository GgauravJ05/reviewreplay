# ReviewReplay — notes for Claude

Read this before working in this repository. Task briefs for upcoming work are in
[docs/tasks/](docs/tasks/README.md); the checklist is [docs/TODO.md](docs/TODO.md).

## What this project is

ReviewReplay benchmarks AI code reviewers on real bugs from a repository's own history. It mines
fix commits, finds the commit that introduced each bug (SZZ: message reference + `git blame`),
replays that change in a clean copy of the full project, asks each reviewer to review it, and grades
the reviews (location gate ±3 lines, then an LLM judge) into recall, precision, false alarms and cost.

Author and maintainer: **Gaurav Jadhav** (GitHub `GgauravJ05`). The repo is public.

## Layout

| Path | What |
|---|---|
| `reviewreplay/` | The package. `cli.py` (commands), `cases.py` (case loading, export of real cases), `mine.py` (SZZ miner), `init.py` (draft answer keys), `runner.py` (run reviewers), `grade.py` (extract + judge), `report.py`, `compare.py`, `label.py`, `claude.py` (headless `claude -p` calls) |
| `reviewreplay/prompts/` | Extractor and judge prompts |
| `reviewreplay/subjects/` | Reviewer definitions (`baseline`, `code-review-skill-*`, `examples/` for Codex, Gemini, `/code-review`) |
| `cases/` | `python/`, `ml/` planted cases; `real/real-NNN/` real bugs (`case.json`, `truth.json`, `NOTES.md`) |
| `results/<run>/` | Every run: `raw/`, `findings/`, `grades/`, `summary.md`, `README.md` with the write-up |
| `docs/` | `PLAN.md` (method), `ROADMAP.md` (phases), `TODO.md` (checklist), `ADDING_A_CASE.md`, `LAUNCH.md`, `tasks/` |
| `site/` | GitHub Pages site (deployed by `.github/workflows/pages.yml`) |
| `tests/` | `python3.13 -m pytest` (the default `python3` has no pytest here) |

## Commands

```bash
python3.13 -m pytest                       # tests
python3 -m reviewreplay check              # validate every case (exports real cases to ~/.cache/reviewreplay/)
python3 -m reviewreplay mine <repo-url> --since 2024-01-01 --limit 40 --json out.json
python3 -m reviewreplay run --out results/<name> --subjects baseline,code-review-skill-invoked --runs 3
python3 -m reviewreplay extract results/<name> && python3 -m reviewreplay grade results/<name>
python3 -m reviewreplay report results/<name>
python3 -m reviewreplay compare results/<a> results/<b>
```

## How work lands

- `main` is protected: branch → PR → one approval → squash merge. Branch names: `feat/…`, `fix/…`,
  `docs/…`, `case/real-NNN-<project>`, `results/<run>`.
- One change per PR; fill in `.github/pull_request_template.md`. Code and result runs go in separate commits.
- Commit as `git -c user.name=GgauravJ05 -c user.email=ggauravj5@gmail.com commit …`.
  **No `Co-Authored-By` trailers**; the author wants full credit.
- If several sessions share this folder, use a `git worktree` for your branch instead of switching
  branches in the shared checkout.

## Hard rules

- **Never handle API keys or tokens.** Reviews and grading run on the author's own `claude` login.
  Commands that spend model usage (`run`, `extract`, `grade`, `verify`, `init`) are given to the
  author to run in a plain terminal tab; don't ask for keys and don't borrow other credentials.
- **Never execute third-party code** from cases or cloned repos. Reviewers run read-only
  (`Read, Grep, Glob, git diff/log/show/status`).
- **Numbers must trace to `results/`.** Any figure in README, site, docs or posts must come from a
  committed run. When numbers change, update README, `site/`, and the relevant `results/*/README.md` together.
- **Credit [code-review-skill](https://github.com/awesome-skills/code-review-skill)** (MIT) wherever
  it is tested, with the pinned commit. It is fetched at run time, never vendored.
- **Cases only from permissively licensed repos**, credited in `NOTES.md`, answer key checked
  against the upstream fix by reading it.
- Don't publish to PyPI, post publicly, or change repo settings without the author's go-ahead.
- Write plain, short prose in docs: active voice, concrete numbers, no hype.
