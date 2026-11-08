"""Tests for `reviewreplay compare` on synthetic run folders (no Claude calls)."""
from __future__ import annotations

import json
from pathlib import Path

from reviewreplay.compare import build_comparison, format_comparison


class FakeCase:
    def __init__(self, cid, kind="real", has_bug=True):
        self.id, self.kind, self.has_bug = cid, kind, has_bug


def finding(label, severity="important"):
    return {"label": label, "severity": severity, "decoy_spot": []}


def make_run(root: Path, name: str, reviews: dict) -> Path:
    """reviews: {(subject, case, run): (findings, cost)}"""
    d = root / name
    subjects = sorted({s for s, _, _ in reviews})
    d.mkdir(parents=True)
    (d / "config.json").write_text(json.dumps(
        {"subjects": [{"name": s, "prompt": "Review", "skill": None} for s in subjects]}))
    for (subject, case, run), (findings, cost) in reviews.items():
        for part, body in (("grades", {"case": case, "findings": findings}), ("raw", {"cost_usd": cost})):
            f = d / part / subject / case / f"run{run}.json"
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(body))
    return d


def test_compare_pools_runs_and_counts(tmp_path):
    a = make_run(tmp_path, "first", {
        ("baseline", "r1", 1): ([finding("hit"), finding("false_alarm")], 0.10),
        ("skill", "r1", 1): ([finding("hit")], 0.20),
    })
    b = make_run(tmp_path, "second", {
        ("baseline", "r2", 1): ([finding("unsure"), finding("valid_other", "minor")], 0.10),
        ("skill", "r2", 1): ([finding("valid_other"), finding("false_alarm")], 0.20),
        ("baseline", "p1", 1): ([finding("hit")], 0.10),
    })
    cases = {"r1": FakeCase("r1"), "r2": FakeCase("r2"), "p1": FakeCase("p1", kind="planted")}
    c = build_comparison([a, b], cases, kind="real")

    base, skill = c["subjects"]["baseline"], c["subjects"]["skill"]
    assert (base["cases"], base["reviews"], base["found"]) == (2, 2, 1)      # planted p1 left out
    assert (base["precision"]["good"], base["precision"]["serious"]) == (1, 3)
    assert base["false_alarms"] == 1 and base["unsure"] == 1
    assert base["minor_per_review"] == 0.5
    assert (skill["precision"]["good"], skill["precision"]["serious"]) == (2, 3)
    assert abs(skill["mean_cost"] - 0.20) < 1e-9

    paired = c["paired"]["skill"]
    assert paired["recall"]["diff"] == 0 and paired["recall"]["n_cases"] == 2
    assert abs(paired["precision"]["diff"] - (2 / 3 - 1 / 3)) < 1e-9
    assert paired["precision"]["lo"] <= paired["precision"]["diff"] <= paired["precision"]["hi"]


def test_compare_without_kind_keeps_every_case(tmp_path):
    a = make_run(tmp_path, "run", {
        ("baseline", "r1", 1): ([finding("hit")], 0.1),
        ("baseline", "p1", 1): ([], 0.1),
    })
    cases = {"r1": FakeCase("r1"), "p1": FakeCase("p1", kind="planted")}
    c = build_comparison([a], cases)
    assert c["subjects"]["baseline"]["cases"] == 2 and c["paired"] == {}


def test_format_has_one_row_per_subject_and_no_signed_zero(tmp_path):
    a = make_run(tmp_path, "run", {
        ("baseline", "r1", 1): ([finding("hit")], 0.1),
        ("skill", "r1", 1): ([finding("hit")], 0.1),
    })
    text = format_comparison(build_comparison([a], {"r1": FakeCase("r1")}))
    assert "| baseline |" in text and "| skill |" in text
    assert "-0" not in text and "+0 " not in text
