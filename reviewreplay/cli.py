"""reviewreplay command line.

  reviewreplay doctor [--login]                    check git, claude, Python and the cache folder
  reviewreplay init  [REPO] --out .reviewreplay   build a benchmark from a repo's own bugs
  reviewreplay check [CASES_DIR]
  reviewreplay make-patch CASE_DIR...
  reviewreplay run    --out results/<id> [--subjects a,b] [--cases DIR] [--runs 3]
  reviewreplay extract results/<id>
  reviewreplay grade   results/<id>
  reviewreplay verify  results/<id>                check `unsure` findings against the code
  reviewreplay report  results/<id>
  reviewreplay compare results/<a> results/<b> [--kind real] [--out FILE.md]
  reviewreplay label   results/<id>/labels.csv
  reviewreplay mine    https://github.com/<owner>/<repo> [--since 2025-06-01]
  reviewreplay agreement results/<id>/labels.csv
  reviewreplay comment  results/<id> --out comment.md   the scorecard as a PR comment (CI)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import claude, doctor
from .cases import check_case, find_case_dirs, load_cases, make_patch
from .ci import write_comment
from .compare import write_comparison
from .grade import extract_all, grade_all, wanted_judges
from .init import init, usable_candidates
from .label import label_sheet
from .mine import as_dicts, mine, table
from .report import agreement, write_label_sheet, write_report
from .runner import run_all
from .subjects import BUILTIN_SUBJECTS, load_subjects
from .verify import MAX_LIB_MB, verify_all


def _cases(path: str | None):
    return load_cases(Path(path) if path else Path("cases"))


def _subjects_dir() -> Path:
    """./subjects if the current folder has one, else the built-in reviewers."""
    return Path("subjects") if Path("subjects").is_dir() else BUILTIN_SUBJECTS


_NO_CANDIDATES = ("no usable fix commits since {since}. Try an earlier --since (e.g. 2023-01-01), "
                  "or --pattern with your project's wording for fixes (e.g. 'fix|bug|regress').")


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
    p.add_argument("--dry-run", action="store_true", help="list usable fixes and stop; spends nothing")

    p = sub.add_parser("doctor", help="check git, claude, Python and the cache folder")
    p.add_argument("--login", action="store_true",
                   help="also send one tiny prompt to check the claude login works")

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
    p.add_argument("--dry-run", action="store_true", help="show reviews, cost and time; run nothing")

    for name in ("extract", "grade"):
        p = sub.add_parser(name)
        p.add_argument("run_dir")
        p.add_argument("--model", default=claude.DEFAULT_MODEL)
        p.add_argument("--workers", type=int, default=4)
        p.add_argument("--cases")
        if name == "grade":
            p.add_argument("--force", action="store_true", help="re-grade even if grades exist")
            p.add_argument("--judges", type=int, default=1,
                           help="judge votes per review with --model (existing grades count as one)")
            p.add_argument("--second-judge", help="add votes from a different judge model")
            p.add_argument("--second-votes", type=int, default=1)

    p = sub.add_parser("verify", help="check `unsure` findings against the code (read-only)")
    p.add_argument("run_dir")
    p.add_argument("--model", default=claude.DEFAULT_MODEL)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--cases")
    p.add_argument("--force", action="store_true", help="check again even if a result exists")
    p.add_argument("--all-severities", action="store_true",
                   help="also check minor findings (default: blocking and important only)")
    p.add_argument("--kind", help="check one case kind only (real, planted, clean, decoy)")
    p.add_argument("--max-lib-mb", type=int, default=MAX_LIB_MB,
                   help="largest library download to fetch for a claim")

    p = sub.add_parser("report")
    p.add_argument("run_dir")
    p.add_argument("--cases")

    p = sub.add_parser("compare", help="combine several runs into one table, paired vs a baseline")
    p.add_argument("run_dirs", nargs="+")
    p.add_argument("--kind", help="keep one case kind (real, planted, clean, decoy)")
    p.add_argument("--baseline", default="baseline")
    p.add_argument("--drop-contested", action="store_true",
                   help="leave out findings the judges split on")
    p.add_argument("--ignore-verify", action="store_true",
                   help="use the judges' labels only, without `verify` results")
    p.add_argument("--out", help="also write the table here (.md), with a .json beside it")
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

    p = sub.add_parser("comment", help="write the scorecard as a pull-request comment (for CI)")
    p.add_argument("run_dir", nargs="?")
    p.add_argument("--out", required=True)
    p.add_argument("--dry-run-file", help="a saved `run --dry-run` output to post instead")
    p.add_argument("--run-url", help="link to the workflow run")

    p = sub.add_parser("agreement", help="judge vs. human labels (Cohen's kappa)")
    p.add_argument("sheet")

    a = ap.parse_args(argv)

    if a.cmd == "doctor":
        return 0 if doctor.print_checks(doctor.checks(login=a.login)) else 1

    if a.cmd == "init":
        out = Path(a.out)
        if a.dry_run:
            cands = usable_candidates(a.repo, since=a.since, max_cases=a.max_cases, pattern=a.pattern)
            if not cands:
                print(_NO_CANDIDATES.format(since=a.since))
                return 1
            n = min(len(cands), a.max_cases)
            print(f"{len(cands)} usable fix commit(s) since {a.since}; init would try them in order "
                  f"until {n} draft case(s) are made, one model call each.")
            for c in cands[:n]:
                print(f"  {c.fix[:10]}  {c.subject[:70]}")
            print("Nothing was drafted (--dry-run).")
            return 0
        if not doctor.preflight():
            return 1
        report = init(a.repo, out, since=a.since, max_cases=a.max_cases, model=a.model,
                      pattern=a.pattern)
        for fix, msg in report:
            print(f"{fix}  {msg}")
        if not report:
            print(_NO_CANDIDATES.format(since=a.since))
            return 1
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
        if not cases:
            print(f"no cases found in {a.cases or 'cases'}: run `reviewreplay init` first, or pass --cases DIR")
            return 1
        if a.dry_run:
            print(doctor.describe_run([c.id for c in cases], [s.name for s in subjects], a.runs,
                                      Path(a.out), a.workers))
            return 0
        if not doctor.preflight():
            return 1
        run_all(cases, subjects, a.runs, Path(a.out), model=a.model, budget=a.budget,
                workers=a.workers, total_budget=a.total_budget)
        return 0

    if a.cmd == "extract":
        extract_all(Path(a.run_dir), a.model, a.workers)
        return 0

    if a.cmd == "grade":
        cases = {c.id: c for c in _cases(a.cases)}
        judges = wanted_judges(a.model, a.judges, a.second_judge, a.second_votes)
        grade_all(Path(a.run_dir), cases, a.model, a.workers, force=a.force, judges=judges)
        return 0

    if a.cmd == "verify":
        cases = {c.id: c for c in _cases(a.cases)}
        verify_all(Path(a.run_dir), cases, a.model, a.workers, force=a.force,
                   all_severities=a.all_severities, limit_mb=a.max_lib_mb, kind=a.kind)
        return 0

    if a.cmd == "compare":
        cases = {c.id: c for c in _cases(a.cases)}
        print(write_comparison([Path(d) for d in a.run_dirs], cases, Path(a.out) if a.out else None,
                               kind=a.kind, baseline=a.baseline, drop_contested=a.drop_contested,
                               use_checks=not a.ignore_verify))
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

    if a.cmd == "comment":
        print(write_comment(Path(a.out), run_dir=Path(a.run_dir) if a.run_dir else None,
                            dry_run_file=Path(a.dry_run_file) if a.dry_run_file else None,
                            run_url=a.run_url))
        return 0

    if a.cmd == "agreement":
        print(json.dumps(agreement(Path(a.sheet)), indent=2))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
