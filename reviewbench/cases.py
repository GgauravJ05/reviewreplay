"""Load, resolve and validate test cases.

A case directory holds:
  case.json     metadata (id, kind, track, title, source, license, added)
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
    bugs: list[Spot] = field(default_factory=list)
    known_ok: list[Spot] = field(default_factory=list)
    # other real problems in the change that a reviewer may fairly report (graded valid_other)
    related_valid: list[str] = field(default_factory=list)

    @property
    def has_bug(self) -> bool:
        return bool(self.bugs)


class CaseError(Exception):
    pass


def _locate(case_dir: Path, loc: dict, where: str) -> tuple[int, int]:
    target = case_dir / "after" / loc["file"]
    if not target.exists():
        raise CaseError(f"{where}: file not found: after/{loc['file']}")
    lines = target.read_text(encoding="utf-8").splitlines()
    hits = [n for n, text in enumerate(lines, start=1) if loc["anchor"] in text]
    if len(hits) != 1:
        raise CaseError(f"{where}: anchor {loc['anchor']!r} matched {len(hits)} lines in {loc['file']}")
    start = hits[0]
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
    truth = json.loads((case_dir / "truth.json").read_text(encoding="utf-8"))
    bugs = [_resolve(case_dir, b, i, "bugs") for i, b in enumerate(truth.get("bugs", []))]
    ok = [_resolve(case_dir, s, i, "known_ok") for i, s in enumerate(truth.get("known_ok", []))]
    if meta["kind"] in {"planted", "real"} and not bugs:
        raise CaseError(f"{meta['kind']} case has no bugs in truth.json")
    if meta["kind"] in {"clean", "decoy"} and bugs:
        raise CaseError(f"{meta['kind']} case must have no bugs")
    if meta["kind"] == "decoy" and not ok:
        raise CaseError("decoy case needs at least one known_ok spot")
    return Case(id=meta["id"], kind=meta["kind"], track=meta["track"], title=meta["title"],
                path=case_dir, meta=meta, bugs=bugs, known_ok=ok,
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
    patch = case_dir / "change.patch"
    if not patch.exists():
        return ["change.patch missing (run `reviewbench make-patch`)"]
    changed = sum(1 for line in patch.read_text(encoding="utf-8").splitlines()
                  if line[:1] in "+-" and not line.startswith(("+++", "---")))
    if changed > MAX_CHANGED_LINES:
        problems.append(f"change too large: {changed} changed lines > {MAX_CHANGED_LINES}")
    if _count_lines(case_dir / "base") > MAX_BASE_LINES:
        problems.append(f"base/ larger than {MAX_BASE_LINES} lines")
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp) / "ws"
        shutil.copytree(case_dir / "base", ws, ignore=IGNORE_CACHES)
        proc = subprocess.run(["git", "apply", str(patch.resolve())],
                              cwd=ws, capture_output=True, text=True)
        if proc.returncode != 0:
            problems.append(f"patch does not apply: {proc.stderr.strip()}")
        else:
            cmp = filecmp.dircmp(ws, case_dir / "after", ignore=[*CACHE_DIRS, ".git"])
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
