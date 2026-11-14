"""Preflight checks (`reviewreplay doctor`) and cost estimates (`--dry-run`). Spends nothing,
except `doctor --login`, which sends one tiny prompt to check the login works."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from math import ceil
from pathlib import Path

from . import claude

MIN_PYTHON = (3, 10)
# Per-review figures from the 186 committed m2 reviews (results/m2-*/raw): cost $0.038 / $0.059 /
# $0.103 and time 9 / 15 / 28 seconds at the 10th, 50th and 90th percentile. Reviews only;
# extract and grade add a smaller amount per review.
COST_PER_REVIEW = (0.038, 0.059, 0.103)
SECONDS_PER_REVIEW = (9, 15, 28)


def cache_dir() -> Path:
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "reviewreplay"


def _check_python() -> tuple[bool, str]:
    v = sys.version_info[:2]
    ok = v >= MIN_PYTHON
    return ok, (f"Python {v[0]}.{v[1]}" if ok else
                f"Python {v[0]}.{v[1]} is too old: install Python 3.10 or newer")


def _check_git() -> tuple[bool, str]:
    if not shutil.which("git"):
        return False, "git not found: install git (https://git-scm.com/downloads)"
    out = subprocess.run(["git", "--version"], capture_output=True, text=True)
    return out.returncode == 0, out.stdout.strip() or "git --version failed"


def _check_claude() -> tuple[bool, str]:
    if not shutil.which("claude"):
        return False, ("claude not found: install Claude Code "
                       "(https://docs.claude.com/claude-code) and run `claude` once to log in")
    try:
        version = claude.cli_version()
    except OSError as e:
        return False, f"claude did not start ({e}): reinstall Claude Code"
    return bool(version), version or "claude --version printed nothing: reinstall Claude Code"


def _check_cache() -> tuple[bool, str]:
    d = cache_dir()
    try:
        d.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=d):
            pass
    except OSError as e:
        return False, f"cache folder {d} is not writable ({e.strerror}): fix its permissions or set XDG_CACHE_HOME"
    return True, f"cache folder {d}"


def _check_login() -> tuple[bool, str]:
    proc = subprocess.run(["claude", "-p", "Reply with OK.", "--model", claude.DEFAULT_MODEL,
                           *claude.ISOLATION], capture_output=True, text=True,
                          env=claude.clean_env(), timeout=120)
    text = (proc.stdout or "") + (proc.stderr or "")
    try:
        claude.check_fatal(text)
    except claude.AccountError as e:
        return False, f"claude login problem ({e}): run `claude` and log in, or wait for your usage limit to reset"
    if proc.returncode != 0:
        return False, f"claude -p failed (exit {proc.returncode}): run `claude` once in this terminal to finish setup"
    return True, f"logged in ({claude.auth_mode()})"


def checks(*, login: bool = False) -> list[tuple[str, bool, str]]:
    """(name, ok, one line: what was found, or the fix). The login check is skipped unless asked."""
    out = [("python", *_check_python()), ("git", *_check_git()), ("claude", *_check_claude()),
           ("cache", *_check_cache())]
    if login:
        out.append(("login", *(_check_login() if out[2][1] else (False, "skipped: claude not found"))))
    return out


def print_checks(results: list[tuple[str, bool, str]]) -> bool:
    for name, ok, msg in results:
        print(f"{'ok  ' if ok else 'FAIL'} {name:<7} {msg}")
    return all(ok for _, ok, _ in results)


def preflight() -> bool:
    """The checks `run` and `init` need before spending anything. Prints only the failures."""
    bad = [(n, ok, m) for n, ok, m in checks() if not ok]
    if bad:
        print_checks(bad)
        print("Fix the above, then re-run (`reviewreplay doctor` checks everything).")
    return not bad


def pending_reviews(case_ids: list[str], subject_names: list[str], runs: int, out: Path) -> tuple[int, int]:
    """(total, already done). Runs resume, so finished reviews are not paid for again."""
    total = done = 0
    for k in range(1, runs + 1):
        for s in subject_names:
            for c in case_ids:
                total += 1
                done += (out / "raw" / s / c / f"run{k}.json").exists()
    return total, done


def estimate(n_reviews: int, workers: int) -> dict:
    lo, mid, hi = (n_reviews * c for c in COST_PER_REVIEW)
    waves = ceil(n_reviews / max(workers, 1))
    t_mid, t_hi = (waves * s / 60 for s in SECONDS_PER_REVIEW[1:])
    return {"reviews": n_reviews, "cost": (lo, mid, hi), "minutes": (t_mid, t_hi)}


def describe_run(case_ids: list[str], subject_names: list[str], runs: int, out: Path, workers: int) -> str:
    total, done = pending_reviews(case_ids, subject_names, runs, out)
    todo = total - done
    e = estimate(todo, workers)
    lo, mid, hi = e["cost"]
    lines = [f"{len(case_ids)} case(s) x {len(subject_names)} reviewer(s) x {runs} run(s) = {total} review(s)"]
    if done:
        lines.append(f"{done} already in {out}; {todo} left to run")
    lines.append(f"estimated cost: about ${mid:.2f} (${lo:.2f} to ${hi:.2f}), reviews only")
    lines.append(f"estimated time: about {e['minutes'][0]:.0f} min (up to {e['minutes'][1]:.0f}) "
                 f"with {workers} worker(s)")
    lines.append("Nothing was run (--dry-run). Drop --dry-run to start; runs resume if stopped.")
    return "\n".join(lines)
