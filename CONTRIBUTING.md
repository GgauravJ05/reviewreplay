# Contributing to ReviewReplay

ReviewReplay is built in public, and early. The most useful contributions right now:

- **A real bug as a case.** A fix commit in a public, permissively licensed repository, the commit
  that introduced the bug, and an answer key. See [docs/ADDING_A_CASE.md](docs/ADDING_A_CASE.md),
  or run `reviewreplay init` on a repository and open a pull request with the drafts you checked.
- **A reviewer adapter.** Any tool that prints a review can be a subject: see
  `reviewreplay/subjects/examples/`. Reviewers must run read-only.
- **A second opinion on a grade.** If you think a finding was graded wrongly, open an issue with
  the case, run and finding; `reviewreplay label` writes a hand-label sheet.
- **Bugs and rough edges** in the CLI.

## Development

```bash
git clone https://github.com/GgauravJ05/reviewreplay && cd reviewreplay
python3 -m pip install -e .
python3 -m pip install pytest
python3 -m pytest
```

No runtime dependencies beyond the Python standard library, git and the reviewer CLIs you test.

## How pull requests work here

`main` is protected, so every change from a contributor goes through a pull request:

1. **Open an issue first** for anything bigger than a small fix or a new case, so we agree on the
   approach before you spend time on it.
2. **Fork, then branch** from `main` (`case/real-013-rich`, `fix/grade-line-gate`, `docs/...`).
3. **One change per pull request**, with a title that says what it does. Fill in the template.
4. **Tests must pass.** The `Tests` check runs on every pull request. For a first-time
   contributor, the maintainer approves the run first; that's a safety rule for forks, not a
   judgement on you.
5. **One maintainer review** is required, and every review conversation must be resolved. New
   commits after an approval need a fresh look.
6. **Keep it up to date with `main`.** Use the "Update branch" button or rebase; please don't
   merge `main` into your branch repeatedly.
7. **Squash merge only.** Each pull request lands as one commit on `main`, titled after the pull
   request, so history stays readable.

Pull requests that change several unrelated things, skip the template, or add numbers without
results behind them will be asked to split or fix before review.

## Ground rules

- Never commit API keys, tokens or private code. Reviews run with your own credentials, set in
  your own shell (`ANTHROPIC_API_KEY` or `REVIEWBENCH_OAUTH_TOKEN`).
- Cases come only from code whose licence allows it; credit the source in the case's `NOTES.md`.
- Keep numbers honest: every claim in a README or post must trace to files under `results/`.
- One change per pull request, with a short description of why.

By contributing you agree that your contribution is licensed under the MIT licence.
