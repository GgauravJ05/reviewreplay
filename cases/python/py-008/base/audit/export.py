"""Copy audit records to the warehouse as JSON lines."""
from __future__ import annotations

import json
from pathlib import Path

from .reader import read_rows


def export_jsonl(src: str | Path, dst: str | Path) -> int:
    n = 0
    with open(dst, "w", encoding="utf-8") as out:
        for r in read_rows(src):
            out.write(json.dumps({"at": r.at.isoformat(), "actor": r.actor,
                                  "action": r.action, "severity": r.severity}) + "\n")
            n += 1
    return n
