"""② Run reviews: every (subject, case, run index) once, resumable, a few in parallel."""
from __future__ import annotations

import json
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from . import claude
from .cases import Case
from .subjects import Subject, build_workspace

READ_ONLY = ["--allowedTools", "Read,Grep,Glob,Bash(git diff:*),Bash(git log:*),Bash(git show:*),Bash(git status:*)",
             "--disallowedTools", "Edit,Write,NotebookEdit,WebFetch,WebSearch"]


def raw_path(out: Path, subject: str, case_id: str, k: int) -> Path:
    return out / "raw" / subject / case_id / f"run{k}.json"


def review_once(case: Case, subject: Subject, k: int, out: Path, model: str, budget: float) -> dict:
    path = raw_path(out, subject.name, case.id, k)
    if path.exists():
        prev = json.loads(path.read_text())
        if not prev.get("is_error"):
            return {"skipped": True, **{x: prev.get(x) for x in ("subject", "case", "run")}}
    with tempfile.TemporaryDirectory(prefix="rb-") as tmp:
        ws = build_workspace(case, subject, Path(tmp))
        rec = claude.run_stream(subject.prompt, ws, model=model,
                                extra=[*READ_ONLY, "--max-budget-usd", str(budget)])
    rec.update({
        "subject": subject.name, "case": case.id, "run": k, "model": model,
        "prompt": subject.prompt, "skill": subject.skill,
        "when": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, indent=2))
    return rec


def run_all(cases: list[Case], subjects: list[Subject], runs: int, out: Path, *, model: str,
            budget: float, workers: int, total_budget: float | None = None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    cfg = out / "config.json"
    if not cfg.exists():
        cfg.write_text(json.dumps({
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "model": model, "cli_version": claude.cli_version(), "runs": runs,
            "cases": [c.id for c in cases],
            "subjects": [{"name": s.name, "skill": s.skill, "prompt": s.prompt, "credit": s.credit}
                         for s in subjects],
        }, indent=2))
    jobs = [(c, s, k) for k in range(1, runs + 1) for s in subjects for c in cases]
    spent = 0.0
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(review_once, c, s, k, out, model, budget): (c.id, s.name, k)
                for c, s, k in jobs}
        for fut in as_completed(futs):
            cid, sname, k = futs[fut]
            done += 1
            try:
                rec = fut.result()
            except Exception as e:  # keep going; a failed review is retried on the next run
                print(f"[{done}/{len(jobs)}] {sname} {cid} run{k}: ERROR {e}", flush=True)
                continue
            if rec.get("skipped"):
                print(f"[{done}/{len(jobs)}] {sname} {cid} run{k}: cached", flush=True)
                continue
            spent += rec.get("cost_usd") or 0
            flag = "ERR" if rec.get("is_error") else "ok"
            print(f"[{done}/{len(jobs)}] {sname} {cid} run{k}: {flag} {rec['seconds']}s "
                  f"${rec.get('cost_usd') or 0:.3f} skills={rec['skills_invoked']} total=${spent:.2f}",
                  flush=True)
            if total_budget and spent > total_budget:
                print(f"budget {total_budget} reached; stopping (re-run to resume)", flush=True)
                pool.shutdown(cancel_futures=True)
                break
