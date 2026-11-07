"""Run the Claude Code CLI headless, isolated from the host machine's setup.

Isolation (proven in spikes/m0): the normal `claude` login plus
  --setting-sources project   no user settings → no user plugins, hooks, or memory
  --strict-mcp-config         no MCP servers
  --no-session-persistence    nothing written to session history
and every CLAUDE*/ANTHROPIC_*/MCP_* environment variable removed, so a run started from
inside a Claude session can't attach to it.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

DEFAULT_MODEL = os.environ.get("RB_MODEL", "claude-sonnet-5-5")
ISOLATION = ["--setting-sources", "project", "--strict-mcp-config", "--no-session-persistence"]


TOKEN_VAR = "REVIEWBENCH_OAUTH_TOKEN"   # from `claude setup-token`; set in your own shell
FATAL_MARKERS = ("hit your session limit", "hit your usage limit", "Failed to authenticate",
                 "OAuth session expired", "Invalid API key", "rate_limit")


class AccountError(RuntimeError):
    """Usage limit or login problem: retrying now won't help, so stop the whole run."""


def clean_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("CLAUDE", "ANTHROPIC_", "MCP_"))}
    # A long-lived token keeps test runs independent of the desktop app's login, which
    # refreshes (and invalidates) the shared keychain login. Never logged or written to disk.
    token = os.environ.get(TOKEN_VAR)
    if token:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = token
    env.pop(TOKEN_VAR, None)
    return env


def auth_mode() -> str:
    return "setup-token" if os.environ.get(TOKEN_VAR) else "keychain login"


def check_fatal(text: str) -> None:
    for marker in FATAL_MARKERS:
        if marker.lower() in (text or "").lower():
            raise AccountError(text.strip()[:200])


def cli_version() -> str:
    proc = subprocess.run(["claude", "--version"], capture_output=True, text=True, env=clean_env())
    return proc.stdout.strip()


def run_stream(prompt: str, cwd: Path, *, model: str = DEFAULT_MODEL, extra: list[str] | None = None,
               timeout: int = 900) -> dict:
    """Run a prompt with stream-json output. Returns result payload + tool calls + skills invoked."""
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
           "--model", model, *ISOLATION, *(extra or [])]
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=clean_env(), capture_output=True, text=True,
                              timeout=timeout)
        stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr, code = "timeout", -1
    seconds = round(time.monotonic() - started, 1)

    result: dict = {}
    tool_calls: list[dict] = []
    skills: list[str] = []
    for line in stdout.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "result":
            result = ev
        elif ev.get("type") == "assistant":
            for block in ev.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    inp = block.get("input", {})
                    tool_calls.append({"name": block.get("name"), "input": _short(inp)})
                    if block.get("name") == "Skill":
                        skills.append(str(inp.get("skill", "?")))
    if not result or result.get("is_error"):
        check_fatal(str(result.get("result", "")) + "\n" + stderr)
    return {
        "exit_code": code, "seconds": seconds,
        "is_error": result.get("is_error", True) if result else True,
        "answer": result.get("result", ""),
        "cost_usd": result.get("total_cost_usd"), "usage": result.get("usage"),
        "num_turns": result.get("num_turns"),
        "tool_calls": tool_calls, "skills_invoked": skills,
        "stderr_tail": stderr[-1500:],
    }


def run_json(prompt: str, schema: dict, cwd: Path, *, model: str = DEFAULT_MODEL,
             timeout: int = 300, retries: int = 2) -> dict:
    """Run a no-tools prompt that must return JSON matching `schema`."""
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--model", model, *ISOLATION,
           "--disable-slash-commands",
           "--disallowedTools", "Bash,Read,Edit,Write,Grep,Glob,WebFetch,WebSearch,Agent,NotebookEdit",
           "--json-schema", json.dumps(schema)]
    last = ""
    for _ in range(retries + 1):
        proc = subprocess.run(cmd, cwd=cwd, env=clean_env(), capture_output=True, text=True,
                              timeout=timeout)
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            last = proc.stdout[-500:] + proc.stderr[-500:]
            check_fatal(last)
            continue
        if payload.get("is_error"):
            check_fatal(str(payload.get("result", "")))
        out = payload.get("structured_output")
        if isinstance(out, dict):
            return {"data": out, "cost_usd": payload.get("total_cost_usd")}
        last = str(payload.get("result"))[:500]
    raise RuntimeError(f"structured call failed: {last}")


def _short(inp: dict) -> dict:
    return {k: (v[:200] if isinstance(v, str) else v) for k, v in inp.items()}
