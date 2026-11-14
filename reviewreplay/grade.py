"""③ Extract findings and ④ grade them against the answer key.

Extraction: one structured call per review turns free text into findings (same prompt for every subject).
Grading, two stages:
  1. location match (code): a finding is a *candidate* for a truth bug if it names the same file and its
     line range overlaps one of the bug's locations (± TOLERANCE lines). If no bug is that close, a
     finding in the same file within ± APPROX_TOLERANCE lines still reaches the judge (`match: "approx"`):
     reviewers often cite lines from memory ("~212"). Decoy traps are found against `known_ok` spots
     with the strict tolerance only, so a wider window never hides a false alarm.
  2. judge (one structured call per review): decides whether each candidate is the *same defect*, and
     classifies everything else as valid_other / invalid / unsure.
A finding counts as a hit only if both stages agree.

Several judges (`grade --judges N --second-judge MODEL`): each judge run is kept in `judge_runs`, every
finding gets its `votes`, the majority `label`, and `contested` when no label has a strict majority.
A grade file from a single judge counts as the first vote, so adding judges only runs the new ones.
"""
from __future__ import annotations

import json
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import claude
from .cases import Case, Spot

PKG = Path(__file__).resolve().parent
TOLERANCE = 3
APPROX_TOLERANCE = 15   # bugs only: a cited line this close still reaches the judge
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
    return (PKG / "prompts" / name).read_text(encoding="utf-8")


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


def location_match(finding: dict, spots: list[Spot], *, no_line_same_file: bool = False,
                   approx_tol: int | None = None) -> tuple[list[str], str | None]:
    """Spots the finding may describe, and how they matched: "exact" (within ± TOLERANCE), "approx"
    (no exact match, but within ± approx_tol in the same file) or "file" (no_line_same_file: the
    finding gives no line at all, so any spot in the same file). The judge's same-defect rule decides."""
    hit = [s.id for s in spots if any(overlaps(finding, *loc) for loc in s.locations)]
    if hit:
        return hit, "exact"
    if approx_tol is not None and finding.get("line_start", 0) > 0:
        hit = [s.id for s in spots if any(overlaps(finding, *loc, tol=approx_tol) for loc in s.locations)]
        if hit:
            return hit, "approx"
    if no_line_same_file and finding.get("line_start", 0) <= 0:
        hit = [s.id for s in spots
               if any(same_file(finding.get("file", ""), loc[0]) for loc in s.locations)]
        if hit:
            return hit, "file"
    return [], None


def candidates(finding: dict, spots: list[Spot], *, no_line_same_file: bool = False,
               approx_tol: int | None = None) -> list[str]:
    return location_match(finding, spots, no_line_same_file=no_line_same_file, approx_tol=approx_tol)[0]


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


def label_for(row: dict, j: dict) -> str:
    """One judge's verdict on one finding → hit / valid_other / unsure / false_alarm."""
    if j.get("same_bug_as") and j["same_bug_as"] in row["candidates"]:
        return "hit"
    if j.get("verdict") == "valid_other":
        return "valid_other"
    if j.get("verdict") == "unsure":
        return "unsure"
    return "false_alarm"


def tally(labels: list[str]) -> tuple[str, bool, float]:
    """Majority label, contested flag and agreement share. A finding is contested when no label has
    a strict majority; the first vote's label breaks the tie."""
    counts: dict[str, int] = {}
    for lab in labels:
        counts[lab] = counts.get(lab, 0) + 1
    top = max(counts.values())
    winners = [lab for lab in labels if counts[lab] == top]      # in vote order
    label = winners[0]
    return label, top * 2 <= len(labels), top / len(labels)


def wanted_judges(model: str, judges: int = 1, second_judge: str | None = None,
                  second_votes: int = 1) -> list[str]:
    return [model] * max(1, judges) + ([second_judge] * second_votes if second_judge else [])


def _legacy_runs(old: dict, model: str) -> list[dict]:
    """A grade file written before multi-judge: its one judge call becomes the first vote."""
    if "judge_runs" in old:
        return old["judge_runs"]
    return [{"model": old.get("judge_model", model), "cost_usd": old.get("judge_cost_usd", 0.0),
             "grades": {str(f["index"]): f["judge"] for f in old["findings"] if "judge" in f}}]


def _missing(have: list[dict], want: list[str]) -> list[str]:
    left = [r["model"] for r in have]
    out = []
    for m in want:
        if m in left:
            left.remove(m)
        else:
            out.append(m)
    return out


def _judge_prompt(case: Case, rows: list[dict]) -> str:
    listing = "\n".join(
        f"- index={r['index']} [{r['severity']}] {r['file']}:{r['line_start']}-{r['line_end']}: "
        f"{r['summary']} (candidates: {r['candidates'] or '[]'})" for r in rows)
    return (_prompt("judge.md").replace("{bugs}", _fmt_spots(case.bugs, "summary"))
            .replace("{known_ok}", _fmt_spots(case.known_ok, "note"))
            .replace("{related}", "\n".join(f"- {r}" for r in case.related_valid) or "(none)")
            .replace("{findings}", listing))


def _call_judge(prompt: str, model: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="rb-j-") as tmp:
        res = claude.run_json(prompt, JUDGE_SCHEMA, Path(tmp), model=model)
    return {"model": model, "cost_usd": res["cost_usd"] or 0.0,
            "grades": {str(g["index"]): g for g in res["data"]["grades"]}}


def apply_votes(rows: list[dict], runs: list[dict]) -> None:
    """Fill each finding's votes, label and contested flag from the judge runs."""
    for r in rows:
        votes = []
        for run in runs:
            j = run["grades"].get(str(r["index"]),
                                  {"same_bug_as": None, "verdict": "unsure", "reason": "not graded"})
            votes.append({"model": run["model"], "label": label_for(r, j), "same_bug_as": j.get("same_bug_as"),
                          "verdict": j.get("verdict"), "reason": j.get("reason", "")})
        label, contested, share = tally([v["label"] for v in votes])
        first = runs[0]["grades"].get(str(r["index"]), {"same_bug_as": None, "verdict": "unsure",
                                                        "reason": "not graded"})
        hit = next((v["same_bug_as"] for v in votes if v["label"] == "hit"), None) if label == "hit" else None
        r.update({"judge": first, "votes": votes, "hit_bug": hit, "label": label,
                  "contested": contested, "agreement": share})


def grade_one(case: Case, findings_file: Path, out_file: Path, model: str, force: bool = False,
              judges: list[str] | None = None, call=_call_judge) -> str:
    want = judges or [model]
    findings = json.loads(findings_file.read_text())["findings"]
    rows = []
    for i, f in enumerate(findings):
        hit, how = location_match(f, case.bugs, no_line_same_file=True, approx_tol=APPROX_TOLERANCE)
        rows.append({**f, "index": i, "candidates": hit, "match": how,
                     "decoy_spot": candidates(f, case.known_ok)})
    have: list[dict] = []
    if out_file.exists() and not force:
        have = _legacy_runs(json.loads(out_file.read_text()), model)
    todo = _missing(have, want) if rows else []
    if out_file.exists() and not force and not todo:
        return "cached"
    if todo:
        prompt = _judge_prompt(case, rows)
        have = have + [call(prompt, m) for m in todo]
    if rows:
        apply_votes(rows, have)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps({"case": case.id, "kind": case.kind, "findings": rows,
                                    "judge_runs": have,
                                    "judge_cost_usd": sum(r["cost_usd"] for r in have)}, indent=2))
    return f"ok ({len(todo)} new vote{'s' if len(todo) != 1 else ''})" if todo else "ok"


def grade_all(run_dir: Path, cases: dict[str, Case], model: str, workers: int,
              force: bool = False, judges: list[str] | None = None) -> None:
    jobs = []
    for f in sorted((run_dir / "findings").rglob("run*.json")):
        rel = f.relative_to(run_dir / "findings")
        case_id = rel.parts[1]
        if case_id not in cases:            # `--cases cases/real` grades only the real cases
            continue
        jobs.append((cases[case_id], f, run_dir / "grades" / rel))
    _parallel(jobs, lambda j: grade_one(*j, model, force, judges), workers, "grade")


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
