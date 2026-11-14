"""Turn any git repository's own history into a private review benchmark.

    reviewreplay init [REPO] --out .reviewreplay

1. mine REPO for fix commits that point back to the commit that introduced the bug
2. for each candidate, an LLM drafts the answer key from the fix (message + diff) and the
   introducing diff; the draft is checked against the code (the anchor line must exist)
3. write draft cases (case.json "status": "draft"); a person confirms each one by reading
   its NOTES.md and setting "status": "ready". `reviewreplay run` skips drafts by default.

Bugs your team actually shipped are the most relevant test of a reviewer for your codebase, and
code in a private repository is unlikely to be in any model's training data.
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from datetime import date
from pathlib import Path

from . import claude
from .cases import MAX_CHANGED_LINES, CaseError, check_case, real_tree, repo_clone
from .mine import Candidate, _is_code, mine

DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "is_behavior_bug": {"type": "boolean"},
        "reason": {"type": "string"},
        "file": {"type": "string"},
        "anchor_line": {"type": "string"},
        "span": {"type": "integer"},
        "severity": {"type": "string", "enum": ["blocking", "important", "minor"]},
        "summary": {"type": "string"},
        "trigger": {"type": "string"},
    },
    "required": ["is_behavior_bug", "reason", "file", "anchor_line", "span", "severity",
                 "summary", "trigger"],
}

DRAFT_PROMPT = """You are building an answer key for a code-review benchmark.

Commit A introduced a change. Later, commit B fixed a problem in it. A reviewer will be shown
commit A only and asked to find bugs. Decide whether commit B fixes a real behavior bug that
commit A introduced (not a feature, refactor, typing, style or docs change). If so, describe it.

Rules:
- `file`: path of the file in commit A where the bug is.
- `anchor_line`: copy one line from commit A's version of that file, exactly, where the bug is.
  Choose a distinctive line.
- `span`: how many lines from the anchor the bug covers (1-15).
- `summary`: what is wrong and why, in one or two sentences, using only what the commits show.
- `trigger`: a concrete input or situation and the wrong result, as described by the fix.

Commit B message:
{fix_message}

Commit B diff (code files):
{fix_diff}

Commit A message:
{intro_message}

Commit A diff:
{intro_diff}
"""


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "repo"


def _track(path: str) -> str:
    return {"py": "python", "ts": "typescript", "tsx": "typescript", "mts": "typescript",
            "cts": "typescript", "js": "javascript", "jsx": "javascript", "mjs": "javascript",
            "cjs": "javascript", "go": "go", "rs": "rust",
            "java": "java"}.get(path.rsplit(".", 1)[-1], "other")


def draft_case(repo: Path, repo_ref: str, cand: Candidate, out: Path, model: str) -> tuple[Path | None, str]:
    """Draft one case. Returns (case dir or None, message)."""
    fix_files = [f for f in _git(repo, "diff-tree", "--no-commit-id", "-r", "--name-only", cand.fix).split()
                 if _is_code(f)]
    if not fix_files:
        return None, "fix touches no code files"
    prompt = DRAFT_PROMPT.format(
        fix_message=_git(repo, "show", "-s", "--format=%B", cand.fix)[:3000],
        fix_diff=_git(repo, "diff", f"{cand.fix}^", cand.fix, "--", *fix_files)[:12000],
        intro_message=_git(repo, "show", "-s", "--format=%B", cand.introducer)[:3000],
        intro_diff=_git(repo, "diff", f"{cand.introducer}^", cand.introducer)[:24000],
    )
    with tempfile.TemporaryDirectory(prefix="rb-draft-") as tmp:
        res = claude.run_json(prompt, DRAFT_SCHEMA, cwd=Path(tmp), model=model)
    d = res.get("data") or {}
    if not d.get("is_behavior_bug"):
        return None, f"not a behavior bug: {str(d.get('reason', '?'))[:120]}"

    name = repo_ref.rstrip("/").removesuffix(".git").split("/")[-1]
    case_id = f"{_slug(name)}-{cand.fix[:8]}"
    meta = {
        "id": case_id, "kind": "real", "track": _track(d["file"]),
        "title": cand.introducer_subject[:120] or f"Commit {cand.introducer[:10]}",
        "source": f"{repo_ref}@{cand.introducer}", "license": "same as the repository",
        "added": date.today().isoformat(), "repo": repo_ref, "commit": cand.introducer,
        "fix": cand.fix, "status": "draft", "drafted_by": model,
        "signals": {"referenced": bool(cand.referenced), "blame_agrees": cand.agree},
    }
    tree = real_tree(meta)
    after = tree / "after" / d["file"]
    if not after.exists():
        return None, f"drafted file not found: {d['file']}"
    want = " ".join(d["anchor_line"].split())
    lines = after.read_text(encoding="utf-8", errors="replace").splitlines()
    hits = ([ln for ln in lines if " ".join(ln.split()) == want]
            or [ln for ln in lines if want and want in " ".join(ln.split())])
    if not hits:
        return None, "drafted anchor line not found in the code"
    anchor = hits[0].strip()
    bug = {"id": "b1", "file": d["file"], "anchor": anchor, "span": max(1, min(int(d["span"]), 15)),
           "class": "real", "severity": d["severity"], "summary": d["summary"], "trigger": d["trigger"]}
    if sum(1 for ln in lines if anchor in ln) > 1:
        bug["occurrence"] = 1
    case_dir = out / "cases" / "real" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "case.json").write_text(json.dumps(meta, indent=2) + "\n")
    (case_dir / "truth.json").write_text(
        json.dumps({"bugs": [bug], "known_ok": [], "related_valid": []}, indent=2) + "\n")
    (case_dir / "NOTES.md").write_text(
        f"# {case_id} (draft)\n\nIntroduced in `{cand.introducer}`: {cand.introducer_subject}\n"
        f"Fixed in `{cand.fix}`: {cand.subject}\n\nWhy this is a bug (drafted by {model}):\n"
        f"{d['reason']}\n\n**To confirm:** read both commits; check that `truth.json` names the right "
        f"line and describes the bug the fix repairs; then set `\"status\": \"ready\"` in case.json.\n")
    problems = check_case(case_dir)
    if problems:
        return case_dir, "drafted, but check failed: " + "; ".join(problems)
    return case_dir, "drafted"


def init(repo_ref: str, out: Path, *, since: str, max_cases: int, model: str,
         pattern: str | None = None) -> list[tuple[str, str]]:
    repo = repo_clone(repo_ref)
    kw = {"pattern": pattern} if pattern else {}
    cands = [c for c in mine(repo_ref, since=since, limit=max_cases * 5, **kw)
             if c.introducer and c.introducer_lines and c.introducer_lines <= MAX_CHANGED_LINES]
    cands.sort(key=lambda c: (not c.agree, not c.referenced))
    report: list[tuple[str, str]] = []
    made = 0
    for cand in cands:
        if made >= max_cases:
            break
        try:
            case_dir, msg = draft_case(repo, repo_ref, cand, out, model)
        except (CaseError, KeyError, ValueError, RuntimeError, subprocess.CalledProcessError) as e:
            case_dir, msg = None, f"error: {e}"
        report.append((cand.fix[:10], msg))
        made += int(bool(case_dir) and msg == "drafted")
    return report
