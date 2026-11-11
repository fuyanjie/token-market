#!/usr/bin/env python3
"""Official PROTOCOL_v1.1 WP2 convergence grid.

Grid (540 runs): routers PILOT, strongest, cascade — all at a=0.1, P=0.25, π=1,
trust_feedback=false — × learners {egreedy, fictitious_play, exp3}
× n_rounds {48, 200, 500}. n_tasks and buyer budget are paired by
tokenmarket.wp1.scale_horizon (n_tasks=10*n_rounds, budget × n_tasks/480).

This script only writes raw runs under results/v1.1/. Convergence CIs,
recommended n_rounds, and Decision A remain Experiment's analysis step.

Official command:

  /workspace/tmvenv/bin/python -u scripts/v1.1/run_wp2.py --out results/v1.1/wp2 --jobs 8
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from multiprocessing import Pool
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tokenmarket.config import load_config  # noqa: E402
from tokenmarket.sim import build_backends, prepare, run_single  # noqa: E402
from tokenmarket.sellers import Reputation  # noqa: E402
from tokenmarket.v1_metrics import MODES, _HIST, exposure, intent, mean_or_none  # noqa: E402
from tokenmarket.wp1 import (  # noqa: E402
    PROTOCOL_SHA256, Cell, MemoryLog, _PREPARED, cell_config,
)

WP2_CELLS = (
    Cell("pilot", "a0.1", 0.25, 1.0),
    Cell("strongest", "a0.1", 0.25, 1.0),
    Cell("cascade", "a0.1", 0.25, 1.0),
)
WP2_ROUNDS = (48, 200, 500)
WP2_LEARNERS = ("egreedy", "fictitious_play", "exp3")
N_SEEDS = 20


def output_path(value):
    path = Path(value).resolve()
    if not path.is_relative_to((ROOT / "results/v1.1").resolve()):
        raise ValueError("all outputs must be under results/v1.1/")
    return path


def write_json(path, value):
    with path.open("x", encoding="utf-8") as fh:
        json.dump(value, fh, indent=2)
        fh.write("\n")


def write_csv(path, rows):
    if not rows:
        return
    with path.open("x", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, list(rows[0]), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v
                             for k, v in row.items()})


def quarter_bounds(n_rounds):
    """Last two official Q windows: length k = max(1, int(n*0.25)), same k as intent() tail."""
    k = max(1, int(n_rounds * 0.25))
    q4 = (n_rounds - k, n_rounds)
    q3 = (n_rounds - 2 * k, n_rounds - k)
    q2 = (n_rounds - 3 * k, n_rounds - 2 * k)
    q1 = (0, n_rounds - 3 * k)
    return (("Q1",) + q1, ("Q2",) + q2, ("Q3",) + q3, ("Q4",) + q4), k


def intent_window(m, records, start, end):
    """Same Q aggregation as intent(), over rounds [start, end)."""
    modes = m.get("strategic_modes") or {}
    banned_all = m.get("strategic_delisted_rounds") or {}
    window = list(range(start, end))
    tail_sales = [r["seller_id"] for r in records
                  if r.get("status") == "allowed" and r.get("seller_id") in modes
                  and start <= int(r["round"]) < end]
    per_mode = {k: [] for k in MODES}
    n_present = n_del = 0
    for sid, ms in sorted(modes.items()):
        hist = {mode: list((m.get(_HIST[mode]) or {}).get(sid, [])) for mode in ms}
        banned = set(banned_all.get(sid, []))
        present = [r for r in window if r not in banned and all(r < len(h) for h in hist.values())]
        delisted = [r for r in window if r in banned]
        n_present += len(present)
        n_del += len(delisted)
        for mode in ms:
            v = mean_or_none(hist[mode][r] for r in present)
            if v is not None:
                per_mode[mode].append(v)
    q = {f"Q_{k}": mean_or_none(v) for k, v in per_mode.items()}
    avail = [v for v in q.values() if v is not None]
    return {"Q": mean_or_none(avail), **q, "tail_trade": bool(tail_sales),
            "tail_sales": len(tail_sales), "Q_present_rounds": n_present,
            "delisted_rounds": n_del}


def per_round_q(m):
    modes = m.get("strategic_modes") or {}
    banned_all = m.get("strategic_delisted_rounds") or {}
    n = 0
    hists = {}
    for sid, ms in modes.items():
        hists[sid] = (ms, {mode: list((m.get(_HIST[mode]) or {}).get(sid, [])) for mode in ms},
                      set(banned_all.get(sid, [])))
        for series in hists[sid][1].values():
            n = max(n, len(series))
    out = []
    for r in range(n):
        vals = []
        for sid, (ms, hist, banned) in hists.items():
            if r in banned:
                continue
            if any(r >= len(hist[mode]) for mode in ms):
                continue
            mode_vals = [hist[mode][r] for mode in ms]
            if mode_vals:
                vals.append(sum(mode_vals) / len(mode_vals))
        out.append(None if not vals else sum(vals) / len(vals))
    return out


def run_id(cell, learner, n_rounds, seed=None):
    base = f"{cell.cell_id}__{learner}__R{n_rounds}"
    return base if seed is None else f"{base}__seed{seed}"


def run_wp2_cell(job):
    cell, seed, n_rounds, learner = job["cell"], job["seed"], job["n_rounds"], job["learner"]
    cfg = cell_config(job["base"], cell, seed, n_rounds, learner)
    backend, cache_file = job.get("backend"), job["cache_file"]
    key = (backend, cache_file, json.dumps(cfg.get("task_pool", {}), sort_keys=True),
           json.dumps(cfg["models"], sort_keys=True),
           json.dumps(cfg.get("backends", {}), sort_keys=True),
           tuple(sorted((s["claimed_model"], s["actual_model"], s["backend"]) for s in cfg["sellers"])))
    if key not in _PREPARED:
        _PREPARED[key] = prepare(cfg, backend, cache_file, log=lambda *a: None)[:3]
    pool, cache, stats = _PREPARED[key]
    backends = build_backends(cfg, {backend} if backend else {s["backend"] for s in cfg["sellers"]}, cache)
    logger = MemoryLog()
    m = run_single(cfg, "posted_price", cell.policy, seed, backends, Reputation(cfg["models"], stats),
                   logger, pool, backend_override=backend)
    tail_rounds = max(1, cfg["run"]["n_rounds"] // 4)
    q = intent(m, logger.records, cfg["run"]["n_rounds"], tail_trade_rounds=tail_rounds)
    tail_from = cfg["run"]["n_rounds"] - tail_rounds
    counts = {sid: 0 for sid in m["strategic_modes"]}
    for rec in logger.records:
        if rec["status"] == "allowed" and rec["seller_id"] in counts and rec["round"] >= tail_from:
            counts[rec["seller_id"]] += 1
    windows, k = quarter_bounds(n_rounds)
    segments = {}
    for name, start, end in windows:
        seg = intent_window(m, logger.records, start, end)
        segments[name] = dict(seg, start=start, end=end)
    q3, q4 = segments["Q3"]["Q"], segments["Q4"]["Q"]
    delta = None if (q3 is None or q4 is None) else (q3 - q4)
    traj = per_round_q(m)
    row = dict(cell.metadata(), seed=seed, **exposure(logger.records), **q,
               q_swap=q["Q_swap"], q_theft=q["Q_theft"], q_downgrade=q["Q_downgrade"],
               accuracy=m["task_accuracy"], cost_per_task=m["mean_cost_per_task_incl_audit"],
               cost=m["total_cost_incl_audit"], audit_cost=m["total_audit_cost"],
               n_audits=m["n_audits"], audit_rate_realised=m["n_audits"] / max(1, m["n_purchases"]),
               fill_rate=m["fill_rate"], n_tasks=cfg["run"]["n_tasks"], n_rounds=cfg["run"]["n_rounds"],
               tail_rounds=tail_rounds, strategic_tail_counts=counts, learner=learner,
               budget_multiplier=cfg["market"]["budget_multiplier"], audit_checks=m["audit_checks"],
               audit_rule=m["audit_rule"],
               config_hash=hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest(),
               wp2_run_id=run_id(cell, learner, n_rounds, seed),
               quarter_k=k,
               Q1=segments["Q1"]["Q"], Q2=segments["Q2"]["Q"], Q3=q3, Q4=q4,
               Q3_minus_Q4=delta,
               Q3_start=segments["Q3"]["start"], Q3_end=segments["Q3"]["end"],
               Q4_start=segments["Q4"]["start"], Q4_end=segments["Q4"]["end"],
               Q3_identifiable_trade=segments["Q3"]["tail_trade"],
               Q4_identifiable_trade=segments["Q4"]["tail_trade"],
               Q3_present_rounds=segments["Q3"]["Q_present_rounds"],
               Q4_present_rounds=segments["Q4"]["Q_present_rounds"])
    if job.get("traj_dir"):
        path = job["traj_dir"] / f"{run_id(cell, learner, n_rounds, seed)}.json"
        with path.open("x", encoding="utf-8") as fh:
            json.dump({
                "wp2_run_id": row["wp2_run_id"], "cell_id": cell.cell_id, "learner": learner,
                "n_rounds": n_rounds, "seed": seed, "q_round": traj,
                "Q1": segments["Q1"], "Q2": segments["Q2"], "Q3": segments["Q3"], "Q4": segments["Q4"],
                "Q3_minus_Q4": delta,
            }, fh)
            fh.write("\n")
    if job.get("log_dir"):
        path = job["log_dir"] / f"{run_id(cell, learner, n_rounds, seed)}.jsonl"
        with path.open("x", encoding="utf-8") as fh:
            for rec in logger.records:
                fh.write(json.dumps(rec) + "\n")
    return row


def summarize(rows):
    groups = {}
    for row in rows:
        key = (row["cell_id"], row["learner"], row["n_rounds"])
        groups.setdefault(key, []).append(row)
    summaries = []
    for (cell_id, learner, n_rounds), runs in groups.items():
        n_tail = sum(bool(r["tail_trade"]) for r in runs)
        q3q4 = [r["Q3_minus_Q4"] for r in runs if r["Q3_minus_Q4"] is not None]
        summary = {k: runs[0][k] for k in (
            "router", "audit", "penalty", "pi", "cell_id", "arm", "policy",
            "trust_feedback", "penalty_label", "audit_efficacy_evidence_allowed",
            "learner", "n_rounds", "n_tasks", "budget_multiplier", "quarter_k")}
        summary.update(n_runs=len(runs), tail_trade_runs=n_tail, tail_trade_rate=n_tail / len(runs),
                       Q_identifiable=n_tail / len(runs) > 0.5,
                       n_delta=len(q3q4),
                       Q3_minus_Q4_mean=(sum(q3q4) / len(q3q4) if q3q4 else None))
        for metric in ("E", "E_tok", "Q", "Q1", "Q2", "Q3", "Q4", "q_swap", "q_theft",
                       "q_downgrade", "accuracy", "cost_per_task"):
            values = [r[metric] for r in runs if r[metric] is not None]
            summary[metric] = sum(values) / len(values) if values else None
        summaries.append(summary)
    return summaries


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=str(ROOT / "configs/v1.0/scale.yaml"))
    ap.add_argument("--out", required=True, help="fresh output directory under results/v1.1/")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seeds", type=int, nargs="+", default=None)
    ap.add_argument("--n-rounds", type=int, nargs="+", default=None)
    ap.add_argument("--learner", nargs="+", default=None)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--cache-file", default=str(ROOT / "cache/llm_outputs.jsonl"))
    ap.add_argument("--log-transactions", action="store_true")
    ap.add_argument("--official", action="store_true",
                    help="require the frozen official grid (seeds 0-19, all three horizons and learners)")
    args = ap.parse_args(argv)
    protocol = ROOT / "docs/v1.1/PROTOCOL_v1.1.md"
    if hashlib.sha256(protocol.read_bytes()).hexdigest() != PROTOCOL_SHA256:
        ap.error("frozen protocol checksum mismatch")
    if args.jobs < 1:
        ap.error("--jobs must be positive")
    seeds = args.seeds if args.seeds is not None else list(range(N_SEEDS))
    n_rounds_list = tuple(args.n_rounds) if args.n_rounds is not None else WP2_ROUNDS
    learners = tuple(args.learner) if args.learner is not None else WP2_LEARNERS
    if not seeds or len(seeds) != len(set(seeds)) or any(s < 0 for s in seeds):
        ap.error("seeds must be distinct nonnegative integers")
    if any(n not in WP2_ROUNDS for n in n_rounds_list):
        ap.error("n_rounds must be a subset of {48, 200, 500}")
    if any(l not in WP2_LEARNERS for l in learners):
        ap.error("learner must be a subset of egreedy, fictitious_play, exp3")
    official = (seeds == list(range(N_SEEDS)) and tuple(n_rounds_list) == WP2_ROUNDS
                and tuple(learners) == WP2_LEARNERS)
    if args.official and not official:
        ap.error("official WP2 is fixed: seeds 0-19, rounds 48/200/500, all three learners, three router cells")
    try:
        out = output_path(args.out)
    except ValueError as exc:
        ap.error(str(exc))
    if out.exists() and any(out.iterdir()):
        ap.error("output directory must be fresh/empty; refusing to overwrite results")
    base = load_config(args.config)
    # Verify pairing on every horizon before writing anything else.
    pairing = {}
    for n_rounds in n_rounds_list:
        cfg = cell_config(base, WP2_CELLS[0], seeds[0], n_rounds, learners[0])
        if cfg["run"]["n_tasks"] != 10 * n_rounds:
            ap.error(f"n_tasks was not paired to 10*n_rounds at n_rounds={n_rounds}")
        pairing[str(n_rounds)] = {
            "n_rounds": n_rounds, "n_tasks": cfg["run"]["n_tasks"],
            "budget_multiplier": cfg["market"]["budget_multiplier"],
            "budget_multiplier_at_480": cfg["market"]["budget_multiplier_at_480"],
        }
    jobs_meta = [{"cell_id": c.cell_id, "router": c.router, "audit": c.audit,
                  "penalty": c.penalty, "pi": c.pi, "learner": learner, "n_rounds": n,
                  "n_tasks": pairing[str(n)]["n_tasks"],
                  "budget_multiplier": pairing[str(n)]["budget_multiplier"]}
                 for c in WP2_CELLS for learner in learners for n in n_rounds_list]
    out.mkdir(parents=True, exist_ok=True)
    meta = {
        "mode": "wp2", "official": official, "dry_run": args.dry_run,
        "protocol_sha256": PROTOCOL_SHA256,
        "git_head": subprocess.check_output(
            ["git", "--no-pager", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "config": str(Path(args.config).resolve()),
        "seeds": seeds, "n_rounds": list(n_rounds_list), "learners": list(learners),
        "cells": [c.metadata() for c in WP2_CELLS],
        "pairing": pairing,
        "n_run_groups": len(jobs_meta),
        "n_runs_planned": len(jobs_meta) * len(seeds),
        "argv": list(argv) if argv is not None else sys.argv[1:],
        "cell_choice": (
            "PROTOCOL §2 names routers PILOT, strongest, and cascade + a=0.1 at π=1. "
            "Official WP2 uses the frozen WP1 cells pilot/strongest/cascade at a=0.1, P=0.25, π=1, "
            "trust_feedback=false (not cascade+trust). Horizon pairing is scale_horizon only."
        ),
        "inference": "plain means only; Q3-Q4 bootstrap, recommended n_rounds, and Decision A remain Experiment's responsibility",
    }
    write_json(out / "run_meta.json", meta)
    write_json(out / "manifest.json", jobs_meta)
    if args.dry_run:
        print(json.dumps({"official": official, "n_run_groups": meta["n_run_groups"],
                          "n_runs_planned": meta["n_runs_planned"], "pairing": pairing}))
        return
    traj_dir = out / "trajectories"
    traj_dir.mkdir()
    log_dir = out / "transactions" if args.log_transactions else None
    if log_dir:
        log_dir.mkdir()
    jobs = [{"base": base, "cell": cell, "seed": seed, "n_rounds": n_rounds,
             "learner": learner, "backend": None, "cache_file": args.cache_file,
             "traj_dir": traj_dir, "log_dir": log_dir}
            for cell in WP2_CELLS for learner in learners for n_rounds in n_rounds_list
            for seed in seeds]
    start = time.monotonic()
    rows = []

    def collect(results):
        with (out / "completed_runs.jsonl").open("x", encoding="utf-8") as fh:
            for row in results:
                rows.append(row)
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                print(f"completed {len(rows)}/{len(jobs)} {row['wp2_run_id']}", flush=True)

    if args.jobs > 1:
        with Pool(args.jobs) as pool:
            collect(pool.imap(run_wp2_cell, jobs, chunksize=1))
    else:
        collect(map(run_wp2_cell, jobs))
    write_csv(out / "per_seed.csv", rows)
    write_json(out / "cells.json", summarize(rows))
    write_json(out / "completion.json", {"n_runs_completed": len(rows), "elapsed_s": time.monotonic() - start})


if __name__ == "__main__":
    main()
