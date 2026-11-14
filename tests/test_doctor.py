"""doctor checks and --dry-run estimates (no Claude calls, no network)."""
from __future__ import annotations

import subprocess
from types import SimpleNamespace

from reviewreplay import cli, doctor


def test_missing_git_and_claude_print_a_fix(monkeypatch, tmp_path):
    monkeypatch.setattr(doctor.shutil, "which", lambda name: None)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    found = {name: (ok, msg) for name, ok, msg in doctor.checks()}
    assert found["git"] == (False, "git not found: install git (https://git-scm.com/downloads)")
    assert not found["claude"][0] and "install Claude Code" in found["claude"][1]
    assert found["cache"][0] and found["python"][0]


def test_login_check_is_off_by_default_and_skipped_without_claude(monkeypatch, tmp_path):
    monkeypatch.setattr(doctor.shutil, "which", lambda name: None)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert [n for n, *_ in doctor.checks()] == ["python", "git", "claude", "cache"]
    login = doctor.checks(login=True)[-1]
    assert login == ("login", False, "skipped: claude not found")


def test_login_failure_names_the_fix(monkeypatch):
    def fake_run(*a, **k):
        return subprocess.CompletedProcess(a[0], 1, stdout="", stderr="Failed to authenticate. API Error: 401")
    monkeypatch.setattr(doctor.subprocess, "run", fake_run)
    ok, msg = doctor._check_login()
    assert not ok and "log in" in msg


def test_unwritable_cache_is_reported(monkeypatch, tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")                       # a file where the cache folder should go
    monkeypatch.setenv("XDG_CACHE_HOME", str(blocker))
    ok, msg = doctor._check_cache()
    assert not ok and "not writable" in msg


def test_estimate_scales_with_reviews_and_workers():
    e = doctor.estimate(12, workers=3)
    assert e["cost"] == tuple(12 * c for c in doctor.COST_PER_REVIEW)
    assert e["minutes"][0] == 4 * doctor.SECONDS_PER_REVIEW[1] / 60      # 4 waves of 3


def test_dry_run_counts_only_reviews_still_to_run(tmp_path):
    done = tmp_path / "raw" / "baseline" / "c1" / "run1.json"
    done.parent.mkdir(parents=True)
    done.write_text("{}")
    assert doctor.pending_reviews(["c1", "c2"], ["baseline", "skill"], 2, tmp_path) == (8, 1)
    text = doctor.describe_run(["c1", "c2"], ["baseline", "skill"], 2, tmp_path, workers=3)
    assert "= 8 review(s)" in text and "7 left to run" in text and "Nothing was run" in text


def test_run_dry_run_spends_nothing(monkeypatch, tmp_path, capsys):
    cases = [SimpleNamespace(id="c1", meta={}), SimpleNamespace(id="c2", meta={})]
    monkeypatch.setattr(cli, "_cases", lambda path: cases)
    monkeypatch.setattr(cli, "load_subjects", lambda d, names: [SimpleNamespace(name="baseline")])
    monkeypatch.setattr(cli, "run_all", lambda *a, **k: (_ for _ in ()).throw(AssertionError("ran")))
    monkeypatch.setattr(doctor, "preflight", lambda: (_ for _ in ()).throw(AssertionError("checked")))
    assert cli.main(["run", "--out", str(tmp_path / "r"), "--runs", "3", "--dry-run"]) == 0
    assert "2 case(s) x 1 reviewer(s) x 3 run(s) = 6 review(s)" in capsys.readouterr().out


def test_run_stops_before_spending_when_preflight_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "_cases", lambda path: [SimpleNamespace(id="c1", meta={})])
    monkeypatch.setattr(cli, "load_subjects", lambda d, names: [SimpleNamespace(name="baseline")])
    monkeypatch.setattr(cli, "run_all", lambda *a, **k: (_ for _ in ()).throw(AssertionError("ran")))
    monkeypatch.setattr(doctor, "preflight", lambda: False)
    assert cli.main(["run", "--out", str(tmp_path / "r")]) == 1


def test_init_dry_run_with_no_candidates_suggests_wider_search(monkeypatch, capsys):
    monkeypatch.setattr(cli, "usable_candidates", lambda *a, **k: [])
    assert cli.main(["init", ".", "--dry-run", "--since", "2025-01-01"]) == 1
    out = capsys.readouterr().out
    assert "no usable fix commits since 2025-01-01" in out and "--pattern" in out
