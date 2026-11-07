"""Find candidate real cases: bug-fix commits and the commits that introduced the bug.

For each fix commit whose message suggests a regression, two independent signals point at the
introducing commit:
  - referenced: a commit hash or PR number mentioned in the fix message ("introduced in #1234")
  - blame (SZZ): the commits that last touched the lines the fix deletes or rewrites
A candidate where both agree is the strongest. Every candidate still needs a careful read of the
fix, the issue and the introducing diff before it becomes a case.
"""
from __future__ import annotations

import re
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .cases import MAX_CHANGED_LINES, repo_clone

FIX_PATTERN = r"regression|introduced (in|by)|broken (in|by|since)|broke |caused by|since v?[0-9]"
SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
PR_RE = re.compile(r"(?:#|pull/)(\d{2,6})\b")
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@")


@dataclass
class Candidate:
    fix: str
    date: str
    subject: str
    referenced: list[str] = field(default_factory=list)
    blamed: list[str] = field(default_factory=list)
    introducer: str | None = None
    agree: bool = False
    introducer_lines: int | None = None
    introducer_subject: str = ""
    introducer_date: str = ""


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout


def _is_code(path: str) -> bool:
    """Library code: a .py file outside tests and docs (src/click/testing.py counts as code)."""
    parts = path.lower().split("/")
    name = parts[-1]
    if not name.endswith(".py") or parts[0] in ("docs", "doc", "examples", "benchmarks"):
        return False
    is_test = (any(d in ("test", "tests", "testing") for d in parts[:-1])
               or name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py")
    return not is_test


def _referenced(repo: Path, message: str, fix: str) -> list[str]:
    out = []
    for sha in SHA_RE.findall(message):
        full = _git(repo, "rev-parse", "--verify", "-q", f"{sha}^{{commit}}").strip()
        if full and full != fix and full not in out:
            out.append(full)
    for pr in PR_RE.findall(message):
        hit = _git(repo, "log", "--format=%H", "-F", f"--grep=(#{pr})", "-n", "1", f"{fix}^").strip()
        if hit and hit not in out:
            out.append(hit)
    return out


def _blamed(repo: Path, fix: str, max_files: int = 4) -> list[str]:
    files = [f for f in _git(repo, "diff-tree", "--no-commit-id", "-r", "--name-only", fix).split()
             if _is_code(f)][:max_files]
    votes: Counter = Counter()
    for f in files:
        for line in _git(repo, "diff", "-U0", f"{fix}^", fix, "--", f).splitlines():
            m = HUNK_RE.match(line)
            if not m or m.group(2) == "0":
                continue                       # pure addition: nothing to blame
            start, n = int(m.group(1)), int(m.group(2) or 1)
            porcelain = _git(repo, "blame", "--porcelain", "-L", f"{start},{start + n - 1}",
                             f"{fix}^", "--", f)
            for row in porcelain.splitlines():
                parts = row.split()
                if len(parts) >= 3 and len(parts[0]) == 40 and parts[1].isdigit():
                    votes[parts[0]] += 1
    return [sha for sha, _ in votes.most_common()]


def _landing(repo: Path, sha: str, fix: str, mainline: set[str]) -> str:
    """The commit that brought `sha` into the main line: itself, or the merge that landed it."""
    if sha in mainline:
        return sha
    merges = _git(repo, "rev-list", "--first-parent", "--ancestry-path", "--merges",
                  f"{sha}..{fix}").split()
    return merges[-1] if merges else sha


def _changed_lines(repo: Path, sha: str) -> int:
    """Lines changed against the first parent (for a merge: the whole merged PR)."""
    total = 0
    for row in _git(repo, "diff", "--numstat", f"{sha}^", sha).splitlines():
        a, d, *_ = row.split("\t") + ["", ""]
        if a.isdigit() and d.isdigit():
            total += int(a) + int(d)
    return total


def mine(url: str, since: str = "2025-06-01", limit: int = 40,
         pattern: str = FIX_PATTERN) -> list[Candidate]:
    repo = repo_clone(url)
    _git(repo, "fetch", "-q", "origin")
    log = _git(repo, "log", "HEAD", f"--since={since}", "--no-merges", "-i", "-E",
               f"--grep={pattern}", "--format=%H%x00%ad%x00%s%x00%b%x1e", "--date=short")
    mainline = set(_git(repo, "rev-list", "--first-parent", "HEAD").split())
    out: list[Candidate] = []
    for rec in log.split("\x1e"):
        if not rec.strip():
            continue
        fix, date, subject, body = (rec.strip("\n").split("\x00") + ["", "", "", ""])[:4]
        cand = Candidate(fix=fix, date=date, subject=subject)
        cand.referenced = [_landing(repo, s, fix, mainline)
                           for s in _referenced(repo, subject + "\n" + body, fix)]
        cand.blamed = list(dict.fromkeys(_landing(repo, s, fix, mainline)
                                         for s in _blamed(repo, fix)))[:3]
        agreed = [s for s in cand.referenced if s in cand.blamed]
        cand.introducer = (agreed or cand.referenced or cand.blamed or [None])[0]
        cand.agree = bool(agreed)
        if cand.introducer:
            cand.introducer_lines = _changed_lines(repo, cand.introducer)
            meta = _git(repo, "show", "-s", "--format=%ad%x00%s", "--date=short", cand.introducer)
            cand.introducer_date, _, cand.introducer_subject = meta.strip().partition("\x00")
        out.append(cand)
        if len(out) >= limit:
            break
    return out


def table(cands: list[Candidate]) -> str:
    rows = ["| fix | date | fix subject | introducer | lines | agree | introducer subject |",
            "|---|---|---|---|---|---|---|"]
    for c in cands:
        ok = c.introducer_lines is not None and c.introducer_lines <= MAX_CHANGED_LINES
        rows.append(f"| {c.fix[:10]} | {c.date} | {c.subject[:60]} | "
                    f"{(c.introducer or '-')[:10]} | {c.introducer_lines if c.introducer else '-'}"
                    f"{'' if ok else ' ✗'} | {'yes' if c.agree else ''} | {c.introducer_subject[:50]} |")
    return "\n".join(rows)


def as_dicts(cands: list[Candidate]) -> list[dict]:
    return [asdict(c) for c in cands]
