"""Reviewer setups ("subjects") and their isolated workspaces.

subjects/<name>.json:
{
  "name": "code-review-skill-invoked",
  "skill": {"name": "code-review-skill",
            "repo": "https://github.com/awesome-skills/code-review-skill",
            "commit": "4850184"},            # null for no skill
  "invoke": true,                           # prefix the prompt with /<skill name>
  "invoke_command": null,                   # or a built-in command, e.g. "/code-review"
  "credit": "awesome-skills/code-review-skill (MIT)"
}

Skills are fetched at the pinned commit (from a local clone in RB_SKILLS_DIR or the parent folder
if present, else cloned into .cache/), never vendored into this repository.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .cases import IGNORE_CACHES, Case

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "skills"
REVIEW_PROMPT = ("Review the uncommitted changes in this repository. "
                 "Report any bugs you find, with file and line.")
SKILL_JUNK = (".git", ".hive", ".github", "index.html", "index.en.html", ".nojekyll")


@dataclass
class Subject:
    name: str
    skill: dict | None
    invoke: bool
    invoke_command: str | None
    credit: str | None

    @property
    def prompt(self) -> str:
        if self.invoke_command:
            return f"{self.invoke_command} {REVIEW_PROMPT}"
        if self.invoke and self.skill:
            return f"/{self.skill['name']} {REVIEW_PROMPT}"
        return REVIEW_PROMPT


def load_subject(path: Path) -> Subject:
    d = json.loads(path.read_text(encoding="utf-8"))
    return Subject(name=d["name"], skill=d.get("skill"), invoke=bool(d.get("invoke")),
                   invoke_command=d.get("invoke_command"), credit=d.get("credit"))


def load_subjects(root: Path, names: list[str] | None = None) -> list[Subject]:
    subs = [load_subject(p) for p in sorted(root.glob("*.json"))]
    if names:
        by = {s.name: s for s in subs}
        missing = [n for n in names if n not in by]
        if missing:
            raise SystemExit(f"unknown subjects: {missing}; have {sorted(by)}")
        subs = [by[n] for n in names]
    return subs


def _local_clone(repo_url: str) -> Path | None:
    name = repo_url.rstrip("/").split("/")[-1].removesuffix(".git")
    for base in (os.environ.get("RB_SKILLS_DIR"), str(ROOT.parent)):
        if base and (Path(base) / name / ".git").exists():
            return Path(base) / name
    return None


def skill_source(skill: dict) -> Path:
    """Return a directory containing the skill at its pinned commit."""
    dest = CACHE / f"{skill['name']}@{skill['commit']}"
    if (dest / "SKILL.md").exists():
        return dest
    repo = _local_clone(skill["repo"])
    if repo is None:
        repo = CACHE / f"_clone-{skill['name']}"
        if not repo.exists():
            subprocess.run(["git", "clone", "-q", skill["repo"], str(repo)], check=True)
    have = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{skill['commit']}^{{commit}}"])
    if have.returncode != 0:
        subprocess.run(["git", "-C", str(repo), "fetch", "-q", "origin", skill["commit"]], check=True)
    tmp = dest.with_suffix(".tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    archive = subprocess.run(["git", "-C", str(repo), "archive", skill["commit"]],
                             check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(tmp)], input=archive, check=True)
    for junk in SKILL_JUNK:
        p = tmp / junk
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()
    tmp.rename(dest)
    return dest


def build_workspace(case: Case, subject: Subject, root: Path) -> Path:
    """Fresh git repo of base/, change applied uncommitted, skill (if any) in .claude/skills/."""
    ws = root / "ws"
    shutil.copytree(case.path / "base", ws, ignore=IGNORE_CACHES)
    git = ["git", "-C", str(ws), "-c", "user.name=rb", "-c", "user.email=rb@example.invalid"]
    subprocess.run(["git", "-C", str(ws), "init", "-q", "-b", "main"], check=True)
    subprocess.run(git + ["add", "-A"], check=True)
    subprocess.run(git + ["commit", "-q", "-m", "base"], check=True)
    subprocess.run(["git", "-C", str(ws), "apply", str((case.path / "change.patch").resolve())],
                   check=True)
    # an installed skill must never show up as part of "the uncommitted changes"
    (ws / ".git" / "info" / "exclude").write_text(".claude/\n")
    if subject.skill:
        shutil.copytree(skill_source(subject.skill), ws / ".claude" / "skills" / subject.skill["name"])
    return ws
