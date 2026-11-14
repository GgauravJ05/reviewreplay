"""The GitHub Action's pull-request comment, and how CI credentials reach `claude`."""
from __future__ import annotations

from reviewreplay import ci, claude

SUMMARY = """# ReviewReplay results — `ci`

Model `claude-sonnet-5-5` · 1 runs per case · 2 cases

| Subject | Reviews | Recall | Precision |
|---|---|---|---|
| baseline | 2 | 50% [0%–100%] | 80% [60%–100%] |
| ours | 2 | 100% [100%–100%] | 90% [80%–100%] |

## Paired difference vs. baseline

| Subject | Recall Δ | Clean pass Δ | Precision Δ |
|---|---|---|---|
| ours | +50 pts [+0, +100] | — | +10 pts [+0, +20] |

## Per case

| Subject | Case | Kind | Recall |
|---|---|---|---|
| baseline | c1 | real | 100% |

## Subjects

- **ours**. Prompt: `secret sauce`
"""


def test_scorecard_keeps_headline_and_paired_difference_only():
    text = ci.comment(summary_md=SUMMARY, run_url="https://example.invalid/run/1")
    assert text.startswith(ci.MARKER)
    assert "| ours | 2 | 100%" in text and "## Paired difference" in text
    assert "## Per case" not in text and "secret sauce" not in text and "# ReviewReplay results" not in text
    assert "[Workflow run and full results](https://example.invalid/run/1)" in text


def test_dry_run_comment_says_nothing_was_spent():
    text = ci.comment(dry_run="2 case(s) x 1 reviewer(s) x 1 run(s) = 2 review(s)\n")
    assert "Dry run: nothing was reviewed and nothing was spent." in text
    assert "```\n2 case(s) x 1 reviewer(s)" in text


def test_missing_summary_points_to_the_log():
    assert "Check the workflow log" in ci.comment()


def test_long_comment_is_truncated_under_github_limit():
    rows = "\n".join(f"| row {i} | x |" for i in range(20_000))
    text = ci.comment(summary_md=SUMMARY.replace("## Per case", rows + "\n\n## Per case"))
    assert len(text) <= ci.MAX_CHARS and text.endswith("(truncated)\n")


def test_ci_api_key_reaches_claude_only_under_its_own_name(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "host-key")          # a host setting must not leak in
    monkeypatch.setenv(claude.API_KEY_VAR, "ci-key")
    env = claude.clean_env()
    assert env["ANTHROPIC_API_KEY"] == "ci-key"
    assert claude.API_KEY_VAR not in env
    assert claude.auth_mode() == "api key"


def test_no_ci_key_means_no_anthropic_variables(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "host-key")
    monkeypatch.delenv(claude.API_KEY_VAR, raising=False)
    monkeypatch.delenv(claude.TOKEN_VAR, raising=False)
    assert not any(k.startswith("ANTHROPIC_") for k in claude.clean_env())
