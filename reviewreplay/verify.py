"""Settle `unsure` findings by reading the code (roadmap 1.3).

The judge grades from text alone, so a claim like "nothing in the fish script reverses the escaping"
or "py7zr treats an empty targets list as no filter" comes back `unsure`. `verify` gives each such
finding to a read-only checker (Read, Grep and Glob only) with:

  project/        the repository after the change
  change.patch    the change under review
  libs/<name>/    a third-party library's source, when the claim depends on one: from PyPI, the last
                  release before the change; only .py/.pyi files are extracted, nothing is run

The checker answers confirmed / refuted / unsure and must quote the code it relied on. Each quote is
checked against the cited file here, in code; a confirmed or refuted verdict with no quote that
exists is downgraded to unsure. Results go to verify/<subject>/<case>/runN.json beside grades/, so
re-grading never erases them, and `report`/`compare` apply them: confirmed → valid_other,
refuted → false_alarm.
"""
from __future__ import annotations

import io
import json
import re
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

from . import claude
from .cases import CACHE_ROOT, Case, _ensure_commit, _git, repo_clone
from .grade import SERIOUS, _fmt_spots, _parallel, _prompt

LIB_CACHE = CACHE_ROOT / "libs"
MAX_LIB_MB = 60
SOURCE_SUFFIXES = (".py", ".pyi")
EFFECT = {"confirmed": "valid_other", "refuted": "false_alarm", "unsure": "unsure"}

LIBRARY_SCHEMA = {
    "type": "object",
    "properties": {"library": {"type": ["string", "null"]}, "reason": {"type": "string"}},
    "required": ["library", "reason"],
}
VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["confirmed", "refuted", "unsure"]},
        "reason": {"type": "string"},
        "evidence": {"type": "array", "items": {
            "type": "object",
            "properties": {"file": {"type": "string"}, "line": {"type": "integer"},
                           "quote": {"type": "string"}},
            "required": ["file", "line", "quote"],
        }},
    },
    "required": ["verdict", "reason", "evidence"],
}


# ---------- quotes ----------

def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def quote_found(ws: Path, ev: dict) -> bool:
    """True if the quote (whitespace-insensitive, at least 8 characters) is in the cited file,
    which must sit inside the workspace."""
    q = _squash(ev.get("quote", "")).strip("`")
    if len(q) < 8:
        return False
    try:
        path = (ws / ev.get("file", "").lstrip("/")).resolve()
        path.relative_to(ws.resolve())
        return q in _squash(path.read_text(errors="replace"))
    except (OSError, ValueError):
        return False


def settle(raw: dict, ws: Path) -> dict:
    """Apply the quote check to a checker's answer."""
    ok = [e for e in raw.get("evidence", []) if quote_found(ws, e)]
    verdict = raw.get("verdict", "unsure")
    note = ""
    if verdict != "unsure" and not ok:
        verdict, note = "unsure", "downgraded: no quoted evidence was found in the cited files"
    return {"verdict": verdict, "reason": raw.get("reason", ""), "evidence": raw.get("evidence", []),
            "evidence_ok": len(ok), **({"note": note} if note else {})}


# ---------- third-party source ----------

def _safe_name(name: str) -> bool:
    p = Path(name)
    return not p.is_absolute() and ".." not in p.parts and name.endswith(SOURCE_SUFFIXES)


def extract_sources(archive: bytes, filename: str, dest: Path) -> int:
    """Write only .py/.pyi members with safe relative paths. Returns the number written."""
    n = 0
    if filename.endswith((".whl", ".zip")):
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            for m in z.infolist():
                if not m.is_dir() and _safe_name(m.filename):
                    out = dest / m.filename
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_bytes(z.read(m))
                    n += 1
    elif filename.endswith((".tar.gz", ".tgz")):
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as t:
            for m in t.getmembers():
                if m.isfile() and _safe_name(m.name):
                    out = dest / m.name
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_bytes(t.extractfile(m).read())
                    n += 1
    return n


def pick_release(releases: dict, before: datetime) -> tuple[str, dict] | None:
    """The newest non-yanked release uploaded before `before`, and its best file: a pure-Python
    wheel, else the sdist."""
    best = None
    for version, files in releases.items():
        files = [f for f in files if not f.get("yanked")]
        if not files:
            continue
        when = min(datetime.fromisoformat(f["upload_time_iso_8601"].replace("Z", "+00:00")) for f in files)
        if when >= before:
            continue
        pure = [f for f in files if f["filename"].endswith(("-py3-none-any.whl", "-py2.py3-none-any.whl"))]
        sdist = [f for f in files if f["packagetype"] == "sdist" and f["filename"].endswith((".tar.gz", ".zip"))]
        chosen = (pure or sdist or [None])[0]
        if chosen and (best is None or when > best[2]):
            best = (version, chosen, when)
    return (best[0], best[1]) if best else None


def _fetch(url: str, limit_mb: int) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as r:
        data = r.read(limit_mb * 1024 * 1024 + 1)
    if len(data) > limit_mb * 1024 * 1024:
        raise ValueError(f"over {limit_mb} MB")
    return data


def library_source(name: str, before: datetime, limit_mb: int = MAX_LIB_MB) -> tuple[Path, str] | None:
    """Cached source of PyPI package `name` as of `before`, or None if it can't be had."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}", name):
        return None
    try:
        meta = json.loads(_fetch(f"https://pypi.org/pypi/{name}/json", 20))
        picked = pick_release(meta.get("releases", {}), before)
        if not picked:
            return None
        version, f = picked
        dest = LIB_CACHE / f"{name.lower()}-{version}"
        if not dest.exists():
            if f.get("size", 0) > limit_mb * 1024 * 1024:
                return None
            tmp = dest.with_suffix(".tmp")
            shutil.rmtree(tmp, ignore_errors=True)
            tmp.mkdir(parents=True)
            if not extract_sources(_fetch(f["url"], limit_mb), f["filename"], tmp):
                shutil.rmtree(tmp)
                return None
            tmp.rename(dest)
        return dest, version
    except (OSError, ValueError, KeyError):
        return None


def change_date(case: Case) -> datetime:
    repo = repo_clone(case.meta["repo"])
    _ensure_commit(repo, case.meta["commit"])
    out = _git(repo, "show", "-s", "--format=%cI", case.meta["commit"], text=True).stdout.strip()
    return datetime.fromisoformat(out)


# ---------- one finding ----------

def _claim(f: dict) -> str:
    return f"[{f['severity']}] {f['file']}:{f['line_start']}-{f['line_end']}: {f['summary']}"


def _which_library(case: Case, f: dict, model: str) -> str | None:
    prompt = _prompt("verify_library.md").replace("{claim}", _claim(f)).replace("{title}", case.title)
    with tempfile.TemporaryDirectory(prefix="rb-v-") as tmp:
        res = claude.run_json(prompt, LIBRARY_SCHEMA, Path(tmp), model=model)
    lib = res["data"].get("library")
    return lib.strip() if isinstance(lib, str) and lib.strip() else None


def check_finding(case: Case, f: dict, model: str, limit_mb: int = MAX_LIB_MB) -> dict:
    library = _which_library(case, f, model)
    lib_info = None
    with tempfile.TemporaryDirectory(prefix="rb-v-") as tmp:
        ws = Path(tmp) / "ws"
        shutil.copytree(case.tree / "after", ws / "project", symlinks=False,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
        shutil.copy(case.tree / "change.patch", ws / "change.patch")
        (ws / "libs").mkdir()
        if library:
            got = library_source(library, change_date(case), limit_mb)
            if got:
                src, version = got
                shutil.copytree(src, ws / "libs" / library)
                lib_info = {"name": library, "version": version}
            else:
                lib_info = {"name": library, "version": None, "note": "source not available"}
        libs = (f"libs/{library}/ holds {library} {lib_info['version']}, the last release before the "
                f"change." if lib_info and lib_info.get("version") else "libs/ is empty.")
        prompt = (_prompt("verify.md").replace("{claim}", _claim(f)).replace("{title}", case.title)
                  .replace("{libs}", libs)
                  .replace("{known_ok}", _fmt_spots(case.known_ok, "note"))
                  .replace("{related}", "\n".join(f"- {r}" for r in case.related_valid) or "(none)"))
        res = claude.run_json(prompt, VERIFY_SCHEMA, ws, model=model, read_files=True, timeout=900)
        out = settle(res["data"], ws)
    return {**out, "library": lib_info, "cost_usd": res["cost_usd"] or 0.0}


# ---------- a run ----------

def targets(grade: dict, all_severities: bool = False) -> list[dict]:
    return [f for f in grade["findings"]
            if f["label"] == "unsure" and (all_severities or f["severity"] in SERIOUS)]


def verify_one(case: Case, grade_file: Path, out_file: Path, model: str, force: bool = False,
               all_severities: bool = False, check=check_finding, limit_mb: int = MAX_LIB_MB) -> str:
    grade = json.loads(grade_file.read_text())
    todo = targets(grade, all_severities)
    done = {} if force or not out_file.exists() else json.loads(out_file.read_text())["findings"]
    new = [f for f in todo if str(f["index"]) not in done]
    if not todo or not new:
        return "nothing to check" if not todo else "cached"
    for f in new:
        done[str(f["index"])] = check(case, f, model, limit_mb)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps({"case": case.id, "model": model, "findings": done}, indent=2))
    return ", ".join(done[str(f["index"])]["verdict"] for f in new)


def verify_all(run_dir: Path, cases: dict[str, Case], model: str, workers: int, force: bool = False,
               all_severities: bool = False, limit_mb: int = MAX_LIB_MB, kind: str | None = None) -> None:
    jobs = []
    for g in sorted((run_dir / "grades").rglob("run*.json")):
        rel = g.relative_to(run_dir / "grades")
        if rel.parts[1] in cases and (not kind or cases[rel.parts[1]].kind == kind):
            jobs.append((cases[rel.parts[1]], g, run_dir / "verify" / rel))
    _parallel(jobs, lambda j: verify_one(*j, model, force, all_severities, limit_mb=limit_mb), workers, "verify")


def apply_checks(grade: dict, checks: dict | None) -> dict:
    """The grade with checked `unsure` findings relabelled; each keeps its `check`."""
    if not checks:
        return grade
    rows = []
    for f in grade["findings"]:
        c = checks.get(str(f["index"]))
        if c and f["label"] == "unsure":
            f = {**f, "label": EFFECT[c["verdict"]], "check": c, "label_before_check": "unsure"}
        rows.append(f)
    return {**grade, "findings": rows}


def load_checks(run_dir: Path, rel: Path) -> dict | None:
    p = run_dir / "verify" / rel
    return json.loads(p.read_text())["findings"] if p.exists() else None


def check_summary(run_dirs: list[Path], cases: dict[str, Case], kind: str | None = None) -> dict:
    """Counts of code-check verdicts over the run folders."""
    out = {"checked": 0, "confirmed": 0, "refuted": 0, "unsure": 0, "downgraded": 0, "cost_usd": 0.0}
    for d in run_dirs:
        for v in sorted((d / "verify").rglob("run*.json")):
            case = cases.get(v.relative_to(d / "verify").parts[1])
            if kind and (case is None or case.kind != kind):
                continue
            for c in json.loads(v.read_text())["findings"].values():
                out["checked"] += 1
                out[c["verdict"]] += 1
                out["downgraded"] += bool(c.get("note"))
                out["cost_usd"] += c.get("cost_usd", 0.0)
    return out
