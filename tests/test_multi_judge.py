"""Multi-judge grading: votes, contested findings, reuse of single-judge grades (no Claude calls)."""
from __future__ import annotations

import json
from pathlib import Path

from reviewreplay.cases import Case, Spot
from reviewreplay.compare import build_comparison
from reviewreplay.grade import grade_one, label_for, tally, wanted_judges

BUG = Spot(id="b1", file="src/a.py", lines=(10, 12), info={"summary": "off by one"}, also=[])


def case() -> Case:
    return Case(id="real-x", kind="real", track="python", title="t", path=Path("."), meta={},
                tree=Path("."), bugs=[BUG])


def write_findings(tmp: Path) -> Path:
    f = tmp / "findings" / "baseline" / "real-x" / "run1.json"
    f.parent.mkdir(parents=True)
    f.write_text(json.dumps({"findings": [
        {"file": "src/a.py", "line_start": 11, "line_end": 11, "severity": "important", "summary": "bug"},
        {"file": "src/b.py", "line_start": 5, "line_end": 5, "severity": "important", "summary": "other"},
    ]}))
    return f


def judge(verdicts: dict[int, tuple[str | None, str]]):
    """A fake judge call: index → (same_bug_as, verdict)."""
    calls = []

    def call(prompt, model):
        calls.append(model)
        return {"model": model, "cost_usd": 0.01,
                "grades": {str(i): {"index": i, "same_bug_as": b, "verdict": v, "reason": "r"}
                           for i, (b, v) in verdicts.items()}}
    return call, calls


# ---- voting rules ----

def test_label_for_needs_bug_among_candidates():
    row = {"candidates": ["b1"]}
    assert label_for(row, {"same_bug_as": "b1", "verdict": "matches_truth"}) == "hit"
    assert label_for({"candidates": []}, {"same_bug_as": "b1", "verdict": "matches_truth"}) == "false_alarm"
    assert label_for(row, {"same_bug_as": None, "verdict": "valid_other"}) == "valid_other"
    assert label_for(row, {"same_bug_as": None, "verdict": "unsure"}) == "unsure"
    assert label_for(row, {"same_bug_as": None, "verdict": "invalid"}) == "false_alarm"


def test_tally_majority_and_contested():
    assert tally(["hit"]) == ("hit", False, 1.0)
    assert tally(["valid_other", "false_alarm", "valid_other"])[:2] == ("valid_other", False)
    label, contested, share = tally(["valid_other", "false_alarm"])
    assert (label, contested, share) == ("valid_other", True, 0.5)      # tie: first vote wins, contested
    assert tally(["a", "b", "c"])[1] is True


def test_wanted_judges():
    assert wanted_judges("s") == ["s"]
    assert wanted_judges("s", 3, "o") == ["s", "s", "s", "o"]
    assert wanted_judges("s", 0, "o", 2) == ["s", "o", "o"]


# ---- grade_one ----

def test_three_votes_record_majority(tmp_path):
    f = write_findings(tmp_path)
    out = tmp_path / "grades" / "run1.json"
    answers = iter([{0: ("b1", "matches_truth"), 1: (None, "valid_other")},
                    {0: ("b1", "matches_truth"), 1: (None, "invalid")},
                    {0: ("b1", "matches_truth"), 1: (None, "valid_other")}])

    def call(prompt, model):
        v = next(answers)
        return {"model": model, "cost_usd": 0.01,
                "grades": {str(i): {"index": i, "same_bug_as": b, "verdict": x, "reason": "r"}
                           for i, (b, x) in v.items()}}
    grade_one(case(), f, out, "s", judges=["s", "s", "s"], call=call)
    g = json.loads(out.read_text())
    a, b = g["findings"]
    assert a["label"] == "hit" and a["hit_bug"] == "b1" and not a["contested"]
    assert b["label"] == "valid_other" and not b["contested"] and abs(b["agreement"] - 2 / 3) < 1e-9
    assert len(g["judge_runs"]) == 3 and abs(g["judge_cost_usd"] - 0.03) < 1e-9


def test_existing_single_judge_grade_counts_as_first_vote(tmp_path):
    f = write_findings(tmp_path)
    out = tmp_path / "grades" / "run1.json"
    one, calls = judge({0: ("b1", "matches_truth"), 1: (None, "valid_other")})
    grade_one(case(), f, out, "s", call=one)
    old = json.loads(out.read_text())
    old.pop("judge_runs")                                   # a grade file from before multi-judge
    out.write_text(json.dumps(old))

    disagree, calls2 = judge({0: ("b1", "matches_truth"), 1: (None, "invalid")})
    status = grade_one(case(), f, out, "s", judges=["s", "o"], call=disagree)
    assert calls2 == ["o"] and status == "ok (1 new vote)"   # only the missing judge ran
    g = json.loads(out.read_text())
    assert [r["model"] for r in g["judge_runs"]] == ["s", "o"]
    assert g["findings"][1]["contested"] is True and g["findings"][1]["label"] == "valid_other"
    assert grade_one(case(), f, out, "s", judges=["s", "o"], call=disagree) == "cached"


# ---- reporting ----

def make_run(tmp: Path, findings: list[dict]) -> Path:
    d = tmp / "run"
    for part, body in (("grades", {"case": "real-x", "kind": "real", "findings": findings}),
                       ("raw", {"cost_usd": 0.1})):
        p = d / part / "baseline" / "real-x" / "run1.json"
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps(body))
    (d / "config.json").write_text(json.dumps({"subjects": [{"name": "baseline", "prompt": "R", "skill": None}]}))
    return d


def vote(model, label):
    return {"model": model, "label": label}


def test_drop_contested_and_judge_agreement(tmp_path):
    d = make_run(tmp_path, [
        {"label": "hit", "severity": "important", "decoy_spot": [], "contested": False,
         "votes": [vote("s", "hit"), vote("s", "hit"), vote("o", "hit")]},
        {"label": "valid_other", "severity": "important", "decoy_spot": [], "contested": True,
         "votes": [vote("s", "valid_other"), vote("o", "false_alarm")]},
    ])
    cases = {"real-x": case()}
    keep = build_comparison([d], cases)
    drop = build_comparison([d], cases, drop_contested=True)
    assert keep["subjects"]["baseline"]["precision"]["serious"] == 2
    assert drop["subjects"]["baseline"]["precision"]["serious"] == 1
    assert keep["subjects"]["baseline"]["contested"] == 1
    j = keep["judges"]
    assert (j["findings"], j["unanimous"], j["contested"]) == (2, 1, 1)
    assert j["between_models"]["models"] == ["s", "o"] and j["between_models"]["agreement"] == 0.5
