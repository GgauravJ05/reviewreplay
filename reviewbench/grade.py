"""③ Extract findings and ④ grade them against the answer key.

Extraction: one structured call per review turns free text into findings (same prompt for every subject).
Grading, two stages:
  1. location match (code): a finding is a *candidate* for a truth bug if it names the same file and its
     line range overlaps one of the bug's locations (± TOLERANCE lines). Decoy traps are found the same
     way against `known_ok` spots.
  2. judge (one structured call per review): decides whether each candidate is the *same defect*, and
     classifies everything else as valid_other / invalid / unsure.
A finding counts as a hit only if both stages agree.
"""
from __future__ import annotations

import json
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import claude
from .cases import Case, Spot

ROOT = Path(__file__).resolve().parents[1]
TOLERANCE = 3
SERIOUS = {"blocking", "important"}

FINDINGS_SCHEMA = {
    "type": "object",
    "properties": {"findings": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "file": {"type": "string"},
            "line_start": {"type": "integer"},
            "line_end": {"type": "integer"},
            "severity": {"type": "string", "enum": ["blocking", "important", "minor", "note"]},
            "summary": {"type": "string"},
        },
        "required": ["file", "line_start", "line_end", "severity", "summary"],
    }}},
    "required": ["findings"],
}
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {"grades": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "index": {"type": "integer"},
            "same_bug_as": {"type": ["string", "null"]},
            "verdict": {"type": "string", "enum": ["matches_truth", "valid_other", "invalid", "unsure"]},
            "reason": {"type": "string"},
        },
        "required": ["index", "same_bug_as", "verdict", "reason"],
    }}},
    "required": ["grades"],
}


def _prompt(name: str) -> str:
    return (ROOT / "prompts" / name).read_text(encoding="utf-8")


def norm_path(p: str) -> str:
    p = p.strip().strip("`").removeprefix("./")
    return p.split(":")[0] if ":" in p and not p.startswith("/") else p


def same_file(a: str, b: str) -> bool:
    a, b = norm_path(a), norm_path(b)
    return bool(a) and (a == b or a.endswith("/" + b) or b.endswith("/" + a))


def overlaps(finding: dict, file: str, start: int, end: int, tol: int = TOLERANCE) -> bool:
    if not same_file(finding.get("file", ""), file):
        return False
    fs, fe = finding.get("line_start", 0), finding.get("line_end", 0) or finding.get("line_start", 0)
    if fs <= 0:
        return False
    fs, fe = min(fs, fe), max(fs, fe)
    return fs <= end + tol and fe >= start - tol


def candidates(finding: dict, spots: list[Spot]) -> list[str]:
    return [s.id for s in spots if any(overlaps(finding, *loc) for loc in s.locations)]


# ---------- extraction ----------

def extract_one(raw_file: Path, out_file: Path, model: str) -> str:
    if out_file.exists():
        return "cached"
    rec = json.loads(raw_file.read_text())
    if rec.get("is_error"):
        return "skip-error"
    answer = rec.get("answer") or ""
    with tempfile.TemporaryDirectory(prefix="rb-x-") as tmp:
        res = claude.run_json(_prompt("extractor.md").replace("{review}", answer),
                              FINDINGS_SCHEMA, Path(tmp), model=model)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps({**res["data"], "extract_cost_usd": res["cost_usd"]}, indent=2))
    return "ok"


def extract_all(run_dir: Path, model: str, workers: int) -> None:
    raws = sorted((run_dir / "raw").rglob("run*.json"))
    jobs = [(r, run_dir / "findings" / r.relative_to(run_dir / "raw")) for r in raws]
    _parallel(jobs, lambda j: extract_one(*j, model), workers, "extract")


# ---------- grading ----------

def _fmt_spots(spots: list[Spot], key: str) -> str:
    if not spots:
        return "(none)"
    rows = []
    for s in spots:
        locs = ", ".join(f"{f}:{a}-{b}" for f, a, b in s.locations)
        rows.append(f"- id={s.id} at {locs}: {s.info.get(key, '')}"
                    + (f" (trigger: {s.info['trigger']})" if s.info.get("trigger") else ""))
    return "\n".join(rows)


def grade_one(case: Case, findings_file: Path, out_file: Path, model: str) -> str:
    if out_file.exists():
        return "cached"
    findings = json.loads(findings_file.read_text())["findings"]
    rows = []
    for i, f in enumerate(findings):
        rows.append({**f, "index": i, "candidates": candidates(f, case.bugs),
                     "decoy_spot": candidates(f, case.known_ok)})
    judged: dict[int, dict] = {}
    judge_cost = 0.0
    if rows:
        listing = "\n".join(
            f"- index={r['index']} [{r['severity']}] {r['file']}:{r['line_start']}-{r['line_end']}: "
            f"{r['summary']} (candidates: {r['candidates'] or '[]'})" for r in rows)
        prompt = (_prompt("judge.md").replace("{bugs}", _fmt_spots(case.bugs, "summary"))
                  .replace("{known_ok}", _fmt_spots(case.known_ok, "note"))
                  .replace("{findings}", listing))
        with tempfile.TemporaryDirectory(prefix="rb-j-") as tmp:
            res = claude.run_json(prompt, JUDGE_SCHEMA, Path(tmp), model=model)
        judge_cost = res["cost_usd"] or 0.0
        judged = {g["index"]: g for g in res["data"]["grades"]}
    for r in rows:
        j = judged.get(r["index"], {"same_bug_as": None, "verdict": "unsure", "reason": "not graded"})
        hit = j["same_bug_as"] if j["same_bug_as"] in r["candidates"] else None
        if hit:
            label = "hit"
        elif j["verdict"] == "valid_other":
            label = "valid_other"
        elif j["verdict"] == "unsure":
            label = "unsure"
        else:
            label = "false_alarm"
        r.update({"judge": j, "hit_bug": hit, "label": label})
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps({"case": case.id, "kind": case.kind, "findings": rows,
                                    "judge_cost_usd": judge_cost}, indent=2))
    return "ok"


def grade_all(run_dir: Path, cases: dict[str, Case], model: str, workers: int) -> None:
    jobs = []
    for f in sorted((run_dir / "findings").rglob("run*.json")):
        rel = f.relative_to(run_dir / "findings")
        case_id = rel.parts[1]
        jobs.append((cases[case_id], f, run_dir / "grades" / rel))
    _parallel(jobs, lambda j: grade_one(*j, model), workers, "grade")


def _parallel(jobs, fn, workers: int, label: str) -> None:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(fn, j): j for j in jobs}
        for n, fut in enumerate(as_completed(futs), start=1):
            j = futs[fut]
            name = "/".join(Path(j[-1]).parts[-3:])
            try:
                status = fut.result()
            except claude.AccountError as e:
                print(f"STOPPING {label}: account problem ({e}); re-run to resume.", flush=True)
                pool.shutdown(cancel_futures=True)
                raise SystemExit(3)
            except Exception as e:
                status = f"ERROR {e}"
            print(f"[{label} {n}/{len(jobs)}] {name}: {status}", flush=True)
