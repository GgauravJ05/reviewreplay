"""`verify`: quote checks, safe source extraction, release choice, incremental runs and relabelling
(no Claude or network calls)."""
from __future__ import annotations

import io
import json
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from reviewreplay.cases import Case
from reviewreplay.compare import build_comparison
from reviewreplay.verify import (apply_checks, extract_sources, pick_release, quote_found, settle,
                                 targets, verify_one)


def ws_with(tmp: Path) -> Path:
    ws = tmp / "ws"
    (ws / "project").mkdir(parents=True)
    (ws / "project" / "a.py").write_text("def f(x):\n    if x is None:\n        return 0\n    return x + 1\n")
    (tmp / "secret.py").write_text("password = 'nope-not-here'\n")
    return ws


def test_quote_found_is_whitespace_insensitive_and_stays_in_workspace(tmp_path):
    ws = ws_with(tmp_path)
    assert quote_found(ws, {"file": "project/a.py", "quote": "if x is None:   return 0"})
    assert not quote_found(ws, {"file": "project/a.py", "quote": "if x is not None:"})
    assert not quote_found(ws, {"file": "project/a.py", "quote": "x + 1"})          # too short
    assert not quote_found(ws, {"file": "../secret.py", "quote": "password = 'nope-not-here'"})
    assert not quote_found(ws, {"file": "project/missing.py", "quote": "anything at all"})


def test_settle_downgrades_a_verdict_without_evidence(tmp_path):
    ws = ws_with(tmp_path)
    good = settle({"verdict": "refuted", "reason": "r",
                   "evidence": [{"file": "project/a.py", "line": 2, "quote": "if x is None:"}]}, ws)
    assert good["verdict"] == "refuted" and good["evidence_ok"] == 1 and "note" not in good
    bad = settle({"verdict": "confirmed", "reason": "r",
                  "evidence": [{"file": "project/a.py", "line": 2, "quote": "made up code here"}]}, ws)
    assert bad["verdict"] == "unsure" and bad["evidence_ok"] == 0 and "downgraded" in bad["note"]


def test_extract_sources_keeps_only_safe_python_files(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("pkg/core.py", "x = 1\n")
        z.writestr("pkg/core.pyi", "x: int\n")
        z.writestr("pkg/_speedups.so", "binary")
        z.writestr("../evil.py", "boom")
        z.writestr("pkg/setup.sh", "rm -rf /")
    assert extract_sources(buf.getvalue(), "pkg-1.0-py3-none-any.whl", tmp_path / "w") == 2
    assert sorted(p.name for p in (tmp_path / "w").rglob("*") if p.is_file()) == ["core.py", "core.pyi"]
    assert not (tmp_path / "evil.py").exists()

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        for name, data in (("pkg-1.0/pkg/mod.py", b"y = 2\n"), ("pkg-1.0/../../evil.py", b"boom")):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            t.addfile(info, io.BytesIO(data))
    assert extract_sources(buf.getvalue(), "pkg-1.0.tar.gz", tmp_path / "t") == 1


def file(name, when, kind="bdist_wheel", yanked=False):
    return {"filename": name, "upload_time_iso_8601": when, "packagetype": kind, "yanked": yanked,
            "url": f"https://files/{name}", "size": 10}


def test_pick_release_takes_newest_before_the_change():
    releases = {
        "1.0": [file("p-1.0-py3-none-any.whl", "2024-01-01T00:00:00Z")],
        "1.1": [file("p-1.1-cp312-macosx.whl", "2024-06-01T00:00:00Z"),
                file("p-1.1.tar.gz", "2024-06-01T00:00:00Z", "sdist")],
        "1.2": [file("p-1.2-py3-none-any.whl", "2024-08-01T00:00:00Z", yanked=True)],
        "2.0": [file("p-2.0-py3-none-any.whl", "2025-01-01T00:00:00Z")],
    }
    version, f = pick_release(releases, datetime(2024, 9, 1, tzinfo=timezone.utc))
    assert version == "1.1" and f["filename"] == "p-1.1.tar.gz"           # no pure wheel: the sdist
    assert pick_release(releases, datetime(2023, 1, 1, tzinfo=timezone.utc)) is None


def case() -> Case:
    return Case(id="real-x", kind="real", track="python", title="t", path=Path("."), meta={},
                tree=Path("."), bugs=[])


def finding(i, label, severity="important"):
    return {"index": i, "label": label, "severity": severity, "decoy_spot": [], "contested": False,
            "file": "a.py", "line_start": 1, "line_end": 1, "summary": f"claim {i}"}


def test_verify_one_checks_serious_unsure_findings_once(tmp_path):
    grade = tmp_path / "grades" / "baseline" / "real-x" / "run1.json"
    grade.parent.mkdir(parents=True)
    grade.write_text(json.dumps({"case": "real-x", "findings": [
        finding(0, "hit"), finding(1, "unsure"), finding(2, "unsure", "minor"), finding(3, "unsure")]}))
    out = tmp_path / "verify" / "baseline" / "real-x" / "run1.json"
    seen = []

    def check(c, f, model, limit_mb):
        seen.append(f["index"])
        return {"verdict": "confirmed" if f["index"] == 1 else "refuted", "reason": "r",
                "evidence": [], "evidence_ok": 1, "library": None, "cost_usd": 0.02}

    assert verify_one(case(), grade, out, "s", check=check) == "confirmed, refuted"
    assert seen == [1, 3]
    assert verify_one(case(), grade, out, "s", check=check) == "cached" and seen == [1, 3]
    assert len(targets(json.loads(grade.read_text()), all_severities=True)) == 3
    assert set(json.loads(out.read_text())["findings"]) == {"1", "3"}


def test_apply_checks_relabels_only_unsure():
    grade = {"findings": [finding(0, "hit"), finding(1, "unsure"), finding(2, "unsure")]}
    checks = {"0": {"verdict": "refuted"}, "1": {"verdict": "confirmed"}, "2": {"verdict": "unsure"}}
    rows = apply_checks(grade, checks)["findings"]
    assert [r["label"] for r in rows] == ["hit", "valid_other", "unsure"]
    assert rows[1]["label_before_check"] == "unsure" and rows[1]["check"]["verdict"] == "confirmed"
    assert apply_checks(grade, None) is grade


def test_compare_applies_checks_unless_ignored(tmp_path):
    d = tmp_path / "run"
    for part, body in (("grades", {"case": "real-x", "kind": "real",
                                   "findings": [finding(0, "hit"), finding(1, "unsure")]}),
                       ("raw", {"cost_usd": 0.1}),
                       ("verify", {"case": "real-x", "model": "s",
                                   "findings": {"1": {"verdict": "confirmed", "cost_usd": 0.02}}})):
        p = d / part / "baseline" / "real-x" / "run1.json"
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps(body))
    (d / "config.json").write_text(json.dumps({"subjects": [{"name": "baseline", "prompt": "R", "skill": None}]}))
    cases = {"real-x": case()}
    on = build_comparison([d], cases)
    off = build_comparison([d], cases, use_checks=False)
    assert on["subjects"]["baseline"]["precision"]["good"] == 1 + 1
    assert off["subjects"]["baseline"]["precision"]["good"] == 1
    assert on["subjects"]["baseline"]["unsure"] == 0 and off["subjects"]["baseline"]["unsure"] == 1
    assert on["checks"]["checked"] == 1 and on["checks"]["confirmed"] == 1 and off["checks"] is None
