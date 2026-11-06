"""reviewbench command line.

  python -m reviewbench check [CASES_DIR]
  python -m reviewbench make-patch CASE_DIR...
  python -m reviewbench run    --out results/<id> [--subjects a,b] [--cases DIR] [--runs 3]
  python -m reviewbench extract results/<id>
  python -m reviewbench grade   results/<id>
  python -m reviewbench report  results/<id>
  python -m reviewbench agreement results/<id>/labels.csv
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import claude
from .cases import check_case, find_case_dirs, load_cases, make_patch
from .grade import extract_all, grade_all
from .report import agreement, write_label_sheet, write_report
from .runner import run_all
from .subjects import ROOT, load_subjects


def _cases(path: str | None):
    return load_cases(Path(path) if path else ROOT / "cases")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="reviewbench")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("check", help="validate cases")
    p.add_argument("cases", nargs="?")

    p = sub.add_parser("make-patch", help="regenerate change.patch from base/ and after/")
    p.add_argument("case_dirs", nargs="+")

    p = sub.add_parser("run", help="run reviews")
    p.add_argument("--out", required=True)
    p.add_argument("--subjects")
    p.add_argument("--cases")
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--model", default=claude.DEFAULT_MODEL)
    p.add_argument("--budget", type=float, default=1.0, help="max est. $ per review")
    p.add_argument("--total-budget", type=float, help="stop the run after this est. $")
    p.add_argument("--workers", type=int, default=3)

    for name in ("extract", "grade"):
        p = sub.add_parser(name)
        p.add_argument("run_dir")
        p.add_argument("--model", default=claude.DEFAULT_MODEL)
        p.add_argument("--workers", type=int, default=4)
        p.add_argument("--cases")

    p = sub.add_parser("report")
    p.add_argument("run_dir")
    p.add_argument("--cases")

    p = sub.add_parser("agreement", help="judge vs. human labels (Cohen's kappa)")
    p.add_argument("sheet")

    a = ap.parse_args(argv)

    if a.cmd == "check":
        root = Path(a.cases) if a.cases else ROOT / "cases"
        bad = 0
        for d in find_case_dirs(root):
            problems = check_case(d)
            print(f"{'FAIL' if problems else 'ok  '} {d.relative_to(root)}")
            for prob in problems:
                print(f"     - {prob}")
            bad += bool(problems)
        print(f"{bad} failing case(s)")
        return 1 if bad else 0

    if a.cmd == "make-patch":
        for d in a.case_dirs:
            make_patch(Path(d))
            print(f"wrote {Path(d) / 'change.patch'}")
        return 0

    if a.cmd == "run":
        cases = _cases(a.cases)
        subjects = load_subjects(ROOT / "subjects", a.subjects.split(",") if a.subjects else None)
        run_all(cases, subjects, a.runs, Path(a.out), model=a.model, budget=a.budget,
                workers=a.workers, total_budget=a.total_budget)
        return 0

    if a.cmd == "extract":
        extract_all(Path(a.run_dir), a.model, a.workers)
        return 0

    if a.cmd == "grade":
        cases = {c.id: c for c in _cases(a.cases)}
        grade_all(Path(a.run_dir), cases, a.model, a.workers)
        return 0

    if a.cmd == "report":
        cases = {c.id: c for c in _cases(a.cases)}
        out = write_report(Path(a.run_dir), cases)
        sheet = write_label_sheet(Path(a.run_dir))
        print(out.read_text())
        print(f"label sheet: {sheet}")
        return 0

    if a.cmd == "agreement":
        print(json.dumps(agreement(Path(a.sheet)), indent=2))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
