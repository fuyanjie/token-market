#!/usr/bin/env python3
"""Enumerate or run frozen WP1; see docs/v1.1/WP1_RUNNER.md."""
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
from tokenmarket import decision_a  # noqa: E402
from tokenmarket.wp1 import (PROTOCOL_SHA256, cell_config, enumerate_wp1, run_cell,  # noqa: E402
                             summarize_cells)


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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--config", default=str(ROOT / "configs/v1.0/scale.yaml"))
    ap.add_argument("--out", required=True, help="fresh output directory under results/v1.1/")
    ap.add_argument("--dry-run", action="store_true", help="write complete plan, execute no simulation")
    ap.add_argument("--mode", choices=("wp1", "followup", "smoke", "decision_a"), default="wp1")
    ap.add_argument("--seeds", type=int, nargs="+", default=None)
    ap.add_argument("--n-rounds", type=int, default=None, help="tasks and budgets are paired automatically")
    ap.add_argument("--learner", choices=("egreedy", "fictitious_play", "exp3"), default="egreedy")
    ap.add_argument("--cell", action="append", default=[], help="exact cell id; smoke/followup only")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--backend-override", choices=("mock",), default=None, help="smoke only")
    ap.add_argument("--cache-file", default=str(ROOT / "cache/llm_outputs.jsonl"))
    ap.add_argument("--log-transactions", action="store_true")
    ap.add_argument("--protocol", default=str(ROOT / "docs/v1.1/PROTOCOL_v1.1.md"))
    ap.add_argument("--protocol-sha256", default=PROTOCOL_SHA256,
                    help="expected SHA256 of the frozen protocol")
    args = ap.parse_args(argv)
    supplied = list(argv) if argv is not None else sys.argv[1:]
    has = lambda flag: any(a == flag or a.startswith(flag + "=") for a in supplied)
    official_a = args.mode == "decision_a"
    if official_a:
        if not has("--protocol") or not has("--protocol-sha256"):
            ap.error("Decision A requires explicit --protocol and --protocol-sha256 pins")
        if (Path(args.protocol).resolve() != ROOT / "docs/v1.1/PROTOCOL_v1.2.md"
                or args.protocol_sha256 != decision_a.PROTOCOL_SHA256):
            ap.error("Decision A requires the frozen PROTOCOL_v1.2 path and checksum")
        if (args.n_rounds not in (None, 1000) or has("--learner") or args.cell
                or args.backend_override
                or (args.seeds is not None and args.seeds != list(range(20)))):
            ap.error("Decision A is fixed: 1000 rounds, all learners, 48 cells, seeds 0..19, native backends")
        if Path(args.config).resolve() != ROOT / "configs/v1.0/scale.yaml":
            ap.error("Decision A requires the frozen scale configuration")
    protocol = Path(args.protocol).resolve()
    if not protocol.is_file() or hashlib.sha256(protocol.read_bytes()).hexdigest() != args.protocol_sha256:
        ap.error("frozen protocol checksum mismatch")
    if args.jobs < 1:
        ap.error("--jobs must be positive")
    n_rounds = args.n_rounds if args.n_rounds is not None else (
        1000 if official_a else (4 if args.mode == "smoke" else 48))
    learners = decision_a.LEARNERS if official_a else (args.learner,)
    seeds = args.seeds if args.seeds is not None else ([0] if args.mode == "smoke" else list(range(20)))
    if not seeds or len(seeds) != len(set(seeds)) or any(s < 0 for s in seeds):
        ap.error("seeds must be distinct nonnegative integers")
    if args.mode == "wp1" and (n_rounds != 48 or args.learner != "egreedy"
                              or seeds != list(range(20)) or args.cell or args.backend_override):
        ap.error("official WP1 is fixed: complete grid, seeds 0..19, 48 rounds, egreedy, native backends")
    if args.mode == "smoke":
        if len(seeds) != 1 or not 1 <= n_rounds <= 4 or not 1 <= len(args.cell) <= 2:
            ap.error("smoke requires one seed, one or two explicit cells, and at most four rounds")
    if args.mode == "followup":
        if n_rounds not in (48, 200, 500):
            ap.error("followup rounds must be 48, 200 or 500")
        if args.backend_override:
            ap.error("--backend-override is smoke-only")
    cells = decision_a.cells() if official_a else enumerate_wp1()
    if args.cell:
        known = {c.cell_id: c for c in cells}
        if len(args.cell) != len(set(args.cell)) or any(c not in known for c in args.cell):
            ap.error("--cell must name distinct cells from the manifest")
        cells = [known[c] for c in args.cell]
    try:
        out = decision_a.fresh_output(ROOT, args.out) if official_a else output_path(args.out)
    except ValueError as exc:
        ap.error(str(exc))
    if out.exists() and any(out.iterdir()):
        ap.error("output directory must be fresh/empty; refusing to overwrite results")
    base = load_config(args.config)
    first = cell_config(base, cells[0], seeds[0], n_rounds, args.learner)
    if official_a and first["market"]["budget_multiplier"] != decision_a.BUDGET_MULTIPLIER:
        ap.error("Decision A budget pairing mismatch")
    out.mkdir(parents=True, exist_ok=True)
    for arm in ("factorial", "control"):
        (out / arm).mkdir(exist_ok=True)
    meta = {
        "mode": args.mode, "dry_run": args.dry_run, "protocol_sha256": args.protocol_sha256,
        "git_head": subprocess.check_output(
            ["git", "--no-pager", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "config": str(Path(args.config).resolve()), "base_config": base,
        "seeds": seeds, "n_rounds": n_rounds, "n_tasks": first["run"]["n_tasks"],
        "budget_multiplier": first["market"]["budget_multiplier"], "learner": args.learner,
        "backend_override": args.backend_override, "cache_file": str(Path(args.cache_file).resolve()),
        "n_cells": len(cells), "n_factorial_cells": sum(c.arm == "factorial" for c in cells),
        "n_control_cells": sum(c.arm == "control" for c in cells), "n_runs_planned": len(cells) * len(seeds),
        "argv": list(argv) if argv is not None else sys.argv[1:],
        "inference": "plain means only; paired bootstrap and Holm remain Experiment's responsibility",
    }
    if protocol != ROOT / "docs/v1.1/PROTOCOL_v1.1.md":
        meta["protocol_path"] = str(protocol)
    if official_a:
        meta.update(learner="all", learners=list(learners),
                    n_runs_planned=len(cells) * len(seeds) * len(learners))
    write_json(out / "run_meta.json", meta)
    write_json(out / "manifest.json", [c.metadata() for c in cells])
    if args.dry_run:
        print(json.dumps({k: meta[k] for k in ("n_cells", "n_factorial_cells", "n_control_cells",
                                              "n_runs_planned", "n_rounds", "n_tasks", "budget_multiplier")}))
        return
    log_dir = out / "transactions" if args.log_transactions else None
    if log_dir:
        log_dir.mkdir()
        if official_a:
            for learner in learners:
                (log_dir / learner).mkdir()
    jobs = [{"base": base, "cell": cell, "seed": seed, "n_rounds": n_rounds,
             "learner": learner, "backend": args.backend_override,
             "cache_file": args.cache_file, "log_dir": log_dir}
            for cell in cells for learner in learners for seed in seeds]
    worker = decision_a.run_job if official_a else run_cell
    start = time.monotonic()
    rows = []
    # Append completed rows as they arrive, preserving evidence if a later cell fails.
    def collect(results):
        with (out / "completed_runs.jsonl").open("x", encoding="utf-8") as fh:
            for row in results:
                rows.append(row)
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                print(f"completed {len(rows)}/{len(jobs)} {row['cell_id']} seed={row['seed']}", flush=True)
    if args.jobs > 1:
        with Pool(args.jobs) as pool:
            collect(pool.imap(worker, jobs, chunksize=1))
    else:
        collect(map(worker, jobs))
    for arm in ("factorial", "control"):
        arm_rows = [r for r in rows if r["arm"] == arm]
        write_csv(out / arm / "per_seed.csv", arm_rows)
        write_json(out / arm / "cells.json",
                   decision_a.summarize(arm_rows) if official_a else summarize_cells(arm_rows))
    write_json(out / "completion.json", {"n_runs_completed": len(rows), "elapsed_s": time.monotonic() - start})


if __name__ == "__main__":
    main()
