"""The pull-request comment for the GitHub Action: the scorecard from a run's summary.md, or a
dry run's estimate. Pure text in, text out, so it is tested without GitHub."""
from __future__ import annotations

from pathlib import Path

MARKER = "<!-- reviewreplay-scorecard -->"
MAX_CHARS = 60_000          # GitHub rejects comments over 65,536 characters
KEEP = ("## Paired difference",)
DROP = ("## Per case", "## Subjects")


def scorecard(summary_md: str) -> str:
    """The headline table and the paired difference; per-case rows and subject prompts are left out."""
    out, skip = [], False
    for line in summary_md.splitlines():
        if line.startswith("## "):
            skip = line.startswith(DROP) and not line.startswith(KEEP)
        if line.startswith("# "):
            continue
        if not skip:
            out.append(line)
    return "\n".join(out).strip()


def comment(*, summary_md: str | None = None, dry_run: str | None = None,
            run_url: str | None = None) -> str:
    parts = [MARKER, "### ReviewReplay scorecard", ""]
    if dry_run is not None:
        parts += ["Dry run: nothing was reviewed and nothing was spent.", "", "```",
                  dry_run.strip(), "```"]
    elif summary_md:
        parts.append(scorecard(summary_md))
    else:
        parts.append("No results: the run produced no summary. Check the workflow log.")
    if run_url:
        parts += ["", f"[Workflow run and full results]({run_url})"]
    text = "\n".join(parts) + "\n"
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS - 40].rsplit("\n", 1)[0] + "\n\n(truncated)\n"
    return text


def write_comment(out: Path, *, run_dir: Path | None = None, dry_run_file: Path | None = None,
                  run_url: str | None = None) -> Path:
    summary = run_dir / "summary.md" if run_dir else None
    text = comment(summary_md=summary.read_text() if summary and summary.exists() else None,
                   dry_run=dry_run_file.read_text() if dry_run_file else None, run_url=run_url)
    out.write_text(text)
    return out
