#!/usr/bin/env python3
"""T4 seller risk ranking evaluation (docs/PROTOCOL_v1.0.md §5).

Per attack type (swap, theft, selective downgrade; plus `any`), reports AUROC, AP and precision@10 on the TEST runs
for three baselines - logistic regression, GBDT, and a rule (low quoted price + billed-tokens anomaly; NOT answer
length) - with the full 7-item whitelist and the 6-item no-latency ablation side by side, their difference
(full - no-latency) and a 95% cluster-bootstrap CI of the difference (test RUNS resampled with replacement).

Official point estimates follow protocol §5 / clarification 6: compute AUROC, AP and precision@10 on each test
run separately, then average over the test runs for which the metric is defined (AUROC needs both classes in
that run; AP needs ≥1 positive; precision@10 is defined on any non-empty run). The bootstrap resamples test
runs and re-averages. A pooled-over-sellers figure is written only as `pooled_*` / an appendix note and is
labelled "not protocol".

Input: either raw transaction logs (--logs, exported here with tokenmarket.t4_export) or an existing export dir with
the 7-item features (--export-dir). The no-latency setting drops tokenmarket.t4_export.LATENCY_COLUMNS from the same
rows (identical to an export made with --drop-latency). --drop-latency evaluates only the 6-item setting.

  /workspace/tmvenv/bin/python scripts/run_v1.py --config configs/v1.0/scale.yaml --seeds 0-19 --pi-grid 1.0 \
      --methods fixed_audit_a0.10 --resample-roster --out results/v1.0/t4_runs --log-dir results/v1.0/t4_runs/logs
  /workspace/tmvenv/bin/python scripts/run_t4_eval.py --logs results/v1.0/t4_runs/logs/*.jsonl \
      --config configs/v1.0/scale.yaml --out results/v1.0/t4_eval
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import Dict, List, Optional

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tokenmarket.t4_export import (KEY_COLUMNS, LABEL, LATENCY_COLUMNS, TYPE_LABELS, check_feature_columns,  # noqa
                                   export_t4, read_records)
from tokenmarket.t4_models import GBDT, METRICS, Encoder, LogisticRegression, rule_scores  # noqa: E402

ATTACK_TYPES = ("swap", "theft", "downgrade", "any")
MODELS = ("logreg", "gbdt", "rule")
SETTINGS = {"full7": False, "nolat6": True}


def _read_csv(path: str) -> List[Dict]:
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load_split(export_dir: str, split: str) -> List[Dict]:
    feats = _read_csv(os.path.join(export_dir, f"features_{split}.csv"))
    labs = {(r["run_id"], r["seller_key"]): r for r in _read_csv(os.path.join(export_dir, f"labels_{split}.csv"))}
    out = []
    for f in feats:
        lab = labs.get((f["run_id"], f["seller_key"]), {})
        f = dict(f)
        f["_labels"] = {t: lab.get(LABEL if t == "any" else TYPE_LABELS[t], "") for t in ATTACK_TYPES}
        out.append(f)
    return out


def feature_cols(rows: List[Dict], drop_latency: bool) -> List[str]:
    cols = [c for c in rows[0] if c not in KEY_COLUMNS and not c.startswith("_")]
    errs = check_feature_columns(cols)
    if errs:
        raise SystemExit("feature columns violate the T4 whitelist/blacklist: " + "; ".join(errs))
    return [c for c in cols if not (drop_latency and c in LATENCY_COLUMNS)]


def scores_for(model: str, cols: List[str], train: List[Dict], ytr: np.ndarray, test: List[Dict]) -> np.ndarray:
    if model == "rule":
        return rule_scores(test)
    enc = Encoder(cols).fit(train)
    Xtr, Xte = enc.transform(train), enc.transform(test)
    m = LogisticRegression(l2=1.0) if model == "logreg" else GBDT()
    return m.fit(Xtr, ytr).predict(Xte)


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return None if not xs else float(np.mean(xs))


def per_run_scores(y, s, runs, metric) -> Dict[str, Optional[float]]:
    """One score per test run; undefined runs are omitted from the official average."""
    y, s, runs = map(np.asarray, (y, s, runs))
    f = METRICS[metric]
    out = {}
    for r in list(dict.fromkeys(runs.tolist())):
        idx = np.where(runs == r)[0]
        out[r] = f(y[idx], s[idx])
    return out


def boot_mean_ci(values: List[Optional[float]], n_boot: int, rng) -> Dict:
    defined = [v for v in values if v is not None]
    if not defined:
        return {"lo": None, "hi": None, "n_valid": 0}
    arr = np.asarray(defined, float)
    means = []
    for _ in range(n_boot):
        means.append(float(rng.choice(arr, size=len(arr), replace=True).mean()))
    lo, hi = np.percentile(means, [2.5, 97.5])
    return {"lo": float(lo), "hi": float(hi), "n_valid": len(means)}


def boot_diff(per_full: Dict, per_nolat: Dict, n_boot: int, rng) -> Dict:
    """Bootstrap the official difference: mean_run(full) - mean_run(nolat), resampling runs where both are defined."""
    runs = [r for r in per_full if per_full[r] is not None and per_nolat.get(r) is not None]
    if not runs:
        return {"lo": None, "hi": None, "n_valid": 0}
    diffs = []
    for _ in range(n_boot):
        pick = rng.choice(runs, size=len(runs), replace=True)
        diffs.append(float(np.mean([per_full[r] - per_nolat[r] for r in pick])))
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {"lo": float(lo), "hi": float(hi), "n_valid": len(diffs)}


def evaluate(export_dir: str, n_boot: int = 2000, only_nolat: bool = False, seed: int = 20261110) -> Dict:
    train, test = load_split(export_dir, "train"), load_split(export_dir, "test")
    settings = {"nolat6": True} if only_nolat else SETTINGS
    cols = {k: feature_cols(train, v) for k, v in settings.items()}
    rng = np.random.default_rng(seed)
    results, notes = [], []
    for t in ATTACK_TYPES:
        tr = [r for r in train if r["_labels"][t] != ""]
        te = [r for r in test if r["_labels"][t] != ""]
        ytr = np.array([int(r["_labels"][t]) for r in tr])
        yte = np.array([int(r["_labels"][t]) for r in te])
        n_runs_test = len({r["run_id"] for r in te})
        base = {"attack_type": t, "n_train": len(tr), "n_train_pos": int(ytr.sum()) if len(tr) else 0,
                "n_test": len(te), "n_test_pos": int(yte.sum()) if len(te) else 0,
                "n_test_runs": n_runs_test}
        if not len(tr) or ytr.min() == ytr.max() or not len(te):
            notes.append(f"{t}: skipped (train needs both classes and a non-empty test set): {base}")
            continue
        runs = [r["run_id"] for r in te]
        for model in MODELS:
            sc = {k: scores_for(model, cols[k], tr, ytr, te) for k in settings}
            for metric, f in METRICS.items():
                row = dict(base, model=model, metric=metric, official="mean of per-test-run scores")
                per = {k: per_run_scores(yte, sc[k], runs, metric) for k in settings}
                for k in settings:
                    vals = list(per[k].values())
                    row[k] = _mean(vals)
                    row[f"n_runs_scored_{k}"] = sum(v is not None for v in vals)
                    row[f"per_run_{k}"] = {str(r): v for r, v in per[k].items()}
                    # pooled-over-sellers (NOT protocol; appendix only)
                    row[f"pooled_{k}"] = f(yte, sc[k])
                if not only_nolat:
                    row["diff_full_minus_nolat"] = (None if row["full7"] is None or row["nolat6"] is None
                                                    else row["full7"] - row["nolat6"])
                    row["pooled_diff_full_minus_nolat"] = (
                        None if row["pooled_full7"] is None or row["pooled_nolat6"] is None
                        else row["pooled_full7"] - row["pooled_nolat6"])
                    ci = boot_diff(per["full7"], per["nolat6"], n_boot, rng)
                    mean_ci = boot_mean_ci(list(per["full7"].values()), n_boot, rng)
                    row.update(diff_ci_lo=ci["lo"], diff_ci_hi=ci["hi"], boot_valid=ci["n_valid"],
                               official_ci_lo=mean_ci["lo"], official_ci_hi=mean_ci["hi"])
                results.append(row)
    return {"export_dir": export_dir, "n_boot": n_boot,
            "bootstrap": "official = mean of per-test-run scores; CI resamples test runs, percentile 95%. "
                         "pooled_* averages sellers across test runs and is not protocol.",
            "feature_columns": cols, "latency_columns": list(LATENCY_COLUMNS), "results": results, "notes": notes}


def _f(v, fmt="{:.3f}"):
    return "–" if v is None else fmt.format(v)


def render_md(res: Dict) -> str:
    only = "full7" not in res["feature_columns"]
    L = ["# T4 seller risk ranking (protocol §5)", "",
         f"Export: `{res['export_dir']}`. Bootstrap: {res['bootstrap']}, B = {res['n_boot']}. "
         "Official numbers are the mean of per-test-run scores (runs where the metric is defined). "
         "`n scored` is how many test runs entered that average. "
         "Rule = low quoted price + billed-tokens anomaly within (run, declared model) peers; it uses no latency, so "
         "its full/no-latency difference is 0 by construction.", ""]
    if only:
        L += ["| attack type | model | metric | n test (pos) | n scored / runs | 6 items (no latency) |",
              "|---|---|---|---|---|---|"]
        for r in res["results"]:
            L.append(f"| {r['attack_type']} | {r['model']} | {r['metric']} | {r['n_test']} ({r['n_test_pos']}) "
                     f"| {r.get('n_runs_scored_nolat6', '–')} / {r.get('n_test_runs', '–')} "
                     f"| {_f(r['nolat6'])} |")
    else:
        L += ["| attack type | model | metric | n test (pos) | n scored / runs | 7 items | 6 items (no latency) | Δ (7 − 6) | 95% CI |",
              "|---|---|---|---|---|---|---|---|---|"]
        for r in res["results"]:
            ns = r.get("n_runs_scored_full7", "–")
            L.append(f"| {r['attack_type']} | {r['model']} | {r['metric']} | {r['n_test']} ({r['n_test_pos']}) "
                     f"| {ns} / {r.get('n_test_runs', '–')} "
                     f"| {_f(r['full7'])} | {_f(r['nolat6'])} | {_f(r['diff_full_minus_nolat'], '{:+.3f}')} "
                     f"| [{_f(r['diff_ci_lo'], '{:+.3f}')}, {_f(r['diff_ci_hi'], '{:+.3f}')}] |")
        L += ["", "## Pooled-over-sellers (not protocol, appendix only)", "",
              "These figures rank sellers from all test runs together. They are not the official numbers.",
              "",
              "| attack type | model | metric | pooled 7 items | pooled 6 items | pooled Δ |",
              "|---|---|---|---|---|---|"]
        for r in res["results"]:
            L.append(f"| {r['attack_type']} | {r['model']} | {r['metric']} | {_f(r.get('pooled_full7'))} "
                     f"| {_f(r.get('pooled_nolat6'))} | {_f(r.get('pooled_diff_full_minus_nolat'), '{:+.3f}')} |")
    if res["notes"]:
        L += ["", "Notes:"] + [f"- {n}" for n in res["notes"]]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--logs", nargs="+", default=None, help="raw transaction JSONL (one condition, many seeds)")
    ap.add_argument("--config", default=None, help="config for listed_quality (needed with --logs)")
    ap.add_argument("--export-dir", default=None, help="existing 7-item T4 export (features_/labels_*.csv)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--drop-latency", action="store_true", help="evaluate only the 6-item no-latency setting")
    ap.add_argument("--train-seeds", type=int, nargs="+", default=None)
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    exp_dir = args.export_dir
    if args.logs:
        cfg = None
        if args.config:
            from tokenmarket.config import load_config
            from tokenmarket.roster import materialize
            cfg = materialize(load_config(args.config))
        exp_dir = os.path.join(args.out, "export")
        export_t4(read_records(args.logs), exp_dir, cfg, args.train_seeds)
    if not exp_dir:
        ap.error("give --logs or --export-dir")
    res = evaluate(exp_dir, args.n_boot, args.drop_latency)
    with open(os.path.join(args.out, "t4_eval.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    md = render_md(res)
    with open(os.path.join(args.out, "t4_eval.md"), "w", encoding="utf-8") as fh:
        fh.write(md)
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
