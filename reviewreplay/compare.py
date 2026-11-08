"""Combine several run folders into one comparison table.

`report` describes one run. `compare` pools runs that share subjects (for example a first batch of
real bugs and a later one), optionally keeps one case kind, and reports per subject:

  bug found     reviews that hit the known bug, as a count
  recall        mean over cases of each case's hit rate, 95% bootstrap interval over cases
  precision     pooled: (hit + valid_other) ÷ serious findings, over all reviews; its interval
                resamples cases and recomputes the pooled ratio
  false alarms  serious findings labelled false_alarm; `unsure` counted separately
  minor         non-serious findings per review
  cost          mean and median per review

Paired differences against the baseline resample the cases both subjects share.
"""
from __future__ import annotations

import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

from .cases import Case
from .grade import tally
from .report import BOOT, bootstrap, cohen_kappa, collect, per_case


def merge_runs(run_dirs: list[Path], cases: dict[str, Case], kind: str | None = None,
               drop_contested: bool = False) -> dict[str, dict[str, list[dict]]]:
    """subject → case → [per-run scores], pooled across run folders."""
    out: dict = defaultdict(lambda: defaultdict(list))
    for d in run_dirs:
        for subject, per in collect(d, cases, drop_contested).items():
            for cid, runs in per.items():
                if kind and cases[cid].kind != kind:
                    continue
                out[subject][cid].extend(runs)
    return out


def _pooled(scores: dict[str, list[dict]], cids) -> float | None:
    serious = sum(r.get("n_serious", 0) for c in cids for r in scores[c])
    good = sum(r.get("n_good", 0) for c in cids for r in scores[c])
    return good / serious if serious else None


def pooled_interval(scores: dict[str, list[dict]], seed: int = 0):
    cids = sorted(scores)
    rng = random.Random(seed)
    vals = []
    for _ in range(BOOT):
        v = _pooled(scores, [rng.choice(cids) for _ in cids])
        if v is not None:
            vals.append(v)
    vals.sort()
    if not vals:
        return None, None, None
    return _pooled(scores, cids), vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]


def paired_pooled(a: dict[str, list[dict]], b: dict[str, list[dict]], seed: int = 1):
    """Pooled precision of a minus b, bootstrapped over the cases both have."""
    shared = sorted(set(a) & set(b))
    if not shared:
        return None
    rng = random.Random(seed)

    def diff(cids):
        x, y = _pooled(a, cids), _pooled(b, cids)
        return None if x is None or y is None else x - y

    vals = sorted(v for v in (diff([rng.choice(shared) for _ in shared]) for _ in range(BOOT))
                  if v is not None)
    point = diff(shared)
    if point is None or not vals:
        return None
    return {"diff": point, "lo": vals[int(0.025 * len(vals))], "hi": vals[int(0.975 * len(vals)) - 1],
            "n_cases": len(shared)}


def subject_row(scores: dict[str, list[dict]]) -> dict:
    runs = [r for rs in scores.values() for r in rs]
    bug_runs = [r for r in runs if "caught" in r]
    costs = [r["cost"] for r in runs if r.get("cost") is not None]
    rec = per_case(scores, "caught")
    m, lo, hi = bootstrap(list(rec.values())) if rec else (None, None, None)
    pm, plo, phi = pooled_interval(scores)
    return {
        "cases": len(scores), "reviews": len(runs),
        "found": int(sum(r["caught"] for r in bug_runs)), "bug_reviews": len(bug_runs),
        "recall": {"mean": m, "lo": lo, "hi": hi},
        "precision": {"mean": pm, "lo": plo, "hi": phi,
                      "good": sum(r.get("n_good", 0) for r in runs),
                      "serious": sum(r.get("n_serious", 0) for r in runs)},
        "false_alarms": sum(r.get("n_false_alarm", 0) for r in runs),
        "unsure": sum(r.get("n_unsure", 0) for r in runs),
        "contested": sum(r.get("n_contested", 0) for r in runs),
        "minor_per_review": statistics.mean(r.get("n_minor", 0) for r in runs) if runs else None,
        "mean_cost": statistics.mean(costs) if costs else None,
        "median_cost": statistics.median(costs) if costs else None,
    }


def judge_agreement(run_dirs: list[Path], cases: dict[str, Case], kind: str | None = None) -> dict | None:
    """How much the judge votes agree, over findings graded more than once."""
    findings = []
    for d in run_dirs:
        for g in sorted((d / "grades").rglob("run*.json")):
            data = json.loads(g.read_text())
            if kind and cases[data["case"]].kind != kind:
                continue
            findings += [f for f in data["findings"] if len(f.get("votes", [])) > 1]
    if not findings:
        return None
    out = {"findings": len(findings), "votes_per_finding": statistics.mean(len(f["votes"]) for f in findings),
           "unanimous": sum(len({v["label"] for v in f["votes"]}) == 1 for f in findings),
           "contested": sum(bool(f.get("contested")) for f in findings)}
    models = []
    for f in findings:
        for v in f["votes"]:
            if v["model"] not in models:
                models.append(v["model"])
    if len(models) > 1:
        pairs = []
        for f in findings:
            a = [v["label"] for v in f["votes"] if v["model"] == models[0]]
            b = [v["label"] for v in f["votes"] if v["model"] == models[1]]
            if a and b:
                pairs.append((tally(a)[0], tally(b)[0]))
        if pairs:
            po, k = cohen_kappa(pairs)
            out["between_models"] = {"models": models[:2], "findings": len(pairs), "agreement": po, "kappa": k}
    return out


def build_comparison(run_dirs: list[Path], cases: dict[str, Case], kind: str | None = None,
                     baseline: str = "baseline", drop_contested: bool = False) -> dict:
    data = merge_runs(run_dirs, cases, kind, drop_contested)
    out: dict = {"runs": [d.name for d in run_dirs], "kind": kind, "drop_contested": drop_contested,
                 "subjects": {}, "paired": {}, "judges": judge_agreement(run_dirs, cases, kind)}
    for subject, scores in sorted(data.items()):
        out["subjects"][subject] = subject_row(scores)
    if baseline in data:
        for subject, scores in data.items():
            if subject == baseline:
                continue
            a, b = per_case(scores, "caught"), per_case(data[baseline], "caught")
            shared = sorted(set(a) & set(b))
            comp = {}
            if shared:
                dm, dlo, dhi = bootstrap([a[c] - b[c] for c in shared], seed=1)
                comp["recall"] = {"diff": dm, "lo": dlo, "hi": dhi, "n_cases": len(shared)}
            pp = paired_pooled(scores, data[baseline])
            if pp:
                comp["precision"] = pp
            out["paired"][subject] = comp
    return out


def _pct(v):
    return "—" if v is None else f"{100 * v:.0f}%"


def format_comparison(c: dict) -> str:
    kind = f" · {c['kind']} cases only" if c["kind"] else ""
    kind += " · contested findings left out" if c.get("drop_contested") else ""
    lines = [f"# ReviewReplay comparison — {', '.join(c['runs'])}{kind}", "",
             "| Subject | Cases | Reviews | Bug found | Recall | Precision (serious) | "
             "Serious false alarms | Unsure | Contested | Minor / review | Mean cost | Median cost |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, r in c["subjects"].items():
        rec, pr = r["recall"], r["precision"]
        rec_s = "—" if rec["mean"] is None else f"{_pct(rec['mean'])} [{_pct(rec['lo'])}–{_pct(rec['hi'])}]"
        pr_s = ("—" if pr["mean"] is None else
                f"{_pct(pr['mean'])} ({pr['good']}/{pr['serious']}) [{_pct(pr['lo'])}–{_pct(pr['hi'])}]")
        found = f"{r['found']} / {r['bug_reviews']}" if r["bug_reviews"] else "—"
        minor = "—" if r["minor_per_review"] is None else f"{r['minor_per_review']:.1f}"
        mean_c = "—" if r["mean_cost"] is None else f"${r['mean_cost']:.3f}"
        med_c = "—" if r["median_cost"] is None else f"${r['median_cost']:.3f}"
        lines.append(f"| {name} | {r['cases']} | {r['reviews']} | {found} | {rec_s} | {pr_s} | "
                     f"{r['false_alarms']} | {r['unsure']} | {r.get('contested', 0)} | {minor} | "
                     f"{mean_c} | {med_c} |")
    if c["paired"]:
        lines += ["", "## Paired difference vs. baseline", "",
                  "Bootstrapped over the cases both subjects share. An interval that includes 0 "
                  "means no clear difference.", "",
                  "| Subject | Recall Δ | Precision Δ (pooled) | Shared cases |", "|---|---|---|---|"]

        def pts(v):
            r = round(100 * v)
            return f"{r:+d}" if r else "0"

        def d(x):
            return "—" if not x else f"{pts(x['diff'])} pts [{pts(x['lo'])}, {pts(x['hi'])}]"
        for name, comp in sorted(c["paired"].items()):
            n = max((v["n_cases"] for v in comp.values()), default=0)
            lines.append(f"| {name} | {d(comp.get('recall'))} | {d(comp.get('precision'))} | {n} |")
    j = c.get("judges")
    if j:
        lines += ["", "## Judge agreement", "",
                  f"{j['findings']} findings graded {j['votes_per_finding']:.1f} times on average: "
                  f"{j['unanimous']} unanimous, {j['contested']} contested (no label with a strict majority)."]
        bm = j.get("between_models")
        if bm:
            lines.append(f"Between `{bm['models'][0]}` and `{bm['models'][1]}` on {bm['findings']} findings: "
                         f"{100 * bm['agreement']:.0f}% agreement, Cohen's kappa {bm['kappa']:.2f}.")
    return "\n".join(lines) + "\n"


def write_comparison(run_dirs: list[Path], cases: dict[str, Case], out: Path | None,
                     kind: str | None = None, baseline: str = "baseline",
                     drop_contested: bool = False) -> str:
    c = build_comparison(run_dirs, cases, kind, baseline, drop_contested)
    text = format_comparison(c)
    if out:
        out.write_text(text)
        out.with_suffix(".json").write_text(json.dumps(c, indent=2))
    return text
