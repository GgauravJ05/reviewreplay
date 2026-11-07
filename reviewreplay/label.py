"""Blind hand-labelling of graded findings, one at a time, in the terminal.

Reads a run's labels.csv and asks for a `human_label` on every unlabelled row. The judge's label,
its reason and the subject (baseline / skill) are never shown, so the human label is independent.
Rows come in a fixed shuffled order (so one subject's findings aren't all labelled together).
Every answer is saved immediately; quit at any time and run again to continue.
"""
from __future__ import annotations

import csv
import os
import random
import textwrap
from pathlib import Path
from typing import Callable

from .cases import Case

LABELS = {"h": "hit", "v": "valid_other", "f": "false_alarm", "u": "unsure"}
CONTEXT = 3  # code lines shown either side of the finding

RUBRIC = """\
Label each finding using only the answer key and the code shown:
  h  hit          describes an answer-key bug: the same wrong behaviour, for the same cause
                  (different wording is fine; right lines with a different complaint is not)
  v  valid_other  a real defect in the changed code that isn't an answer-key bug, including the
                  listed "other known problems" and remarks that the tests miss an answer-key bug
  f  false_alarm  not a real problem, pure style, about unchanged code with no new effect, or
                  contradicts a "looks suspicious but correct" note
  u  unsure       you can't tell from what's here
Add a note after the letter if useful (e.g. "f just style"). s = skip, q = save and quit.
"""


def _wrap(text: str, indent: str = "    ") -> str:
    return textwrap.fill(text, width=100, initial_indent=indent, subsequent_indent=indent)


def _excerpt(case: Case, file: str, lines: str) -> str:
    path = case.tree / "after" / file
    try:
        start, end = (int(x) for x in lines.split("-"))
        src = path.read_text(encoding="utf-8").splitlines()
    except (ValueError, OSError):
        return "    (no code excerpt: file or lines not in the change)"
    if start < 1 or start > len(src):
        return "    (no code excerpt: no specific line given)"
    lo, hi = max(1, start - CONTEXT), min(len(src), max(start, end) + CONTEXT)
    return "\n".join(f"  {'>' if start <= n <= end else ' '} {n:4d}  {src[n - 1]}"
                     for n in range(lo, hi + 1))


def render(row: dict, case: Case) -> str:
    out = [f"Case {case.id} ({case.kind}): {case.title}", "", "Answer key — bugs:"]
    if case.bugs:
        for b in case.bugs:
            locs = ", ".join(f"{f}:{s}-{e}" for f, s, e in b.locations)
            out.append(f"  {b.id}  {locs}")
            out.append(_wrap(b.info.get("summary", "")))
            if b.info.get("trigger"):
                out.append(_wrap("Trigger: " + b.info["trigger"]))
    else:
        out.append("  (none — this change has no bug)")
    if case.known_ok:
        out.append("Looks suspicious but is correct:")
        for s in case.known_ok:
            out.append(f"  {s.id}  {s.file}:{s.lines[0]}-{s.lines[1]}")
            out.append(_wrap(s.info.get("note", "")))
    if case.related_valid:
        out.append("Other known real problems (fair to report):")
        out += [_wrap("- " + r) for r in case.related_valid]
    out += ["", f"Finding ({row['severity']})  {row['file']}:{row['lines']}",
            _wrap(row["summary"]), "", _excerpt(case, row["file"], row["lines"])]
    return "\n".join(out)


def _save(sheet: Path, fields: list[str], rows: list[dict]) -> None:
    tmp = sheet.with_suffix(".csv.tmp")
    with tmp.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, sheet)


def label_sheet(sheet: Path, cases: dict[str, Case], ask: Callable[[str], str] = input,
                show: Callable[[str], None] = print, seed: int = 0) -> int:
    """Label unlabelled rows interactively. Returns how many were labelled this session."""
    with sheet.open(newline="") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    order = list(range(len(rows)))
    random.Random(seed).shuffle(order)
    todo = [i for i in order if not rows[i]["human_label"].strip()]
    show(RUBRIC)
    done = 0
    for n, i in enumerate(todo, start=1):
        row = rows[i]
        show(f"\n{'─' * 100}\n[{len(rows) - len(todo) + done + 1}/{len(rows)}]"
             f"  ({len(todo) - n + 1} unlabelled)\n")
        show(render(row, cases[row["case"]]))
        while True:
            try:
                answer = ask("\nlabel [h/v/f/u, s skip, q quit]: ").strip()
            except EOFError:
                answer = "q"
            key, _, note = answer.partition(" ")
            key = key.lower()
            if key in LABELS:
                row["human_label"], row["human_note"] = LABELS[key], note.strip()
                _save(sheet, fields, rows)
                done += 1
                break
            if key in ("s", "q"):
                break
            show("  please type h, v, f, u, s or q")
        if key == "q":
            break
    left = sum(1 for r in rows if not r["human_label"].strip())
    show(f"\nSaved. Labelled {done} this session; {left} left of {len(rows)}.")
    return done
