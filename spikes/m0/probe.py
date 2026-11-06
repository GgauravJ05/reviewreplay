"""M0 isolation spike: does a headless Claude Code run see ONLY the skill under test?

For each (mode, skill-install) setup this script:
  1. builds a fresh temp workspace (tiny git repo + optional skill install),
  2. runs `claude -p` with an inventory prompt (or a real review prompt with --review),
  3. scans the answer for "canaries" — names that only exist in the host machine's own
     setup (user skills, plugins, memory) — and saves everything under spikes/m0/out/.

Modes
  bare   `--bare`: skips hooks, plugins, memory, CLAUDE.md. Needs ANTHROPIC_API_KEY.
  flags  normal login, isolated with flags only: --setting-sources project,
         --strict-mcp-config, --no-session-persistence.

Skill installs
  none       no skill (baseline)
  project    skill copied to <workspace>/.claude/skills/<name>/
  plugin     skill wrapped as a plugin and passed with --plugin-dir

Usage
  python spikes/m0/probe.py --mode flags --skill none
  python spikes/m0/probe.py --mode flags --skill project --review
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
TOY = HERE / "toy_case"

SKILL_NAME = "code-review-skill"
SKILL_REPO = Path(os.environ.get("RB_SKILL_REPO", HERE.parents[2] / "code-review-skill"))
SKILL_COMMIT = os.environ.get("RB_SKILL_COMMIT", "4850184")
MODEL = os.environ.get("RB_MODEL", "claude-sonnet-5-5")

# Names that exist only in the host's own setup. Seeing any of them in a probe answer = leak.
CANARIES = [
    # user skills in ~/.claude/skills
    "impeccable", "archify", "design-taste-frontend", "frontend-slides", "brag-slim", "apple",
    # plugin namespaces
    "ecc:", "hyperframes", "diagram-design", "engineering:", "anthropic-skills",
    # auto-memory / user CLAUDE.md content
    "Kokoro", "Decklume", "ResQPulse", "Commitfolio",
]

INVENTORY_PROMPT = (
    "Do not use any tools. Report your environment as JSON with exactly these keys: "
    '"skills" (every skill you could invoke, exact names), '
    '"slash_commands" (every slash command available), '
    '"instructions" (one-line summary of any CLAUDE.md, memory, or project instructions you were given, or []), '
    '"extra_tools" (any tools beyond the standard file/shell tools, e.g. MCP tools). '
    "Output only the JSON."
)
REVIEW_PROMPT = (
    "Review the uncommitted changes in this repository. "
    "Report any bugs you find, with file and line."
)
READ_ONLY_TOOLS = "Read,Grep,Glob,Bash(git diff:*),Bash(git log:*),Bash(git show:*)"
BLOCKED_TOOLS = "Edit,Write,NotebookEdit,WebFetch,WebSearch"


def clean_env(mode: str) -> dict[str, str]:
    """Drop every variable that would tie the child run to the parent Claude session."""
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("CLAUDE", "ANTHROPIC_", "MCP_"))}
    if mode == "bare":
        key = os.environ.get("ANTHROPIC_API_KEY")
        if key:
            env["ANTHROPIC_API_KEY"] = key
    return env


def export_skill(dest: Path) -> None:
    """Copy the skill at the pinned commit (git archive: no network, exact version)."""
    dest.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(
        ["git", "-C", str(SKILL_REPO), "archive", SKILL_COMMIT],
        check=True, capture_output=True,
    ).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True)
    for junk in (".hive", ".github", "index.html", "index.en.html", ".nojekyll"):
        p = dest / junk
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()


def build_workspace(root: Path, skill: str) -> list[str]:
    """Create the workspace; return extra CLI args needed for this skill install."""
    ws = root / "ws"
    shutil.copytree(TOY / "base", ws)
    git = ["git", "-C", str(ws), "-c", "user.name=rb", "-c", "user.email=rb@example.invalid"]
    subprocess.run(git[:3] + ["init", "-q", "-b", "main"], check=True)
    subprocess.run(git + ["add", "-A"], check=True)
    subprocess.run(git + ["commit", "-q", "-m", "base"], check=True)
    subprocess.run(git[:3] + ["apply", str(TOY / "change.patch")], check=True)
    # Keep an installed skill out of `git status`, so "review the uncommitted changes"
    # means the case's change only, never the skill's own files.
    (ws / ".git" / "info" / "exclude").write_text(".claude/\n")

    if skill == "project":
        export_skill(ws / ".claude" / "skills" / SKILL_NAME)
        return []
    if skill == "plugin":
        plugin = root / "plugin"
        (plugin / ".claude-plugin").mkdir(parents=True)
        (plugin / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"name": SKILL_NAME, "version": SKILL_COMMIT,
                        "description": "code-review-skill (awesome-skills, MIT) for ReviewBench"}))
        export_skill(plugin / "skills" / SKILL_NAME)
        return ["--plugin-dir", str(plugin)]
    return []


def run(mode: str, skill: str, review: bool, budget: float, timeout: int,
        invoke: bool = False) -> dict:
    tag = f"{mode}-{skill}-{'review' if review else 'inventory'}{'-invoked' if invoke else ''}"
    prompt = REVIEW_PROMPT if review else INVENTORY_PROMPT
    if invoke:  # call the skill explicitly instead of relying on it to trigger by itself
        prompt = f"/{SKILL_NAME} {prompt}"
    with tempfile.TemporaryDirectory(prefix="rb-m0-") as tmp:
        root = Path(tmp)
        extra = build_workspace(root, skill)
        # stream-json logs every tool call, so we can see which skill (if any) a review invoked
        cmd = ["claude", "-p", prompt,
               "--output-format", "stream-json", "--verbose", "--model", MODEL,
               "--strict-mcp-config", "--no-session-persistence",
               "--allowedTools", READ_ONLY_TOOLS, "--disallowedTools", BLOCKED_TOOLS,
               "--max-budget-usd", str(budget), *extra]
        cmd += ["--bare"] if mode == "bare" else ["--setting-sources", "project"]

        started = time.monotonic()
        proc = subprocess.run(cmd, cwd=root / "ws", env=clean_env(mode),
                              capture_output=True, text=True, timeout=timeout)
        elapsed = round(time.monotonic() - started, 1)

    payload: dict = {}
    tool_calls: list[str] = []
    skills_invoked: list[str] = []
    for line in proc.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "result":
            payload = event
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    tool_calls.append(block.get("name", "?"))
                    if block.get("name") == "Skill":
                        skills_invoked.append(str(block.get("input", {}).get("skill", "?")))
    if not payload:
        payload = {"unparsed_stdout": proc.stdout[-4000:]}
    answer = str(payload.get("result", payload))
    leaks = sorted({c for c in CANARIES if c.lower() in answer.lower()})
    skill_seen = SKILL_NAME in answer

    record = {
        "tag": tag, "mode": mode, "skill": skill, "review": review,
        "when": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": MODEL, "skill_commit": SKILL_COMMIT,
        "exit_code": proc.returncode, "seconds": elapsed,
        "cost_usd": payload.get("total_cost_usd"), "usage": payload.get("usage"),
        "num_turns": payload.get("num_turns"), "is_error": payload.get("is_error"),
        "leaked_canaries": leaks, "skill_under_test_visible": skill_seen,
        "skills_invoked": skills_invoked, "tool_calls": tool_calls,
        "answer": answer, "stderr_tail": proc.stderr[-2000:],
        "prompt": prompt,
        "cmd": [c if c != prompt else "<prompt>" for c in cmd],
    }
    OUT.mkdir(exist_ok=True)
    (OUT / f"{tag}.json").write_text(json.dumps(record, indent=2))
    return record


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["bare", "flags"], required=True)
    ap.add_argument("--skill", choices=["none", "project", "plugin"], required=True)
    ap.add_argument("--review", action="store_true", help="run a real review instead of the inventory probe")
    ap.add_argument("--budget", type=float, default=0.50, help="--max-budget-usd per run")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--invoke", action="store_true", help="prefix the prompt with /code-review-skill")
    a = ap.parse_args()
    r = run(a.mode, a.skill, a.review, a.budget, a.timeout, a.invoke)
    print(json.dumps({k: r[k] for k in ("tag", "exit_code", "is_error", "seconds", "cost_usd",
                                        "num_turns", "leaked_canaries", "skill_under_test_visible",
                                        "skills_invoked")}))


if __name__ == "__main__":
    main()
