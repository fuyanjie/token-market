#!/usr/bin/env python3
"""Official frozen T5 runner and evaluator (docs/PROTOCOL_T5.md, frozen 2026-11-22).

Pipeline:
  1. Verify frozen docs/PROTOCOL_T5.md and configs/v1.0/scale.yaml sha256.
  2. Collect training logs at pi=1.0, seeds 0..13, resampled roster, frozen eps=0.20 random/strongest behavior policy.
  3. Export label-stripped training features + labels (excluding 15 hold-out prompt hashes) and run T5 leakage check.
     STOP immediately (no scoring) if leakage check fails (§8).
  4. Select tau separately for Two-stage LR and Two-stage GBDT via online simulation on inner-val seeds 10..13
     (models fitted on non-holdout rows of seeds 0..9; scored strictly on non-holdout tasks vs strongest eligible).
  5. Refit LR and GBDT on all non-holdout rows of seeds 0..13 (without re-selecting tau).
  6. Run online simulator evaluation for all 7 official methods x pi in {1.0, 0.1, 0.0} x test seeds 14..19
     with resampled roster, tracking both full-task metrics and 15-prompt unique-prompt hold-out metrics
     plus the frozen §6 post-hoc incomplete oracle side metric.
  7. Run n=6 paired bootstrap (B=10,000, 95% percentile CIs, Holm within each pi x metric over all 21 method pairs)
     and render summary JSON/CSV/Markdown + descriptive accuracy-cost Pareto figure.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import itertools
import json
import math
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_leak_spec = importlib.util.spec_from_file_location("check_t5_leakage", ROOT / "scripts/check_t5_leakage.py")
_leak_mod = importlib.util.module_from_spec(_leak_spec)
_leak_spec.loader.exec_module(_leak_mod)
run_leakage_check = _leak_mod.check
from tokenmarket.config import deep_merge, load_config  # noqa: E402
from tokenmarket.roster import materialize, roster_seed  # noqa: E402
from tokenmarket.sellers import Reputation  # noqa: E402
from tokenmarket.sim import build_backends, prepare, run_single  # noqa: E402
from tokenmarket.t5_export import (  # noqa: E402
    BEHAVIOR_EPSILON,
    EVAL_PIS,
    HOLDOUT_COUNT,
    HOLDOUT_RNG_SEED,
    INNER_FIT_SEEDS,
    INNER_VAL_SEEDS,
    LABEL,
    PROTOCOL_T5_SHA256,
    SCALE_YAML_SHA256,
    TAU_GRID,
    TEST_SEEDS,
    TRAIN_SEEDS,
    compute_billed_token_fallbacks,
    holdout_prompt_hashes,
    write_t5_export,
)
from tokenmarket.t5_models import (  # noqa: E402
    T5BehaviorPolicy,
    T5CheapestPolicy,
    T5RandomPolicy,
    T5RunObserver,
    T5StrongestPolicy,
    T5TwoStagePolicy,
    TwoStageRecommender,
)
from tokenmarket.v1_metrics import exposure, intent  # noqa: E402

OFFICIAL_METHODS: Tuple[Tuple[str, str, str], ...] = (
    ("t5_logreg", "Two-stage LR (trained on logs)", "trained_recommender"),
    ("t5_gbdt", "Two-stage GBDT (trained on logs)", "trained_recommender"),
    ("cheapest_eligible", "Cheapest eligible", "untrained_baseline"),
    ("strongest_eligible", "Strongest eligible", "untrained_baseline"),
    ("random_eligible", "Random eligible", "untrained_baseline"),
    ("pilot", "Market-adapted PILOT (pilot_v1)", "untrained_baseline"),
    ("stageroute", "Market-adapted StageRoute (stageroute_v1)", "untrained_baseline"),
)
METHOD_NAMES = tuple(m[0] for m in OFFICIAL_METHODS)
METHOD_LABELS = {m[0]: m[1] for m in OFFICIAL_METHODS}
METHOD_FAMILIES = {m[0]: m[2] for m in OFFICIAL_METHODS}

PRIMARY_METRICS = ("accuracy", "cost_per_task", "violation_rate", "E", "fill_rate")
SIDE_METRICS = ("oracle_accuracy_regret", "oracle_cost_regret", "oracle_ebc_regret", "oracle_defined_rate", "E_tok", "Q")
ALL_METRICS = PRIMARY_METRICS + SIDE_METRICS

B_BOOT = 10_000
ALPHA = 0.05
RNG_SEED = 20261122

_PREP_CACHE: Dict = {}


class _MemLog:
    def __init__(self):
        self.records: List[Dict] = []

    def write(self, r: Dict) -> None:
        self.records.append(r)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_frozen_inputs(protocol_path: Path, config_path: Path) -> Dict[str, str]:
    p_hash = sha256_file(protocol_path)
    c_hash = sha256_file(config_path)
    if p_hash != PROTOCOL_T5_SHA256:
        raise SystemExit(f"PROTOCOL_T5.md sha256 mismatch: {p_hash} != {PROTOCOL_T5_SHA256}")
    if c_hash != SCALE_YAML_SHA256:
        raise SystemExit(f"scale.yaml sha256 mismatch: {c_hash} != {SCALE_YAML_SHA256}")
    return {"protocol_sha256": p_hash, "scale_yaml_sha256": c_hash}


def check_safe_out(out_dir: Path, allow_smoke: bool = False) -> None:
    ap = out_dir.resolve()
    res_root = (ROOT / "results").resolve()
    try:
        rel = ap.relative_to(res_root)
    except ValueError:
        return  # outside results/ (e.g. /workspace/token-market-t5-run/smoke) is fine
    parts = rel.parts
    if len(parts) >= 2 and parts[0] == "v1.0" and parts[1] == "t5":
        return
    if allow_smoke and len(parts) >= 1 and parts[0] == "_smoke":
        return
    raise SystemExit(f"Refusing to write inside results/ outside results/v1.0/t5/: {out_dir}")


def _t5_cfg(base: Dict, pi: float, seed: int, n_tasks: Optional[int] = None, n_rounds: Optional[int] = None) -> Dict:
    over: Dict = {
        "market": {
            "compliance_filter": True,
            "feedback": {
                "mode": "sparse" if pi < 1.0 else "immediate",
                "delay_L": 0,
                "reveal_prob": float(pi),
            },
        },
        "roster": {"resample_per_seed": True},
    }
    if n_tasks is not None:
        over.setdefault("run", {})["n_tasks"] = int(n_tasks)
    if n_rounds is not None:
        over.setdefault("run", {})["n_rounds"] = int(n_rounds)
    cfg = deep_merge(base, over)
    return materialize(cfg, seed)


def _get_prepared(cfg: Dict, cache_file: str, backend_override: Optional[str] = None):
    key = (
        backend_override,
        cache_file,
        json.dumps(cfg.get("task_pool", {}), sort_keys=True),
        json.dumps(sorted({s["claimed_model"] for s in cfg["sellers"]} | {s["actual_model"] for s in cfg["sellers"]})),
    )
    if key not in _PREP_CACHE:
        pool, cache, stats, _ = prepare(cfg, backend_override, cache_file, None, lambda *a: None)
        _PREP_CACHE[key] = (pool, cache, stats)
    return _PREP_CACHE[key]


def _run_behavior_seed(job: Dict) -> Tuple[int, List[Dict], List[Dict], Dict]:
    seed = int(job["seed"])
    cfg = _t5_cfg(job["base"], 1.0, seed, job.get("n_tasks"), job.get("n_rounds"))
    pool, cache, stats = _get_prepared(cfg, job["cache_file"], job.get("backend_override"))
    sb = {job["backend_override"]} if job.get("backend_override") else {s.get("backend", "mock") for s in cfg["sellers"]}
    backends = build_backends(cfg, sb, cache)
    rep = Reputation(cfg["models"], stats)
    run_id = f"t5__behavior__pi1__seed{seed}"
    pol = T5BehaviorPolicy(cfg, seed, epsilon=BEHAVIOR_EPSILON)
    obs = T5RunObserver(
        cfg, seed, cache, set(job["holdout_hashes"]), collect_training=True
    )
    lg = _MemLog()
    m = run_single(
        cfg, "posted_price", "t5_recommender_compliant", seed, backends, rep, lg, pool,
        backend_override=job.get("backend_override"),
        t5_policy=pol, run_id_override=run_id, t5_observer=obs,
    )
    summ = obs.summarize(holdout_only=None)
    summ["seed"] = seed
    summ["run_id"] = run_id
    summ["roster_seed"] = roster_seed(cfg["roster"], seed)
    summ["n_train_rows_collected"] = len(obs.train_features)
    summ["n_train_pos_collected"] = sum(int(r[LABEL]) for r in obs.train_labels)
    return seed, obs.train_features, obs.train_labels, summ


def _run_eval_job(job: Dict) -> Dict:
    method = job["method"]
    pi = float(job["pi"])
    seed = int(job["seed"])
    cfg = _t5_cfg(job["base"], pi, seed, job.get("n_tasks"), job.get("n_rounds"))
    pool, cache, stats = _get_prepared(cfg, job["cache_file"], job.get("backend_override"))
    sb = {job["backend_override"]} if job.get("backend_override") else {s.get("backend", "mock") for s in cfg["sellers"]}
    backends = build_backends(cfg, sb, cache)
    rep = Reputation(cfg["models"], stats)

    run_id = job.get("run_id") or f"t5__{method}__pi{pi:g}__seed{seed}"
    fb_model = job["fallback_model_billed"]
    fb_global = job["fallback_global_billed"]
    obs = T5RunObserver(
        cfg, seed, cache, set(job["holdout_hashes"]),
        fallback_model_billed=fb_model, fallback_global_billed=fb_global,
        collect_training=False,
    )

    t5_pol = None
    if method == "t5_logreg":
        sim_policy = "t5_recommender_compliant"
        t5_pol = T5TwoStagePolicy(cfg, seed, job["recommender"])
    elif method == "t5_gbdt":
        sim_policy = "t5_recommender_compliant"
        t5_pol = T5TwoStagePolicy(cfg, seed, job["recommender"])
    elif method == "cheapest_eligible":
        sim_policy = "t5_recommender_compliant"
        t5_pol = T5CheapestPolicy(cfg, seed, fb_model, fb_global)
    elif method == "strongest_eligible":
        sim_policy = "t5_recommender_compliant"
        t5_pol = T5StrongestPolicy(cfg, seed)
    elif method == "random_eligible":
        sim_policy = "t5_recommender_compliant"
        t5_pol = T5RandomPolicy(cfg, seed)
    elif method == "pilot":
        sim_policy = "pilot_v1_compliant"
    elif method == "stageroute":
        sim_policy = "stageroute_v1_compliant"
    else:
        raise ValueError(f"unknown T5 method {method!r}")

    lg = _MemLog()
    m = run_single(
        cfg, "posted_price", sim_policy, seed, backends, rep, lg, pool,
        backend_override=job.get("backend_override"),
        t5_policy=t5_pol, run_id_override=run_id, t5_observer=obs,
    )
    recs = lg.records
    exp_m = exposure(recs)
    int_m = intent(m, recs, int(cfg["run"]["n_rounds"]))
    all_s = obs.summarize(holdout_only=None)
    hold_s = obs.summarize(holdout_only=True)
    nonhold_s = obs.summarize(holdout_only=False)

    # Sanity-check that observer full-task metrics match simulator run_metrics
    assert abs(all_s["accuracy"] - m["task_accuracy"]) < 1e-12
    assert abs(all_s["cost_per_task"] - m["mean_cost_per_task_incl_audit"]) < 1e-12
    assert abs(all_s["violation_rate"] - m["compliance_violation_rate"]) < 1e-12
    assert abs(all_s["E"] - exp_m["E"]) < 1e-12
    assert abs(all_s["fill_rate"] - m["fill_rate"]) < 1e-12

    return {
        "method": method,
        "label": METHOD_LABELS.get(method, method),
        "family": METHOD_FAMILIES.get(method, "unknown"),
        "pi": pi,
        "seed": seed,
        "run_id": run_id,
        "roster_seed": roster_seed(cfg["roster"], seed),
        "all": {
            **all_s,
            "E_tok": float(exp_m["E_tok"]),
            "Q": int_m["Q"],
            "tail_trade": bool(int_m["tail_trade"]),
            "n_audits": int(m["n_audits"]),
        },
        "holdout": {
            **hold_s,
            "E_tok": None,
            "Q": None,
            "tail_trade": None,
        },
        "non_holdout": nonhold_s,
    }


def _select_tau_for_learner(
    model_kind: str,
    inner_fit_feats: List[Dict],
    inner_fit_labs: List[Dict],
    strongest_val_acc: float,
    base: Dict,
    val_seeds: Sequence[int],
    holdout_hashes: Sequence[str],
    cache_file: str,
    jobs: int,
    backend_override: Optional[str],
    n_tasks: Optional[int],
    n_rounds: Optional[int],
) -> Dict:
    """Protocol §3 tau selection on inner validation seeds 10..13 (non-holdout tasks only)."""
    fb_model, fb_global = compute_billed_token_fallbacks(inner_fit_feats, inner_fit_labs)
    y_fit = [int(r[LABEL]) for r in inner_fit_labs]
    fitted = TwoStageRecommender(model_kind, TAU_GRID[0], fb_model, fb_global).fit(inner_fit_feats, y_fit)

    method_name = f"t5_{model_kind}"
    grid_rows = []
    eval_jobs = []
    for tau in TAU_GRID:
        rec_tau = fitted.clone_with_tau(tau)
        for s in val_seeds:
            eval_jobs.append({
                "method": method_name,
                "pi": 1.0,
                "seed": int(s),
                "base": base,
                "cache_file": cache_file,
                "backend_override": backend_override,
                "holdout_hashes": list(holdout_hashes),
                "fallback_model_billed": fb_model,
                "fallback_global_billed": fb_global,
                "recommender": rec_tau,
                "run_id": f"t5__tauval_{model_kind}_t{tau:.2f}__seed{s}",
                "n_tasks": n_tasks,
                "n_rounds": n_rounds,
                "_tau": float(tau),
            })

    if jobs > 1:
        with Pool(jobs) as pool:
            results = pool.map(_run_eval_job, eval_jobs, chunksize=1)
    else:
        results = [_run_eval_job(j) for j in eval_jobs]

    by_tau: Dict[float, List[Dict]] = {float(t): [] for t in TAU_GRID}
    for j, res in zip(eval_jobs, results):
        by_tau[j["_tau"]].append(res)

    for tau in TAU_GRID:
        runs = by_tau[float(tau)]
        accs = [r["non_holdout"]["accuracy"] for r in runs]
        costs = [r["non_holdout"]["cost_per_task"] for r in runs]
        es = [r["non_holdout"]["E"] for r in runs]
        fills = [r["non_holdout"]["fill_rate"] for r in runs]
        grid_rows.append({
            "tau": float(tau),
            "val_accuracy_non_holdout": float(np.mean(accs)),
            "val_cost_per_task_non_holdout": float(np.mean(costs)),
            "val_E_non_holdout": float(np.mean(es)),
            "val_fill_rate_non_holdout": float(np.mean(fills)),
            "meets_strongest_floor": float(np.mean(accs)) >= strongest_val_acc,
            "per_seed": [
                {
                    "seed": r["seed"],
                    "accuracy": r["non_holdout"]["accuracy"],
                    "cost_per_task": r["non_holdout"]["cost_per_task"],
                    "E": r["non_holdout"]["E"],
                    "fill_rate": r["non_holdout"]["fill_rate"],
                }
                for r in runs
            ],
        })

    # Protocol §3 exact selection rule:
    # Among tau with val_acc >= strongest_val_acc, choose lowest cost_per_task (tie: lower tau).
    # If none reaches the floor, choose highest val_acc (tie: lower cost_per_task, then lower tau).
    passing = [g for g in grid_rows if g["val_accuracy_non_holdout"] >= strongest_val_acc]
    if passing:
        floor_rule = False
        chosen = min(passing, key=lambda g: (g["val_cost_per_task_non_holdout"], g["tau"]))
    else:
        floor_rule = True
        chosen = min(
            grid_rows,
            key=lambda g: (-g["val_accuracy_non_holdout"], g["val_cost_per_task_non_holdout"], g["tau"]),
        )

    return {
        "model_kind": model_kind,
        "selected_tau": float(chosen["tau"]),
        "floor_rule_triggered": floor_rule,
        "strongest_val_accuracy_non_holdout": float(strongest_val_acc),
        "chosen_row": chosen,
        "grid": grid_rows,
        "inner_fit_n_rows": len(inner_fit_feats),
        "inner_fit_n_pos": int(sum(y_fit)),
        "inner_fit_fallback_model_billed": fb_model,
        "inner_fit_fallback_global_billed": fb_global,
    }


# --------------------------------------------------------------------------- Statistics (§6)
def holm_adjust(ps: Sequence[float]) -> List[float]:
    m = len(ps)
    if m == 0:
        return []
    order = np.argsort(ps)
    adj = [0.0] * m
    running = 0.0
    for k, idx in enumerate(order):
        running = max(running, min(1.0, (m - k) * float(ps[idx])))
        adj[idx] = running
    return adj


def _rng_for(key: str) -> np.random.Generator:
    digest = hashlib.sha256(f"{RNG_SEED}:{key}".encode("utf-8")).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little"))


def boot_marginal(vals: Sequence[Optional[float]], key: str, n_boot: int = B_BOOT) -> Dict:
    clean = [float(v) for v in vals if v is not None and math.isfinite(float(v))]
    n = len(clean)
    if n == 0:
        return {"mean": None, "lo": None, "hi": None, "n": 0}
    arr = np.asarray(clean, dtype=float)
    rng = _rng_for(key)
    idx = rng.integers(0, n, size=(n_boot, n))
    bm = arr[idx].mean(axis=1)
    lo, hi = np.percentile(bm, [2.5, 97.5])
    return {"mean": float(arr.mean()), "lo": float(lo), "hi": float(hi), "n": n}


def boot_paired(xs: Sequence[Optional[float]], ys: Sequence[Optional[float]], key: str, n_boot: int = B_BOOT) -> Dict:
    pairs = [
        float(x) - float(y)
        for x, y in zip(xs, ys)
        if x is not None and y is not None and math.isfinite(float(x)) and math.isfinite(float(y))
    ]
    n = len(pairs)
    if n == 0:
        return {"delta_mean": None, "delta_lo": None, "delta_hi": None, "p_raw": None, "n": 0}
    d = np.asarray(pairs, dtype=float)
    rng = _rng_for(key)
    idx = rng.integers(0, n, size=(n_boot, n))
    bm = d[idx].mean(axis=1)
    lo, hi = np.percentile(bm, [2.5, 97.5])
    p_raw = min(1.0, 2.0 * min(float((bm <= 0.0).mean()), float((bm >= 0.0).mean())))
    return {
        "delta_mean": float(d.mean()),
        "delta_lo": float(lo),
        "delta_hi": float(hi),
        "p_raw": float(p_raw),
        "n": n,
    }


def analyze_subset(
    eval_rows: Sequence[Dict],
    subset_key: str,
    pis: Sequence[float],
    test_seeds: Sequence[int],
    n_boot: int = B_BOOT,
) -> Tuple[List[Dict], List[Dict]]:
    """Compute marginal cells and 21-pair Holm-corrected contrasts within each (pi, metric)."""
    by_mps = {(r["method"], float(r["pi"]), int(r["seed"])): r[subset_key] for r in eval_rows}
    metrics = PRIMARY_METRICS + (SIDE_METRICS if subset_key == "all" else SIDE_METRICS[:4])

    cells = []
    for pi in pis:
        for method in METHOD_NAMES:
            cell = {
                "subset": subset_key,
                "pi": float(pi),
                "method": method,
                "label": METHOD_LABELS[method],
                "family": METHOD_FAMILIES[method],
                "n_runs": len(test_seeds),
            }
            for met in metrics:
                vals = [by_mps[(method, float(pi), int(s))].get(met) for s in test_seeds]
                cell[met] = boot_marginal(vals, f"marg:{subset_key}:{pi:g}:{method}:{met}", n_boot=n_boot)
            if subset_key == "all":
                tt = [1 for s in test_seeds if by_mps[(method, float(pi), int(s))].get("tail_trade")]
                cell["tail_trade_runs"] = len(tt)
                cell["tail_trade_rate"] = len(tt) / len(test_seeds) if test_seeds else 0.0
            cells.append(cell)

    contrasts = []
    pairs = list(itertools.combinations(METHOD_NAMES, 2))
    assert len(pairs) == 21
    for pi in pis:
        for met in metrics:
            fam_rows = []
            for m_a, m_b in pairs:
                xs = [by_mps[(m_a, float(pi), int(s))].get(met) for s in test_seeds]
                ys = [by_mps[(m_b, float(pi), int(s))].get(met) for s in test_seeds]
                st = boot_paired(xs, ys, f"pair:{subset_key}:{pi:g}:{met}:{m_a}_vs_{m_b}", n_boot=n_boot)
                fam_rows.append({
                    "subset": subset_key,
                    "pi": float(pi),
                    "metric": met,
                    "method_a": m_a,
                    "method_b": m_b,
                    "family_size": len(pairs),
                    **st,
                })
            # Holm correction within each (pi, metric) over all 21 pairs (Protocol §6)
            valid_idx = [i for i, r in enumerate(fam_rows) if r["p_raw"] is not None]
            if valid_idx:
                adj = holm_adjust([fam_rows[i]["p_raw"] for i in valid_idx])
                for i, p_h in zip(valid_idx, adj):
                    fam_rows[i]["p_holm"] = float(p_h)
                    fam_rows[i]["significant"] = bool(p_h < ALPHA)
            for r in fam_rows:
                if "p_holm" not in r:
                    r["p_holm"] = None
                    r["significant"] = False
            contrasts.extend(fam_rows)
    return cells, contrasts


def _write_per_seed_csv(eval_rows: Sequence[Dict], subset_key: str, path: Path) -> None:
    metrics = PRIMARY_METRICS + (SIDE_METRICS if subset_key == "all" else SIDE_METRICS[:4])
    cols = ["method", "label", "family", "pi", "seed", "run_id", "roster_seed", "n_tasks"] + list(metrics)
    if subset_key == "all":
        cols += ["tail_trade", "n_audits"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in eval_rows:
            sub = r[subset_key]
            row = [r["method"], r["label"], r["family"], r["pi"], r["seed"], r["run_id"], r["roster_seed"], sub["n_tasks"]]
            row += ["" if sub.get(m) is None else repr(sub[m]) for m in metrics]
            if subset_key == "all":
                row += [sub.get("tail_trade"), sub.get("n_audits")]
            w.writerow(row)


def _write_cells_csv(cells: Sequence[Dict], subset_key: str, path: Path) -> None:
    metrics = PRIMARY_METRICS + (SIDE_METRICS if subset_key == "all" else SIDE_METRICS[:4])
    cols = ["subset", "pi", "method", "label", "family", "n_runs"]
    for m in metrics:
        cols += [f"{m}_mean", f"{m}_lo", f"{m}_hi"]
    if subset_key == "all":
        cols += ["tail_trade_runs", "tail_trade_rate"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for c in cells:
            row = [c["subset"], c["pi"], c["method"], c["label"], c["family"], c["n_runs"]]
            for m in metrics:
                d = c[m]
                row += ["" if d[k] is None else repr(d[k]) for k in ("mean", "lo", "hi")]
            if subset_key == "all":
                row += [c["tail_trade_runs"], repr(c["tail_trade_rate"])]
            w.writerow(row)


def _write_contrasts_csv(contrasts: Sequence[Dict], path: Path) -> None:
    cols = ["subset", "pi", "metric", "method_a", "method_b", "family_size", "n",
            "delta_mean", "delta_lo", "delta_hi", "p_raw", "p_holm", "significant"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, cols)
        w.writeheader()
        for r in contrasts:
            w.writerow({k: "" if r.get(k) is None else r[k] for k in cols})


def plot_pareto(cells_all: Sequence[Dict], out_dir: Path, is_smoke: bool) -> Tuple[str, str]:
    """Protocol §6 descriptive accuracy-cost Pareto plot (test seeds 14..19, pi=1.0)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pi1 = [c for c in cells_all if abs(c["pi"] - 1.0) < 1e-12]
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    styles = {
        "t5_logreg": ("#1b9e77", "o", "Two-stage LR (trained)"),
        "t5_gbdt": ("#d95f02", "s", "Two-stage GBDT (trained)"),
        "cheapest_eligible": ("#7570b3", "^", "Cheapest eligible"),
        "strongest_eligible": ("#e7298a", "v", "Strongest eligible"),
        "random_eligible": ("#66a61e", "D", "Random eligible"),
        "pilot": ("#1f78b4", "P", "PILOT (pilot_v1)"),
        "stageroute": ("#a65628", "X", "StageRoute (stageroute_v1)"),
    }
    for c in pi1:
        m = c["method"]
        col, mk, lab = styles[m]
        xm, xlo, xhi = c["cost_per_task"]["mean"], c["cost_per_task"]["lo"], c["cost_per_task"]["hi"]
        ym, ylo, yhi = c["accuracy"]["mean"], c["accuracy"]["lo"], c["accuracy"]["hi"]
        ax.errorbar(
            xm, ym,
            xerr=[[max(0.0, xm - xlo)], [max(0.0, xhi - xm)]],
            yerr=[[max(0.0, ym - ylo)], [max(0.0, yhi - ym)]],
            fmt=mk, color=col, markersize=7, capsize=3, elinewidth=1.2, label=lab,
        )
    ax.set_xlabel("Cost per task (synthetic market units, lower is better)")
    ax.set_ylabel("Task accuracy (higher is better)")
    title = "T5 Accuracy–Cost Pareto (pi=1, test seeds, descriptive)"
    if is_smoke:
        title = "[NON-OFFICIAL SMOKE] " + title
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(fontsize=8, loc="best", frameon=True)
    fig.tight_layout()
    pdf_path = out_dir / "fig_t5_pareto_acc_cost.pdf"
    png_path = out_dir / "fig_t5_pareto_acc_cost.png"
    fig.savefig(pdf_path, dpi=200)
    fig.savefig(png_path, dpi=200)
    plt.close(fig)
    return str(pdf_path), str(png_path)


def _fmt_ci(d: Dict, digits: int = 4) -> str:
    if d["mean"] is None:
        return "—"
    return f"{d['mean']:.{digits}f} [{d['lo']:.{digits}f}, {d['hi']:.{digits}f}]"


def render_markdown(payload: Dict) -> str:
    is_smoke = payload["smoke"]
    L = []
    if is_smoke:
        L += ["# [NON-OFFICIAL SMOKE] T5 Evaluation Readout", "",
              "> **WARNING: NON-OFFICIAL SMOKE RUN. DO NOT USE IN PAPER.**", ""]
    else:
        L += ["# Official T5 Readout (docs/PROTOCOL_T5.md, frozen 2026-11-22)", ""]
    L += [
        f"- Protocol sha256: `{payload['hashes']['protocol_sha256']}`",
        f"- `configs/v1.0/scale.yaml` sha256: `{payload['hashes']['scale_yaml_sha256']}`",
        f"- Train seeds: `{payload['train_seeds']}` (inner fit `{payload['inner_fit_seeds']}`, inner val `{payload['inner_val_seeds']}`); "
        f"Test seeds: `{payload['test_seeds']}` (**n = {len(payload['test_seeds'])} test runs**, NOT 20).",
        f"- Bootstrap: B = {payload['n_boot']}, 95% percentile CIs, paired two-sided bootstrap p-values, "
        f"Holm within each (pi, metric) over all 21 pairs of the 7 official methods (alpha = {ALPHA}).",
        f"- Leakage check passed: `{payload['leakage_check']['passed']}` "
        f"({payload['leakage_check']['diagnostics']['n_feature_rows']} train rows, 0 offenders).",
        f"- Hold-out prompts: {len(payload['holdout_prompt_hashes'])} unique prompt hashes drawn via "
        f"`random.Random('{HOLDOUT_RNG_SEED}')` (excluded from training and tau selection).",
        "",
        f"## Frozen tau selection (inner val seeds {payload['inner_val_seeds']}, non-holdout tasks only)",
        "",
        "| learner | selected tau | floor_rule_triggered | strongest val acc | chosen val acc | chosen val cost/task |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for k in ("logreg", "gbdt"):
        ts = payload["tau_selection"][k]
        ch = ts["chosen_row"]
        L.append(
            f"| Two-stage {k.upper()} | {ts['selected_tau']:.2f} | {ts['floor_rule_triggered']} | "
            f"{ts['strongest_val_accuracy_non_holdout']:.4f} | {ch['val_accuracy_non_holdout']:.4f} | "
            f"{ch['val_cost_per_task_non_holdout']:.5f} |"
        )

    for title, cells_key, contrasts_key in (
        (f"Main & pi side tables (ALL test tasks, seeds {payload['test_seeds']}, n={payload['n_test_runs']})", "cells_all", "contrasts_all"),
        (f"Unique-prompt hold-out side tables (15 hold-out prompt hashes, seeds {payload['test_seeds']}, n={payload['n_test_runs']})", "cells_holdout", "contrasts_holdout"),
    ):
        L += ["", f"## {title}", ""]
        cells = payload[cells_key]
        contrasts = payload[contrasts_key]
        for pi in payload["pis"]:
            sub = [c for c in cells if abs(c["pi"] - pi) < 1e-12]
            tag = "Main table" if (cells_key == "cells_all" and abs(pi - 1.0) < 1e-12) else "Required side table"
            L += [
                f"### pi = {pi:g} ({tag})",
                "",
                "| Method | Family | Accuracy | Cost/task | Violation | E (fraud_share) | Fill rate | Oracle acc regret (side) | Oracle cost regret (side) |",
                "|---|---|---|---|---|---|---|---|---|",
            ]
            for c in sub:
                L.append(
                    f"| {c['label']} | {c['family']} | {_fmt_ci(c['accuracy'], 4)} | {_fmt_ci(c['cost_per_task'], 5)} | "
                    f"{_fmt_ci(c['violation_rate'], 4)} | {_fmt_ci(c['E'], 4)} | {_fmt_ci(c['fill_rate'], 4)} | "
                    f"{_fmt_ci(c['oracle_accuracy_regret'], 4)} | {_fmt_ci(c['oracle_cost_regret'], 5)} |"
                )
            sig = [r for r in contrasts if abs(r["pi"] - pi) < 1e-12 and r["metric"] in PRIMARY_METRICS and r["significant"]]
            L += ["", f"Significant Holm-adjusted primary-metric pairs at pi={pi:g} (p_Holm < 0.05, family size 21): **{len(sig)}**."]
            if sig:
                L += ["", "| Metric | Method A | Method B | Delta (A - B) [95% CI] | p_raw | p_Holm |", "|---|---|---|---|---:|---:|"]
                for r in sig:
                    L.append(
                        f"| {r['metric']} | {r['method_a']} | {r['method_b']} | "
                        f"{r['delta_mean']:+.5f} [{r['delta_lo']:+.5f}, {r['delta_hi']:+.5f}] | "
                        f"{r['p_raw']:.4f} | {r['p_holm']:.4f} |"
                    )
            L.append("")

    return "\n".join(L) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Official frozen T5 runner (docs/PROTOCOL_T5.md)")
    ap.add_argument("--config", default=str(ROOT / "configs/v1.0/scale.yaml"))
    ap.add_argument("--protocol", default=str(ROOT / "docs/PROTOCOL_T5.md"))
    ap.add_argument("--cache-file", default=str(ROOT / "cache/llm_outputs.jsonl"))
    ap.add_argument("--out", required=True, help="Official: results/v1.0/t5 ; Smoke: /workspace/token-market-t5-run/smoke")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--n-boot", type=int, default=B_BOOT)
    ap.add_argument("--smoke", action="store_true", help="Non-official fast smoke run (fewer rounds/tasks/seeds)")
    ap.add_argument("--backend-override", default=None, help="Smoke/CI only (must be None for official)")
    args = ap.parse_args(argv)

    out_dir = Path(args.out)
    check_safe_out(out_dir, allow_smoke=args.smoke)
    hashes = verify_frozen_inputs(Path(args.protocol), Path(args.config))

    if not args.smoke and args.backend_override is not None:
        raise SystemExit("Official T5 run forbids --backend-override")

    out_dir.mkdir(parents=True, exist_ok=True)
    in_progress_path = out_dir / "IN_PROGRESS.json"
    completed_path = out_dir / "COMPLETED.json"
    if completed_path.exists():
        completed_path.unlink()

    t0 = time.time()
    in_progress_path.write_text(json.dumps({
        "status": "IN_PROGRESS",
        "smoke": bool(args.smoke),
        "pid": os.getpid(),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "argv": sys.argv[1:] if argv is None else list(argv),
        **hashes,
    }, indent=1), encoding="utf-8")

    base = load_config(args.config)
    if args.smoke:
        train_seeds = (0, 1, 2, 3)
        inner_fit_seeds = (0, 1)
        inner_val_seeds = (2, 3)
        test_seeds = (14, 15)
        pis = (1.0, 0.1, 0.0)
        n_tasks_over: Optional[int] = 160
        n_rounds_over: Optional[int] = 16
        n_boot = min(args.n_boot, 1000)
    else:
        train_seeds = TRAIN_SEEDS
        inner_fit_seeds = INNER_FIT_SEEDS
        inner_val_seeds = INNER_VAL_SEEDS
        test_seeds = TEST_SEEDS
        pis = EVAL_PIS
        n_tasks_over = None
        n_rounds_over = None
        n_boot = int(args.n_boot)

    # Determine frozen 15 hold-out prompt hashes from the pool
    sample_cfg = _t5_cfg(base, 1.0, 0, n_tasks_over, n_rounds_over)
    pool0, _, _ = _get_prepared(sample_cfg, args.cache_file, args.backend_override)
    holdout_hashes = holdout_prompt_hashes(pool0)
    assert len(holdout_hashes) == HOLDOUT_COUNT

    # Step 1: Collect behavior-policy training logs (seeds 0..13, pi=1.0, resampled roster)
    print(f"[T5] Step 1: Collecting training logs on seeds {list(train_seeds)} (pi=1.0, resampled roster)...", flush=True)
    beh_jobs = [
        {
            "seed": int(s),
            "base": base,
            "cache_file": args.cache_file,
            "backend_override": args.backend_override,
            "holdout_hashes": holdout_hashes,
            "n_tasks": n_tasks_over,
            "n_rounds": n_rounds_over,
        }
        for s in train_seeds
    ]
    if args.jobs > 1:
        with Pool(args.jobs) as p:
            beh_res = p.map(_run_behavior_seed, beh_jobs, chunksize=1)
    else:
        beh_res = [_run_behavior_seed(j) for j in beh_jobs]
    beh_res.sort(key=lambda x: x[0])

    train_features: List[Dict] = []
    train_labels: List[Dict] = []
    behavior_summaries: List[Dict] = []
    for _, fs, ls, summ in beh_res:
        train_features.extend(fs)
        train_labels.extend(ls)
        behavior_summaries.append(summ)

    export_dir = out_dir / "export"
    exp_paths = write_t5_export(
        train_features,
        train_labels,
        str(export_dir),
        holdout_hashes,
        extra_meta={"smoke": bool(args.smoke), "behavior_epsilon": BEHAVIOR_EPSILON},
    )
    print(f"[T5] Exported {len(train_features)} non-holdout served train rows ({sum(int(r[LABEL]) for r in train_labels)} pos).", flush=True)

    # Step 2: Mandatory T5 leakage check BEFORE any tau selection or scoring (§2, §8)
    print("[T5] Step 2: Running T5 leakage check...", flush=True)
    offenders, notes, leak_diag = run_leakage_check(
        [exp_paths["features_train"]],
        [exp_paths["labels_train"]],
        exp_paths["manifest"],
        threshold=0.95,
        test_seeds=test_seeds,
    )
    leak_report = {
        "passed": len(offenders) == 0,
        "threshold": 0.95,
        "offenders": offenders,
        "notes": notes,
        "diagnostics": leak_diag,
    }
    (out_dir / "leakage_check.json").write_text(json.dumps(leak_report, indent=1), encoding="utf-8")
    if offenders:
        in_progress_path.write_text(json.dumps({
            "status": "STOPPED_LEAKAGE_CHECK_FAILED",
            "offenders": offenders,
        }, indent=1), encoding="utf-8")
        print(f"[T5] LEAKAGE CHECK FAILED ({len(offenders)} offenders) — STOPPING per §8!", flush=True)
        for o in offenders:
            print(f"  - {o}", flush=True)
        return 1
    print(f"[T5] Leakage check PASSED (0 offenders, max |corr| = {max(leak_diag['max_abs_corr'].values() or [0.0]):.4f}).", flush=True)

    # Step 3: Select tau separately for LR and GBDT on inner split (fit 0..9, val 10..13, non-holdout tasks)
    print(f"[T5] Step 3: Selecting tau on inner split (fit {list(inner_fit_seeds)}, val {list(inner_val_seeds)})...", flush=True)
    inner_fit_set = set(inner_fit_seeds)
    inner_fit_feats = [f for f in train_features if int(f["seed"]) in inner_fit_set]
    inner_fit_labs = [l for l in train_labels if int(l["seed"]) in inner_fit_set]

    # Run strongest_eligible on inner validation seeds to obtain accuracy floor
    fb_inner_m, fb_inner_g = compute_billed_token_fallbacks(inner_fit_feats, inner_fit_labs)
    strongest_val_jobs = [
        {
            "method": "strongest_eligible",
            "pi": 1.0,
            "seed": int(s),
            "base": base,
            "cache_file": args.cache_file,
            "backend_override": args.backend_override,
            "holdout_hashes": holdout_hashes,
            "fallback_model_billed": fb_inner_m,
            "fallback_global_billed": fb_inner_g,
            "run_id": f"t5__tauval_strongest__seed{s}",
            "n_tasks": n_tasks_over,
            "n_rounds": n_rounds_over,
        }
        for s in inner_val_seeds
    ]
    if args.jobs > 1:
        with Pool(args.jobs) as p:
            strongest_val_res = p.map(_run_eval_job, strongest_val_jobs, chunksize=1)
    else:
        strongest_val_res = [_run_eval_job(j) for j in strongest_val_jobs]
    strongest_val_acc = float(np.mean([r["non_holdout"]["accuracy"] for r in strongest_val_res]))
    print(f"[T5] Inner-val strongest_eligible accuracy (non-holdout) = {strongest_val_acc:.4f}", flush=True)

    tau_sel = {}
    for kind in ("logreg", "gbdt"):
        tau_sel[kind] = _select_tau_for_learner(
            kind, inner_fit_feats, inner_fit_labs, strongest_val_acc,
            base, inner_val_seeds, holdout_hashes, args.cache_file,
            args.jobs, args.backend_override, n_tasks_over, n_rounds_over,
        )
        print(
            f"[T5]   {kind}: selected_tau={tau_sel[kind]['selected_tau']:.2f}, "
            f"floor_rule={tau_sel[kind]['floor_rule_triggered']}, "
            f"val_acc={tau_sel[kind]['chosen_row']['val_accuracy_non_holdout']:.4f}, "
            f"val_cost={tau_sel[kind]['chosen_row']['val_cost_per_task_non_holdout']:.5f}",
            flush=True,
        )
    (out_dir / "tau_selection.json").write_text(json.dumps(tau_sel, indent=1), encoding="utf-8")

    # Step 4: Refit LR and GBDT on ALL non-holdout rows of seeds 0..13 (without re-selecting tau)
    print(f"[T5] Step 4: Refitting final LR and GBDT on all non-holdout train rows (seeds {list(train_seeds)})...", flush=True)
    fb_full_m, fb_full_g = compute_billed_token_fallbacks(train_features, train_labels)
    y_full = [int(r[LABEL]) for r in train_labels]
    final_models = {
        "t5_logreg": TwoStageRecommender("logreg", tau_sel["logreg"]["selected_tau"], fb_full_m, fb_full_g).fit(train_features, y_full),
        "t5_gbdt": TwoStageRecommender("gbdt", tau_sel["gbdt"]["selected_tau"], fb_full_m, fb_full_g).fit(train_features, y_full),
    }

    # Step 5: Online simulator evaluation for all 7 official methods x pi x test seeds (with resume)
    ckpt_path = out_dir / "completed_eval_runs.jsonl"
    done_map: Dict[Tuple[str, float, int], Dict] = {}
    if ckpt_path.exists():
        for line in ckpt_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            done_map[(r["method"], float(r["pi"]), int(r["seed"]))] = r

    planned = [(m, float(pi), int(s)) for m in METHOD_NAMES for pi in pis for s in test_seeds]
    todo_jobs = []
    for m, pi, s in planned:
        if (m, pi, s) in done_map:
            continue
        job = {
            "method": m,
            "pi": pi,
            "seed": s,
            "base": base,
            "cache_file": args.cache_file,
            "backend_override": args.backend_override,
            "holdout_hashes": holdout_hashes,
            "fallback_model_billed": fb_full_m,
            "fallback_global_billed": fb_full_g,
            "n_tasks": n_tasks_over,
            "n_rounds": n_rounds_over,
        }
        if m in final_models:
            job["recommender"] = final_models[m]
        todo_jobs.append(job)

    print(
        f"[T5] Step 5: Online evaluation — {len(planned)} planned, {len(done_map)} cached, {len(todo_jobs)} to run...",
        flush=True,
    )
    if todo_jobs:
        with ckpt_path.open("a", encoding="utf-8") as ckpt_fh:
            if args.jobs > 1:
                with Pool(args.jobs) as p:
                    for res in p.imap_unordered(_run_eval_job, todo_jobs, chunksize=1):
                        key = (res["method"], float(res["pi"]), int(res["seed"]))
                        done_map[key] = res
                        ckpt_fh.write(json.dumps(res, ensure_ascii=False) + "\n")
                        ckpt_fh.flush()
            else:
                for j in todo_jobs:
                    res = _run_eval_job(j)
                    key = (res["method"], float(res["pi"]), int(res["seed"]))
                    done_map[key] = res
                    ckpt_fh.write(json.dumps(res, ensure_ascii=False) + "\n")
                    ckpt_fh.flush()

    eval_rows = [done_map[k] for k in planned]
    assert len(eval_rows) == len(planned)

    # Step 6: Statistical analysis (§6) for ALL tasks and unique-prompt hold-out side table
    print(f"[T5] Step 6: Running paired bootstrap (B={n_boot}, n={len(test_seeds)}) and Holm correction...", flush=True)
    cells_all, contrasts_all = analyze_subset(eval_rows, "all", pis, test_seeds, n_boot=n_boot)
    cells_hold, contrasts_hold = analyze_subset(eval_rows, "holdout", pis, test_seeds, n_boot=n_boot)

    # Step 7: Write all outputs & descriptive Pareto figure
    _write_per_seed_csv(eval_rows, "all", out_dir / "per_seed.csv")
    _write_per_seed_csv(eval_rows, "holdout", out_dir / "per_seed_holdout.csv")
    _write_cells_csv(cells_all, "all", out_dir / "cells.csv")
    _write_cells_csv(cells_hold, "holdout", out_dir / "cells_holdout.csv")
    _write_contrasts_csv(contrasts_all, out_dir / "contrasts.csv")
    _write_contrasts_csv(contrasts_hold, out_dir / "contrasts_holdout.csv")
    pdf_fig, png_fig = plot_pareto(cells_all, out_dir, is_smoke=bool(args.smoke))

    elapsed = round(time.time() - t0, 2)
    payload = {
        "task": "T5 task-conditioned model/seller recommendation",
        "smoke": bool(args.smoke),
        "hashes": hashes,
        "train_seeds": list(train_seeds),
        "inner_fit_seeds": list(inner_fit_seeds),
        "inner_val_seeds": list(inner_val_seeds),
        "test_seeds": list(test_seeds),
        "n_test_runs": len(test_seeds),
        "pis": list(pis),
        "methods": [{"method": m, "label": l, "family": f} for m, l, f in OFFICIAL_METHODS],
        "n_boot": n_boot,
        "alpha": ALPHA,
        "holdout_rng_seed": HOLDOUT_RNG_SEED,
        "holdout_prompt_hashes": holdout_hashes,
        "behavior_epsilon": BEHAVIOR_EPSILON,
        "behavior_train_summaries": behavior_summaries,
        "fallback_billed_tokens_full_train": {
            "by_claimed_model": fb_full_m,
            "global_mean": fb_full_g,
        },
        "leakage_check": leak_report,
        "tau_selection": tau_sel,
        "cells_all": cells_all,
        "contrasts_all": contrasts_all,
        "cells_holdout": cells_hold,
        "contrasts_holdout": contrasts_hold,
        "pareto_figures": {"pdf": pdf_fig, "png": png_fig},
        "elapsed_s": elapsed,
        "argv": sys.argv[1:] if argv is None else list(argv),
    }
    (out_dir / "t5_eval.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")
    md = render_markdown(payload)
    (out_dir / "t5_eval.md").write_text(md, encoding="utf-8")

    # Remove IN_PROGRESS and write COMPLETED only now that everything finished cleanly.
    if in_progress_path.exists():
        in_progress_path.unlink()
    completed_path.write_text(json.dumps({
        "status": "COMPLETED",
        "smoke": bool(args.smoke),
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "elapsed_s": elapsed,
        "n_eval_runs": len(eval_rows),
        "leakage_passed": True,
        **hashes,
    }, indent=1), encoding="utf-8")

    print(f"[T5] DONE in {elapsed}s -> {out_dir / 't5_eval.md'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
