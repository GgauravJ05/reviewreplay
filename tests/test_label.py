"""Hand-labelling: blind display, saving, resuming."""
import csv
import shutil
from pathlib import Path

from reviewreplay.cases import load_cases
from reviewreplay.label import label_sheet

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / "results" / "m1-pilot" / "labels.csv"
CASES = {c.id: c for c in load_cases(ROOT / "cases")}


def _copy(tmp_path):
    out = tmp_path / "labels.csv"
    shutil.copy(SHEET, out)
    with out.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["human_label"] = r["human_note"] = ""
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return out, rows


def _rows(path):
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def test_label_saves_resumes_and_hides_judge(tmp_path):
    sheet, rows = _copy(tmp_path)
    shown = []
    answers = iter(["x", "h", "f too picky", "s", "q"])
    assert label_sheet(sheet, CASES, ask=lambda _: next(answers), show=shown.append) == 2
    after = _rows(sheet)
    got = [r for r in after if r["human_label"]]
    assert sorted(r["human_label"] for r in got) == ["false_alarm", "hit"]
    assert any(r["human_note"] == "too picky" for r in got)
    text = "\n".join(shown)
    for r in rows:  # judge reasons never shown
        assert r["judge_reason"] not in text
    assert "auto_label" not in text and "baseline" not in text

    # resume: already-labelled rows are not asked again; EOF quits cleanly
    def eof(_):
        raise EOFError
    assert label_sheet(sheet, CASES, ask=eof, show=lambda _: None) == 0
    assert len([r for r in _rows(sheet) if r["human_label"]]) == 2
