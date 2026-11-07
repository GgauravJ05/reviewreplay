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

## Ground rules

- Never commit API keys, tokens or private code. Reviews run with your own credentials, set in
  your own shell (`ANTHROPIC_API_KEY` or `REVIEWBENCH_OAUTH_TOKEN`).
- Cases come only from code whose licence allows it; credit the source in the case's `NOTES.md`.
- Keep numbers honest: every claim in a README or post must trace to files under `results/`.
- One change per pull request, with a short description of why.

By contributing you agree that your contribution is licensed under the MIT licence.
