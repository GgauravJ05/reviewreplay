"""reviewreplay command line.

  reviewreplay init  [REPO] --out .reviewreplay   build a benchmark from a repo's own bugs
  reviewreplay check [CASES_DIR]
  reviewreplay make-patch CASE_DIR...
  reviewreplay run    --out results/<id> [--subjects a,b] [--cases DIR] [--runs 3]
  reviewreplay extract results/<id>
  reviewreplay grade   results/<id>
  reviewreplay report  results/<id>
  reviewreplay label   results/<id>/labels.csv
  reviewreplay mine    https://github.com/<owner>/<repo> [--since 2025-06-01]
  reviewreplay agreement results/<id>/labels.csv
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import claude
from .cases import check_case, find_case_dirs, load_cases, make_patch
from .grade import extract_all, grade_all
from .init import init
from .label import label_sheet
from .mine import as_dicts, mine, table
from .report import agreement, write_label_sheet, write_report
from .runner import run_all
from .subjects import BUILTIN_SUBJECTS, load_subjects


def _cases(path: str | None):
    return load_cases(Path(path) if path else Path("cases"))


def _subjects_dir() -> Path:
    """./subjects if the current folder has one, else the built-in reviewers."""
    return Path("subjects") if Path("subjects").is_dir() else BUILTIN_SUBJECTS


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="reviewreplay")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="draft cases from a repository's own fixed bugs")
    p.add_argument("repo", nargs="?", default=".")
    p.add_argument("--out", default=".reviewreplay")
    p.add_argument("--since", default="2024-01-01")
    p.add_argument("--max-cases", type=int, default=10)
    p.add_argument("--model", default=claude.DEFAULT_MODEL)
    p.add_argument("--pattern", help="commit-message regex for fix commits")

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
    p.add_argument("--include-drafts", action="store_true", help="also run unconfirmed draft cases")

    for name in ("extract", "grade"):
        p = sub.add_parser(name)
        p.add_argument("run_dir")
        p.add_argument("--model", default=claude.DEFAULT_MODEL)
        p.add_argument("--workers", type=int, default=4)
        p.add_argument("--cases")
        if name == "grade":
            p.add_argument("--force", action="store_true", help="re-grade even if grades exist")

    p = sub.add_parser("report")
    p.add_argument("run_dir")
    p.add_argument("--cases")

    p = sub.add_parser("label", help="hand-label findings blind, one at a time")
    p.add_argument("sheet")
    p.add_argument("--cases")

    p = sub.add_parser("mine", help="list candidate real bugs (fix + introducing commit)")
    p.add_argument("repo")
    p.add_argument("--since", default="2025-06-01")
    p.add_argument("--limit", type=int, default=40)
    p.add_argument("--json", help="also write candidates to this file")
    p.add_argument("--pattern", help="commit-message regex (default: regression wording)")

    p = sub.add_parser("agreement", help="judge vs. human labels (Cohen's kappa)")
    p.add_argument("sheet")

    a = ap.parse_args(argv)

    if a.cmd == "init":
        out = Path(a.out)
        report = init(a.repo, out, since=a.since, max_cases=a.max_cases, model=a.model,
                      pattern=a.pattern)
        for fix, msg in report:
            print(f"{fix}  {msg}")
        drafted = sum(1 for _, m in report if m == "drafted")
        print(f"\n{drafted} draft case(s) in {out / 'cases'}. Confirm each (see its NOTES.md), then:\n"
              f"  reviewreplay run --cases {out / 'cases'} --out {out / 'results'} --include-drafts")
        return 0

    if a.cmd == "check":
        root = Path(a.cases) if a.cases else Path("cases")
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
            if json.loads((Path(d) / "case.json").read_text()).get("kind") == "real":
                print(f"skip {d}: real cases generate their patch from git")
                continue
            make_patch(Path(d))
            print(f"wrote {Path(d) / 'change.patch'}")
        return 0

    if a.cmd == "run":
        cases = _cases(a.cases)
        drafts = [c.id for c in cases if c.meta.get("status") == "draft"]
        if drafts and not a.include_drafts:
            print(f"skipping {len(drafts)} draft case(s) (confirm them or pass --include-drafts)")
            cases = [c for c in cases if c.meta.get("status") != "draft"]
        subjects = load_subjects(_subjects_dir(), a.subjects.split(",") if a.subjects else None)
        run_all(cases, subjects, a.runs, Path(a.out), model=a.model, budget=a.budget,
                workers=a.workers, total_budget=a.total_budget)
        return 0

    if a.cmd == "extract":
        extract_all(Path(a.run_dir), a.model, a.workers)
        return 0

    if a.cmd == "grade":
        cases = {c.id: c for c in _cases(a.cases)}
        grade_all(Path(a.run_dir), cases, a.model, a.workers, force=a.force)
        return 0

    if a.cmd == "report":
        cases = {c.id: c for c in _cases(a.cases)}
        out = write_report(Path(a.run_dir), cases)
        sheet = write_label_sheet(Path(a.run_dir))
        print(out.read_text())
        print(f"label sheet: {sheet}")
        return 0

    if a.cmd == "label":
        label_sheet(Path(a.sheet), {c.id: c for c in _cases(a.cases)})
        return 0

    if a.cmd == "mine":
        cands = mine(a.repo, a.since, a.limit, *([a.pattern] if a.pattern else []))
        print(table(cands))
        if a.json:
            Path(a.json).write_text(json.dumps(as_dicts(cands), indent=2))
        return 0

    if a.cmd == "agreement":
        print(json.dumps(agreement(Path(a.sheet)), indent=2))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
