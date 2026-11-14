"""Tests for the deterministic parts of grading and reporting (no Claude calls)."""
from __future__ import annotations

import csv
from pathlib import Path

from reviewreplay.cases import Spot, load_case, load_cases
from reviewreplay.grade import APPROX_TOLERANCE, candidates, grade_one, location_match, norm_path, overlaps
from reviewreplay.report import agreement, bootstrap, review_scores

ROOT = Path(__file__).resolve().parents[1]


def spot(file: str, a: int, b: int, also=()) -> Spot:
    return Spot(id="b1", file=file, lines=(a, b), info={}, also=list(also))


# ---- location matching ----

def test_norm_path_strips_prefixes_and_line_suffix():
    assert norm_path("./shop/checkout.py") == "shop/checkout.py"
    assert norm_path("`shop/checkout.py:12`") == "shop/checkout.py"


def test_overlap_within_tolerance():
    f = {"file": "shop/checkout.py", "line_start": 15, "line_end": 15}
    assert overlaps(f, "shop/checkout.py", 12, 13)          # 2 lines away, tolerance 3
    assert not overlaps(f, "shop/checkout.py", 1, 5)        # 10 lines away


def test_overlap_requires_same_file_and_a_line():
    assert not overlaps({"file": "other.py", "line_start": 12, "line_end": 12}, "shop/checkout.py", 12, 13)
    assert not overlaps({"file": "shop/checkout.py", "line_start": 0, "line_end": 0}, "shop/checkout.py", 12, 13)


def test_overlap_accepts_suffix_paths_and_reversed_ranges():
    assert overlaps({"file": "checkout.py", "line_start": 13, "line_end": 12}, "shop/checkout.py", 12, 13)


def test_lineless_finding_matches_bug_in_same_file_only_when_asked():
    bug = spot("src/a.py", 40, 42)
    f = {"file": "src/a.py", "line_start": 0, "line_end": 0}
    assert candidates(f, [bug]) == []
    assert candidates(f, [bug], no_line_same_file=True) == ["b1"]
    assert candidates({"file": "src/b.py", "line_start": 0}, [bug], no_line_same_file=True) == []
    assert candidates({"file": "src/a.py", "line_start": 90}, [bug], no_line_same_file=True) == []


def test_candidates_use_alternate_locations():
    s = spot("shop/checkout.py", 12, 13, also=[("shop/config.py", 6, 6)])
    assert candidates({"file": "shop/config.py", "line_start": 6, "line_end": 6}, [s]) == ["b1"]



# ---- approximate lines (bugs only) ----

REAL002 = "src/datasets/utils/extract.py"


def test_approx_line_reaches_judge_for_real002_badpath():
    # real-002: a reviewer described the startswith(base) bug at "~212"; the spot is lines 206-208
    bug = spot(REAL002, 206, 208, also=[(REAL002, 259, 261), (REAL002, 335, 337)])
    f = {"file": REAL002, "line_start": 212, "line_end": 212}
    assert candidates(f, [bug]) == []                                   # outside ±3
    assert location_match(f, [bug], approx_tol=APPROX_TOLERANCE) == (["b1"], "approx")
    f = {"file": REAL002, "line_start": 199, "line_end": 199}           # 7 lines before the spot
    assert location_match(f, [bug], approx_tol=APPROX_TOLERANCE) == (["b1"], "approx")


def test_exact_match_wins_over_approx():
    f = {"file": REAL002, "line_start": 207, "line_end": 207}
    assert location_match(f, [spot(REAL002, 206, 208)], approx_tol=APPROX_TOLERANCE) == (["b1"], "exact")


def test_approx_window_does_not_reach_far_lines_or_other_files():
    bug = spot(REAL002, 206, 208)
    far = {"file": REAL002, "line_start": 408, "line_end": 408}         # 200 lines away
    other = {"file": "src/datasets/load.py", "line_start": 210, "line_end": 210}
    assert location_match(far, [bug], approx_tol=APPROX_TOLERANCE) == ([], None)
    assert location_match(other, [bug], approx_tol=APPROX_TOLERANCE) == ([], None)


def test_decoys_keep_strict_tolerance(tmp_path):
    import json
    from reviewreplay.cases import Case
    bug, decoy = spot("shop/a.py", 100, 101), Spot(id="d1", file="shop/a.py", lines=(10, 11), info={})
    case = Case(id="c1", kind="clean", track="python", title="t", path=tmp_path, meta={}, tree=tmp_path,
                bugs=[bug], known_ok=[decoy])
    findings = tmp_path / "f.json"
    findings.write_text(json.dumps({"findings": [
        {"file": "shop/a.py", "line_start": 20, "line_end": 20, "severity": "important", "summary": "s"},
        {"file": "shop/a.py", "line_start": 110, "line_end": 110, "severity": "important", "summary": "s"}]}))
    out = tmp_path / "g.json"
    fake = lambda prompt, model: {"model": model, "cost_usd": 0.0, "grades": {}}
    grade_one(case, findings, out, "m", call=fake)
    rows = json.loads(out.read_text())["findings"]
    assert rows[0]["decoy_spot"] == []                                  # 9 lines from the decoy: not a trap
    assert rows[1]["candidates"] == ["b1"] and rows[1]["match"] == "approx"

# ---- per-review scores ----

class FakeCase:
    def __init__(self, kind, has_bug):
        self.kind, self.has_bug = kind, has_bug


def f(label, severity="blocking", decoy=()):
    return {"label": label, "severity": severity, "decoy_spot": list(decoy)}


def test_bug_case_caught_and_precision():
    s = review_scores({"findings": [f("hit"), f("false_alarm"), f("false_alarm", "minor")]},
                      {"cost_usd": 0.1, "seconds": 9}, FakeCase("planted", True), None)
    assert s["caught"] == 1.0
    assert s["precision"] == 0.5          # minor findings don't count toward precision


def test_bug_case_hit_at_minor_still_counts_as_caught():
    s = review_scores({"findings": [f("hit", "minor")]}, {}, FakeCase("planted", True), None)
    assert s["caught"] == 1.0 and "precision" not in s


def test_clean_case_valid_other_is_not_a_false_alarm():
    s = review_scores({"findings": [f("valid_other")]}, {}, FakeCase("clean", False), None)
    assert s["clean_pass"] == 1.0


def test_decoy_trap():
    s = review_scores({"findings": [f("false_alarm", "important", decoy=["ok1"])]}, {},
                      FakeCase("decoy", False), None)
    assert s["clean_pass"] == 0.0 and s["trapped"] == 1.0


def test_valid_finding_near_decoy_spot_is_not_a_trap():
    s = review_scores({"findings": [f("valid_other", "important", decoy=["ok3"])]}, {},
                      FakeCase("decoy", False), None)
    assert s["clean_pass"] == 1.0 and s["trapped"] == 0.0


def test_skill_used_flag():
    s = review_scores({"findings": []}, {"skills_invoked": ["code-review-skill"]},
                      FakeCase("clean", False), "code-review-skill")
    assert s["skill_used"] is True


# ---- statistics ----

def test_bootstrap_bounds_contain_mean():
    m, lo, hi = bootstrap([0.0, 1.0, 1.0, 0.0, 1.0])
    assert lo <= m <= hi and m == 0.6


def test_agreement_kappa(tmp_path):
    sheet = tmp_path / "labels.csv"
    with sheet.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["auto_label", "human_label"])
        w.writeheader()
        for a, h in [("hit", "hit"), ("hit", "hit"), ("false_alarm", "false_alarm"), ("false_alarm", "hit"), ("hit", "")]:
            w.writerow({"auto_label": a, "human_label": h})
    r = agreement(sheet)
    assert r["labelled"] == 4 and r["agreement"] == 0.75 and 0 < r["kappa"] < 1


# ---- the real cases ----

def _offline_case_dirs():
    """Planted/clean/decoy cases, plus real cases whose git export is already cached."""
    import json
    from reviewreplay.cases import REAL_CACHE, find_case_dirs
    for d in find_case_dirs(ROOT / "cases"):
        meta = json.loads((d / "case.json").read_text())
        if meta["kind"] != "real" or (REAL_CACHE / f"{meta['id']}@{meta['commit'][:12]}").exists():
            yield d


def test_all_cases_load_and_resolve():
    cases = [load_case(d) for d in _offline_case_dirs()]
    assert len(cases) >= 10
    for c in cases:
        for s in c.bugs + c.known_ok:
            for _, a, b in s.locations:
                assert 1 <= a <= b


def test_py001_resolves_cross_file_location():
    c = load_case(ROOT / "cases" / "python" / "py-001")
    files = [loc[0] for loc in c.bugs[0].locations]
    assert files == ["shop/checkout.py", "shop/config.py"]
