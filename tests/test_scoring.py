"""Tests for the deterministic parts of grading and reporting (no Claude calls)."""
from __future__ import annotations

import csv
from pathlib import Path

from reviewbench.cases import Spot, load_case, load_cases
from reviewbench.grade import candidates, norm_path, overlaps
from reviewbench.report import agreement, bootstrap, review_scores

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


def test_candidates_use_alternate_locations():
    s = spot("shop/checkout.py", 12, 13, also=[("shop/config.py", 6, 6)])
    assert candidates({"file": "shop/config.py", "line_start": 6, "line_end": 6}, [s]) == ["b1"]


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

def test_all_cases_load_and_resolve():
    cases = load_cases(ROOT / "cases")
    assert len(cases) >= 10
    for c in cases:
        for s in c.bugs + c.known_ok:
            for _, a, b in s.locations:
                assert 1 <= a <= b


def test_py001_resolves_cross_file_location():
    c = load_case(ROOT / "cases" / "python" / "py-001")
    files = [loc[0] for loc in c.bugs[0].locations]
    assert files == ["shop/checkout.py", "shop/config.py"]
