"""⑤ Metrics, confidence intervals, the results table, and the hand-label sheet.

Per review (one subject × case × run):
  bug cases     caught      any finding labelled `hit`
                precision   (hit + valid_other) ÷ serious findings (blocking/important); None if none
  clean/decoy   clean_pass  no serious finding labelled false_alarm or unsure
  decoy         trapped     a serious finding lands on a known_ok spot
Each case's score is the mean over its runs; a subject's metric is the mean over cases, with a
95% bootstrap interval resampling cases. Comparisons to the baseline are paired by case.
"""
from __future__ import annotations

import csv
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

from .cases import Case
from .grade import SERIOUS

BOOT = 2000


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def bootstrap(values: list[float], seed: int = 0) -> tuple[float | None, float | None, float | None]:
    vals = [v for v in values if v is not None]
    if not vals:
        return None, None, None
    rng = random.Random(seed)
    means = sorted(_mean([rng.choice(vals) for _ in vals]) for _ in range(BOOT))
    return _mean(vals), means[int(0.025 * BOOT)], means[int(0.975 * BOOT) - 1]


def review_scores(grade: dict, raw: dict, case: Case, subject_skill: str | None) -> dict:
    serious = [f for f in grade["findings"] if f["severity"] in SERIOUS]
    s: dict = {"cost": raw.get("cost_usd"), "seconds": raw.get("seconds"),
               "n_findings": len(grade["findings"]), "n_serious": len(serious)}
    if subject_skill:
        s["skill_used"] = subject_skill in raw.get("skills_invoked", [])
    if case.has_bug:
        s["caught"] = 1.0 if any(f["label"] == "hit" for f in grade["findings"]) else 0.0
        if serious:
            good = sum(1 for f in serious if f["label"] in {"hit", "valid_other"})
            s["precision"] = good / len(serious)
    else:
        bad = [f for f in serious if f["label"] in {"false_alarm", "unsure"}]
        s["clean_pass"] = 0.0 if bad else 1.0
        if case.kind == "decoy":
            s["trapped"] = 1.0 if any(f["decoy_spot"] for f in serious) else 0.0
    return s


def collect(run_dir: Path, cases: dict[str, Case]) -> dict[str, dict[str, list[dict]]]:
    """subject → case → [per-run scores]"""
    cfg = json.loads((run_dir / "config.json").read_text())
    skill_of = {s["name"]: (s["skill"] or {}).get("name") if not s["prompt"].startswith("/") else None
                for s in cfg["subjects"]}
    out: dict = defaultdict(lambda: defaultdict(list))
    for g in sorted((run_dir / "grades").rglob("run*.json")):
        rel = g.relative_to(run_dir / "grades")
        subject, case_id = rel.parts[0], rel.parts[1]
        raw = json.loads((run_dir / "raw" / rel).read_text())
        out[subject][case_id].append(review_scores(json.loads(g.read_text()), raw, cases[case_id],
                                                   skill_of.get(subject)))
    return out


METRICS = [("caught", "Recall"), ("precision", "Precision"), ("clean_pass", "Clean pass"),
           ("trapped", "Decoy trap"), ("skill_used", "Skill used (natural)")]


def per_case(scores: dict[str, list[dict]], key: str) -> dict[str, float]:
    out = {}
    for cid, runs in scores.items():
        vals = [r[key] for r in runs if key in r and r[key] is not None]
        if vals:
            out[cid] = _mean([float(v) for v in vals])
    return out


def build_report(run_dir: Path, cases: dict[str, Case], baseline: str = "baseline") -> dict:
    data = collect(run_dir, cases)
    summary: dict = {"subjects": {}, "paired_vs_baseline": {}}
    for subject, scores in data.items():
        row = {}
        for key, _ in METRICS:
            pc = per_case(scores, key)
            if pc:
                m, lo, hi = bootstrap(list(pc.values()))
                row[key] = {"mean": m, "lo": lo, "hi": hi, "n_cases": len(pc)}
        allruns = [r for runs in scores.values() for r in runs]
        costs = [r["cost"] for r in allruns if r.get("cost") is not None]
        secs = [r["seconds"] for r in allruns if r.get("seconds") is not None]
        row["reviews"] = len(allruns)
        row["median_cost"] = statistics.median(costs) if costs else None
        row["median_seconds"] = statistics.median(secs) if secs else None
        row["mean_findings"] = _mean([r["n_findings"] for r in allruns])
        summary["subjects"][subject] = row
    if baseline in data:
        for subject in data:
            if subject == baseline:
                continue
            comp = {}
            for key in ("caught", "clean_pass", "precision"):
                a, b = per_case(data[subject], key), per_case(data[baseline], key)
                shared = sorted(set(a) & set(b))
                if shared:
                    m, lo, hi = bootstrap([a[c] - b[c] for c in shared], seed=1)
                    comp[key] = {"diff": m, "lo": lo, "hi": hi, "n_cases": len(shared)}
            summary["paired_vs_baseline"][subject] = comp
    summary["per_case"] = {s: {cid: {k: per_case({cid: runs}, k).get(cid) for k, _ in METRICS
                                     if per_case({cid: runs}, k)}
                               for cid, runs in sc.items()} for s, sc in data.items()}
    return summary


def _fmt(cell: dict | None, pct: bool = True) -> str:
    if not cell or cell.get("mean") is None:
        return "—"
    f = (lambda v: f"{100 * v:.0f}%") if pct else (lambda v: f"{v:.2f}")
    return f"{f(cell['mean'])} [{f(cell['lo'])}–{f(cell['hi'])}]"


def write_report(run_dir: Path, cases: dict[str, Case]) -> Path:
    s = build_report(run_dir, cases)
    (run_dir / "summary.json").write_text(json.dumps(s, indent=2))
    cfg = json.loads((run_dir / "config.json").read_text())
    lines = [f"# ReviewBench results — `{run_dir.name}`", "",
             f"Model `{cfg['model']}` · {cfg['cli_version']} · {cfg['runs']} runs per case · "
             f"{len(cfg['cases'])} cases", "",
             "Values are mean over cases (each case averaged over its runs) with a 95% bootstrap "
             "interval over cases.", "",
             "| Subject | Reviews | " + " | ".join(n for _, n in METRICS) +
             " | Findings / review | Median est. cost | Median time |",
             "|---|---|" + "---|" * len(METRICS) + "---|---|---|"]
    for name, row in sorted(s["subjects"].items()):
        cells = [_fmt(row.get(k)) for k, _ in METRICS]
        cost = f"${row['median_cost']:.3f}" if row["median_cost"] is not None else "—"
        secs = f"{row['median_seconds']:.0f}s" if row["median_seconds"] is not None else "—"
        mf = f"{row['mean_findings']:.1f}" if row["mean_findings"] is not None else "—"
        lines.append(f"| {name} | {row['reviews']} | " + " | ".join(cells) + f" | {mf} | {cost} | {secs} |")
    if s["paired_vs_baseline"]:
        lines += ["", "## Paired difference vs. baseline", "",
                  "Positive = better than baseline for recall, clean pass and precision. "
                  "An interval that includes 0 means no clear difference.", "",
                  "| Subject | Recall Δ | Clean pass Δ | Precision Δ |", "|---|---|---|---|"]
        for name, comp in sorted(s["paired_vs_baseline"].items()):
            def d(k):
                c = comp.get(k)
                if not c:
                    return "—"
                return f"{100 * c['diff']:+.0f} pts [{100 * c['lo']:+.0f}, {100 * c['hi']:+.0f}]"
            lines.append(f"| {name} | {d('caught')} | {d('clean_pass')} | {d('precision')} |")
    lines += ["", "## Per case", "", "| Subject | Case | Kind | Recall | Clean pass | Decoy trap | Skill used |",
              "|---|---|---|---|---|---|---|"]
    for name, per in sorted(s["per_case"].items()):
        for cid, m in sorted(per.items()):
            def p(k):
                return f"{100 * m[k]:.0f}%" if m.get(k) is not None else "—"
            lines.append(f"| {name} | {cid} | {cases[cid].kind} | {p('caught')} | {p('clean_pass')} | "
                         f"{p('trapped')} | {p('skill_used')} |")
    lines += ["", "## Subjects", ""]
    for sub in cfg["subjects"]:
        sk = sub["skill"]
        src = f" — {sk['repo']} @ `{sk['commit']}`" if sk else ""
        lines.append(f"- **{sub['name']}**{src}. Prompt: `{sub['prompt']}`"
                     + (f". Credit: {sub['credit']}" if sub.get("credit") else ""))
    out = run_dir / "summary.md"
    out.write_text("\n".join(lines) + "\n")
    return out


# ---------- hand labels ----------

LABEL_FIELDS = ["subject", "case", "kind", "run", "index", "severity", "file", "lines", "summary",
                "candidates", "decoy_spot", "auto_label", "judge_reason", "human_label", "human_note"]


def write_label_sheet(run_dir: Path) -> Path:
    out = run_dir / "labels.csv"
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=LABEL_FIELDS)
        w.writeheader()
        for g in sorted((run_dir / "grades").rglob("run*.json")):
            rel = g.relative_to(run_dir / "grades")
            data = json.loads(g.read_text())
            for f in data["findings"]:
                w.writerow({"subject": rel.parts[0], "case": rel.parts[1], "kind": data["kind"],
                            "run": rel.stem, "index": f["index"], "severity": f["severity"],
                            "file": f["file"], "lines": f"{f['line_start']}-{f['line_end']}",
                            "summary": f["summary"], "candidates": ",".join(f["candidates"]),
                            "decoy_spot": ",".join(f["decoy_spot"]), "auto_label": f["label"],
                            "judge_reason": f["judge"].get("reason", ""), "human_label": "",
                            "human_note": ""})
    return out


def agreement(sheet: Path) -> dict:
    rows = [r for r in csv.DictReader(sheet.open()) if r["human_label"].strip()]
    if not rows:
        return {"labelled": 0}
    pairs = [(r["auto_label"], r["human_label"].strip()) for r in rows]
    n = len(pairs)
    po = sum(a == h for a, h in pairs) / n
    labels = {x for p in pairs for x in p}
    pe = sum((sum(a == l for a, _ in pairs) / n) * (sum(h == l for _, h in pairs) / n) for l in labels)
    kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
    confusion: dict = defaultdict(int)
    for a, h in pairs:
        confusion[f"{a} → {h}"] += 1
    return {"labelled": n, "agreement": po, "kappa": kappa, "confusion": dict(confusion)}
