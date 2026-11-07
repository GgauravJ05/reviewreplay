"""Load, resolve and validate test cases.

A case directory holds:
  case.json     metadata (id, kind, track, title, source, license, added)
                real cases add repo, commit (the bug-introducing commit) and fix; their base/,
                after/ and change.patch are not stored but exported from git into .cache/real/
                (no git history, so the later fix can't leak into the review workspace)
  base/         the code before the change
  after/        the code after the change (source of truth for line numbers)
  change.patch  generated from base/ → after/ with `reviewbench make-patch`
  truth.json    answer key; spots are located by an `anchor` (a unique substring of the
                first line) plus a `span` (number of lines), so edits never break line numbers
  NOTES.md      optional: explanation and source credit
"""
from __future__ import annotations

import filecmp
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

KINDS = {"planted", "real", "clean", "decoy"}
# never part of a case: created by running case code locally
CACHE_DIRS = ("__pycache__", ".pytest_cache", ".mypy_cache", ".ipynb_checkpoints", ".DS_Store")
IGNORE_CACHES = shutil.ignore_patterns(*CACHE_DIRS)
REQUIRED_META = ("id", "kind", "track", "title", "source", "license", "added")
REQUIRED_REAL = ("repo", "commit", "fix")
ROOT = Path(__file__).resolve().parents[1]
REPO_CACHE = ROOT / ".cache" / "repos"
REAL_CACHE = ROOT / ".cache" / "real"
MAX_CHANGED_LINES = 300
MAX_BASE_LINES = 2000


@dataclass
class Spot:
    id: str
    file: str
    lines: tuple[int, int]
    info: dict
    # extra acceptable locations, e.g. the other side of a cross-file bug: (file, start, end)
    also: list[tuple[str, int, int]] = field(default_factory=list)

    @property
    def locations(self) -> list[tuple[str, int, int]]:
        return [(self.file, *self.lines), *self.also]


@dataclass
class Case:
    id: str
    kind: str
    track: str
    title: str
    path: Path
    meta: dict
    tree: Path            # directory holding base/, after/ and change.patch
    bugs: list[Spot] = field(default_factory=list)
    known_ok: list[Spot] = field(default_factory=list)
    # other real problems in the change that a reviewer may fairly report (graded valid_other)
    related_valid: list[str] = field(default_factory=list)

    @property
    def has_bug(self) -> bool:
        return bool(self.bugs)


class CaseError(Exception):
    pass


def _git(repo: Path, *args: str, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, **kw)


def repo_clone(url: str) -> Path:
    """Blobless bare clone of a public repo, cached under .cache/repos/."""
    name = url.rstrip("/").removesuffix(".git").split("github.com/")[-1].replace("/", "__")
    dest = REPO_CACHE / f"{name}.git"
    if not dest.exists():
        REPO_CACHE.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--bare", "--filter=blob:none", url, str(dest)],
                       check=True)
    return dest


def _ensure_commit(repo: Path, sha: str) -> None:
    if subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{sha}^{{commit}}"],
                      capture_output=True).returncode != 0:
        _git(repo, "fetch", "-q", "origin", sha)


def _export(repo: Path, rev: str, dest: Path) -> None:
    dest.mkdir(parents=True)
    archive = _git(repo, "archive", rev).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True)


def real_tree(meta: dict) -> Path:
    """Export a real case's parent (base/), introducing commit (after/) and their diff."""
    dest = REAL_CACHE / f"{meta['id']}@{meta['commit'][:12]}"
    if (dest / "change.patch").exists():
        return dest
    repo = repo_clone(meta["repo"])
    _ensure_commit(repo, meta["commit"])
    parent = _git(repo, "rev-parse", f"{meta['commit']}^", text=True).stdout.strip()
    tmp = dest.with_suffix(".tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    _export(repo, parent, tmp / "base")
    _export(repo, meta["commit"], tmp / "after")
    patch = _git(repo, "diff", "--binary", parent, meta["commit"]).stdout
    (tmp / "change.patch").write_bytes(patch)
    tmp.rename(dest)
    return dest


def _locate(case_dir: Path, loc: dict, where: str) -> tuple[int, int]:
    target = case_dir / "after" / loc["file"]
    if not target.exists():
        raise CaseError(f"{where}: file not found: after/{loc['file']}")
    lines = target.read_text(encoding="utf-8").splitlines()
    hits = [n for n, text in enumerate(lines, start=1) if loc["anchor"] in text]
    nth = loc.get("occurrence")          # 1-based; for code repeated verbatim in one file
    if nth is None and len(hits) != 1:
        raise CaseError(f"{where}: anchor {loc['anchor']!r} matched {len(hits)} lines in {loc['file']}")
    if nth is not None and not 1 <= nth <= len(hits):
        raise CaseError(f"{where}: anchor {loc['anchor']!r} has {len(hits)} matches, not {nth}")
    start = hits[(nth or 1) - 1]
    end = start + int(loc.get("span", 1)) - 1
    if end > len(lines):
        raise CaseError(f"{where}: span runs past end of {loc['file']}")
    return start, end


def _resolve(case_dir: Path, raw: dict, idx: int, kind: str) -> Spot:
    where = f"{kind}[{idx}]"
    start, end = _locate(case_dir, raw, where)
    also = [(a["file"], *_locate(case_dir, a, f"{where}.also[{j}]"))
            for j, a in enumerate(raw.get("also", []))]
    return Spot(id=raw.get("id", f"{kind}{idx}"), file=raw["file"], lines=(start, end),
                info=raw, also=also)


def load_case(case_dir: Path) -> Case:
    meta = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED_META if not meta.get(k)]
    if missing:
        raise CaseError(f"case.json missing: {', '.join(missing)}")
    if meta["kind"] not in KINDS:
        raise CaseError(f"unknown kind {meta['kind']!r}")
    if meta["kind"] == "real":
        missing = [k for k in REQUIRED_REAL if not meta.get(k)]
        if missing:
            raise CaseError(f"real case.json missing: {', '.join(missing)}")
        tree = real_tree(meta)
    else:
        tree = case_dir
    truth = json.loads((case_dir / "truth.json").read_text(encoding="utf-8"))
    bugs = [_resolve(tree, b, i, "bugs") for i, b in enumerate(truth.get("bugs", []))]
    ok = [_resolve(tree, s, i, "known_ok") for i, s in enumerate(truth.get("known_ok", []))]
    if meta["kind"] in {"planted", "real"} and not bugs:
        raise CaseError(f"{meta['kind']} case has no bugs in truth.json")
    if meta["kind"] in {"clean", "decoy"} and bugs:
        raise CaseError(f"{meta['kind']} case must have no bugs")
    if meta["kind"] == "decoy" and not ok:
        raise CaseError("decoy case needs at least one known_ok spot")
    return Case(id=meta["id"], kind=meta["kind"], track=meta["track"], title=meta["title"],
                path=case_dir, meta=meta, tree=tree, bugs=bugs, known_ok=ok,
                related_valid=list(truth.get("related_valid", [])))


def find_case_dirs(root: Path) -> list[Path]:
    return sorted(p.parent for p in root.rglob("case.json"))


def load_cases(root: Path) -> list[Case]:
    return [load_case(d) for d in find_case_dirs(root)]


def make_patch(case_dir: Path) -> str:
    """Write change.patch = diff of base/ → after/ (applies with `git apply`, -p1)."""
    excludes = [x for d in CACHE_DIRS for x in ("-x", d)]
    proc = subprocess.run(["diff", "-ruN", *excludes, "base", "after"], cwd=case_dir,
                          capture_output=True, text=True)
    if proc.returncode not in (0, 1):
        raise CaseError(proc.stderr)
    (case_dir / "change.patch").write_text(proc.stdout, encoding="utf-8")
    return proc.stdout


def _count_lines(root: Path) -> int:
    return sum(len(p.read_text(encoding="utf-8").splitlines())
               for p in root.rglob("*") if p.is_file())


def check_case(case_dir: Path) -> list[str]:
    """Return a list of problems (empty = case is valid)."""
    problems: list[str] = []
    try:
        case = load_case(case_dir)
    except (CaseError, KeyError, json.JSONDecodeError) as e:
        return [f"load: {e}"]
    tree = case.tree
    patch = tree / "change.patch"
    if not patch.exists():
        return ["change.patch missing (run `reviewbench make-patch`)"]
    changed = sum(1 for line in patch.read_text(encoding="utf-8").splitlines()
                  if line[:1] in "+-" and not line.startswith(("+++", "---")))
    if changed > MAX_CHANGED_LINES:
        problems.append(f"change too large: {changed} changed lines > {MAX_CHANGED_LINES}")
    if case.kind != "real" and _count_lines(tree / "base") > MAX_BASE_LINES:
        problems.append(f"base/ larger than {MAX_BASE_LINES} lines")
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp) / "ws"
        shutil.copytree(tree / "base", ws, ignore=IGNORE_CACHES, symlinks=True)
        proc = subprocess.run(["git", "apply", str(patch.resolve())],
                              cwd=ws, capture_output=True, text=True)
        if proc.returncode != 0:
            problems.append(f"patch does not apply: {proc.stderr.strip()}")
        else:
            cmp = filecmp.dircmp(ws, tree / "after", ignore=[*CACHE_DIRS, ".git"])
            diffs = _dircmp_diffs(cmp)
            if diffs:
                problems.append(f"patched base/ differs from after/: {diffs}")
    if case.kind == "decoy":
        for s in case.known_ok:
            if not s.info.get("note"):
                problems.append(f"known_ok {s.id} needs a note")
    return problems


def _dircmp_diffs(cmp: filecmp.dircmp, prefix: str = "") -> list[str]:
    out = [prefix + n for n in cmp.left_only + cmp.right_only + cmp.diff_files]
    for name, sub in cmp.subdirs.items():
        out += _dircmp_diffs(sub, prefix + name + "/")
    return out
