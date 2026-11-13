#!/usr/bin/env python3
"""Read-only WP2 validation and PROTOCOL_v1.1 §2 paired convergence analysis.

Run with /workspace/tmvenv/bin/python scripts/v1.1/analyze_wp2.py.
Use --include-r1000 to combine wp2/ and wp2_r1000/ into wp2_eval_r1000/.
Never runs the simulation.
"""
from __future__ import annotations

from collections import defaultdict
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tokenmarket.config import load_config  # noqa: E402
from tokenmarket.wp1 import PROTOCOL_SHA256, Cell, cell_config  # noqa: E402

B = 10_000
RNG_SEED = 20261111
MARGIN = 0.05
ROUTERS = ("pilot", "strongest", "cascade")
LEARNERS = ("egreedy", "fictitious_play", "exp3")
HORIZONS = (48, 200, 500)
SEEDS = tuple(range(20))
OUT = ROOT / "results/v1.1/wp2_eval"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def paired_bootstrap(differences, key):
    """Resample seed-level Q3-Q4 differences, not quarters independently."""
    values = np.asarray(differences, dtype=float)
    require(values.shape == (20,) and np.isfinite(values).all(),
            f"{key}: need all 20 finite paired seed differences")
    digest = hashlib.sha256(f"{RNG_SEED}:{key}".encode()).digest()
    rng = np.random.default_rng(int.from_bytes(digest[:8], "little"))
    draws = values[rng.integers(0, len(values), size=(B, len(values)))].mean(axis=1)
    lo, hi = np.percentile(draws, [2.5, 97.5])
    p = min(1.0, 2 * min(float(np.mean(draws <= 0)), float(np.mean(draws >= 0))))
    return {"mean": float(values.mean()), "lo": float(lo), "hi": float(hi),
            "p_two_sided_descriptive": p}


def inside_margin(lo, hi):
    return -MARGIN <= lo <= hi <= MARGIN


def validate_inputs(run=None, horizons=HORIZONS, protocol=None,
                    protocol_sha256=PROTOCOL_SHA256, wp1_run=None):
    """Fail closed before writing any analysis if the frozen run is inconsistent."""
    run = Path(run) if run is not None else ROOT / "results/v1.1/wp2"
    n_groups = len(ROUTERS) * len(LEARNERS) * len(horizons)
    n_runs = n_groups * len(SEEDS)
    protocol = Path(protocol) if protocol is not None else ROOT / "docs/v1.1/PROTOCOL_v1.1.md"
    wp1_run = Path(wp1_run) if wp1_run is not None else ROOT / "results/v1.1/wp1"
    require(sha256(protocol) == protocol_sha256, "frozen protocol checksum mismatch")
    meta = read_json(run / "run_meta.json")
    completion = read_json(run / "completion.json")
    require(meta["official"] and not meta["dry_run"], "not an official WP2 run")
    require(meta["protocol_sha256"] == protocol_sha256, "run protocol mismatch")
    require(meta["seeds"] == list(SEEDS) and meta["learners"] == list(LEARNERS)
            and meta["n_rounds"] == list(horizons), "metadata grid mismatch")
    require(meta["n_run_groups"] == n_groups and meta["n_runs_planned"] == n_runs
            and completion["n_runs_completed"] == n_runs, "completion count mismatch")
    rows = [json.loads(line) for line in (run / "completed_runs.jsonl").read_text().splitlines()]
    require(len(rows) == n_runs, f"need {n_runs} runs")
    expected = set(itertools.product(ROUTERS, LEARNERS, horizons, SEEDS))
    actual = {(r["router"], r["learner"], r["n_rounds"], r["seed"]) for r in rows}
    require(actual == expected, "missing, duplicate, or unexpected run")
    csv_rows = list(csv.DictReader((run / "per_seed.csv").open()))
    require(len(csv_rows) == n_runs, "CSV count mismatch")
    require(len({r["wp2_run_id"] for r in csv_rows}) == n_runs, "duplicate CSV run")
    csv_by_id = {r["wp2_run_id"]: r for r in csv_rows}
    wp1 = [json.loads(line) for line in
           (wp1_run / "completed_runs.jsonl").read_text().splitlines()]
    wp1_index = {(r["cell_id"], r["seed"]): r for r in wp1}
    base = load_config(str(ROOT / "configs/v1.0/scale.yaml"))
    groups = defaultdict(list)
    matched = 0
    input_paths = [protocol, ROOT / "scripts/v1.1/run_wp2.py",
                   ROOT / "tokenmarket/wp1.py", ROOT / "tokenmarket/v1_metrics.py",
                   ROOT / "tokenmarket/audit_v1.py",
                   wp1_run / "completed_runs.jsonl"]
    input_paths += [run / name for name in (
        "run_meta.json", "completion.json", "manifest.json",
        "completed_runs.jsonl", "per_seed.csv", "cells.json")]
    for row in rows:
        key = (row["router"], row["learner"], row["n_rounds"])
        groups[key].append(row)
        cell = Cell(row["router"], "a0.1", 0.25, 1.0)
        require(all(row[k] == v for k, v in cell.metadata().items()),
                f"{key}: cell settings mismatch")
        n = row["n_rounds"]
        cfg = cell_config(base, cell, row["seed"], n, row["learner"])
        cfg_hash = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
        require(row["config_hash"] == cfg_hash, f"{key}: config hash mismatch")
        require(row["n_tasks"] == 10 * n and row["budget_multiplier"] ==
                base["market"]["budget_multiplier"] * (10 * n) / 480,
                f"{key}: task/budget scaling mismatch")
        require(row["audit_checks"] == ["identity", "length"]
                and row["audit_rule"] == "fixed", f"{key}: audit mismatch")
        k = max(1, int(n * 0.25))
        require((row["Q3_start"], row["Q3_end"], row["Q4_start"], row["Q4_end"]) ==
                (n - 2 * k, n - k, n - k, n), f"{key}: quarter bounds mismatch")
        require(row["quarter_k"] == row["tail_rounds"] == k, f"{key}: quarter size mismatch")
        require(row["Q4"] == row["Q"] and row["Q3_minus_Q4"] == row["Q3"] - row["Q4"],
                f"{key}: Q4/Q or paired difference mismatch")
        require(row["Q4_identifiable_trade"] == row["tail_trade"],
                f"{key}: tail trade mismatch")
        require(bool(row["tail_sales"]) == row["tail_trade"]
                and sum(row["strategic_tail_counts"].values()) == row["tail_sales"],
                f"{key}: tail sale counts mismatch")
        for field, value in row.items():
            serial = json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
            if value is None:
                serial = ""
            require(csv_by_id[row["wp2_run_id"]][field] == serial,
                    f"{key}: CSV differs from JSONL at {field}")
        trajectory_path = run / "trajectories" / f"{row['wp2_run_id']}.json"
        trajectory = read_json(trajectory_path)
        input_paths.append(trajectory_path)
        require(trajectory["wp2_run_id"] == row["wp2_run_id"]
                and len(trajectory["q_round"]) == n, f"{key}: trajectory identity/length mismatch")
        for quarter in ("Q3", "Q4"):
            segment = trajectory[quarter]
            require(segment["Q"] == row[quarter]
                    and segment["start"] == row[f"{quarter}_start"]
                    and segment["end"] == row[f"{quarter}_end"]
                    and segment["tail_trade"] == row[f"{quarter}_identifiable_trade"]
                    and segment["Q_present_rounds"] == row[f"{quarter}_present_rounds"],
                    f"{key}: trajectory segment mismatch")
        require(trajectory["Q3_minus_Q4"] == row["Q3_minus_Q4"],
                f"{key}: trajectory difference mismatch")
        if row["learner"] == "egreedy" and n == 48:
            old = wp1_index[row["cell_id"], row["seed"]]
            require(all(row[field] == value for field, value in old.items()),
                    f"{key}: WP1 shared fields mismatch")
            matched += 1
    require(matched == (60 if 48 in horizons else 0), "WP1 matching row count mismatch")
    summaries = read_json(run / "cells.json")
    require(len(summaries) == n_groups, f"need {n_groups} group summaries")
    require({(s["router"], s["learner"], s["n_rounds"]) for s in summaries} ==
            set(itertools.product(ROUTERS, LEARNERS, horizons)), "summary grid mismatch")
    for summary in summaries:
        rs = groups[summary["router"], summary["learner"], summary["n_rounds"]]
        tails = sum(r["tail_trade"] for r in rs)
        require(summary["n_runs"] == 20 and summary["tail_trade_runs"] == tails
                and summary["Q_identifiable"] == (tails > 10), "group tail counts mismatch")
        for metric in ("E", "Q", "Q3", "Q4"):
            mean = sum(r[metric] for r in rs) / 20
            require(abs(summary[metric] - mean) < 1e-14, "group mean mismatch")
    expected_manifest = {(Cell(router, "a0.1", 0.25, 1.0).cell_id, learner, n)
                         for router, learner, n in itertools.product(ROUTERS, LEARNERS, horizons)}
    manifest = read_json(run / "manifest.json")
    require(len(manifest) == n_groups and
            {(m["cell_id"], m["learner"], m["n_rounds"]) for m in manifest} == expected_manifest,
            "manifest mismatch")
    checks = {"runs": n_runs, "groups": n_groups, "seeds_per_group": 20,
              "Q4_equals_official_Q_exactly": n_runs, "WP1_R48_shared_field_matches": matched,
              "config_hashes_recomputed": n_runs, "trajectories_checked": n_runs,
              "csv_jsonl_equal": True, "summaries_equal": True}
    hashes = {str(p.relative_to(ROOT)): sha256(p) for p in sorted(input_paths)}
    return groups, checks, hashes


def analyze(groups, horizons=HORIZONS):
    results = []
    for router, learner, n in itertools.product(ROUTERS, LEARNERS, horizons):
        rows = sorted(groups[router, learner, n], key=lambda r: r["seed"])
        require([r["seed"] for r in rows] == list(SEEDS), "invalid seed pairing")
        differences = [r["Q3"] - r["Q4"] for r in rows]
        bootstrap = paired_bootstrap(differences, f"{router}:{learner}:R{n}")
        tails = sum(r["tail_trade"] for r in rows)
        identifiable = tails / len(rows) > 0.5
        within = inside_margin(bootstrap["lo"], bootstrap["hi"])
        results.append({
            "router": router, "learner": learner, "n_rounds": n, "n_tasks": 10 * n,
            "n_runs": len(rows), "tail_trade_runs": tails, "tail_trade_share": tails / len(rows),
            "Q_identifiable": identifiable,
            **{metric + "_mean": float(np.mean([r[metric] for r in rows]))
               for metric in ("E", "Q", "Q3", "Q4")},
            "difference": bootstrap, "CI_inside_margin": within,
            "converged": within and identifiable,
            "seed_differences": [{"seed": r["seed"], "difference": d}
                                 for r, d in zip(rows, differences)],
        })
    lookup = {(r["router"], r["learner"], r["n_rounds"]): r for r in results}
    qualifying = [n for n in horizons if all(lookup[router, learner, n]["converged"]
                  for router in ("pilot", "strongest") for learner in LEARNERS)]
    recommended = min(qualifying) if qualifying else None
    exp3_at_500 = all(lookup[router, "exp3", 500]["converged"] for router in ("pilot", "strongest"))
    return results, recommended, exp3_at_500


def result_table(results):
    lines = [
        "| router | learner | rounds | E | Q | Q3 | Q4 | tail runs | Q id. | mean Q3−Q4 [95% CI] | converged |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for r in results:
        d = r["difference"]
        lines.append(
            f"| {r['router']} | {r['learner']} | {r['n_rounds']} | "
            f"{r['E_mean']:.6f} | {r['Q_mean']:.6f} | {r['Q3_mean']:.6f} | {r['Q4_mean']:.6f} | "
            f"{r['tail_trade_runs']}/20 | {'yes' if r['Q_identifiable'] else 'no'} | "
            f"{d['mean']:.6f} [{d['lo']:.6f}, {d['hi']:.6f}] | "
            f"{'yes' if r['converged'] else 'no'} |")
    return "\n".join(lines)


def combined_inputs(run, r1000_run, **validation):
    groups, checks, hashes = validate_inputs(run, **validation)
    extra, extra_checks, extra_hashes = validate_inputs(r1000_run, (1000,), **validation)
    require(not groups.keys() & extra.keys(), "overlapping input tiers")
    groups.update(extra)
    for key in ("runs", "groups", "Q4_equals_official_Q_exactly",
                "WP1_R48_shared_field_matches", "config_hashes_recomputed", "trajectories_checked"):
        checks[key] += extra_checks[key]
    hashes.update(extra_hashes)
    return groups, checks, hashes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--include-r1000", action="store_true")
    ap.add_argument("--run", type=Path, default=ROOT / "results/v1.1/wp2")
    ap.add_argument("--r1000-run", type=Path, default=ROOT / "results/v1.1/wp2_r1000")
    ap.add_argument("--wp1-run", type=Path, default=ROOT / "results/v1.1/wp1")
    ap.add_argument("--protocol", type=Path, default=ROOT / "docs/v1.1/PROTOCOL_v1.1.md")
    ap.add_argument("--protocol-sha256", default=PROTOCOL_SHA256)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    out = (args.out if args.out is not None else
           (ROOT / "results/v1.1/wp2_eval_r1000" if args.include_r1000 else OUT)).resolve()
    require(out.is_relative_to((ROOT / "results/v1.1").resolve()),
            "all outputs must be under results/v1.1/")
    if args.include_r1000 or args.out is not None:
        require(not out.exists() or not any(out.iterdir()), "output must be fresh/empty")
        protected = [args.run.resolve(), args.r1000_run.resolve(), args.wp1_run.resolve(), OUT.resolve(),
                     (ROOT / "results/v1.0").resolve(), (ROOT / "release").resolve(),
                     *(p.resolve() for p in (ROOT / "results/v1.1").glob("wp1*"))]
        require(not any(out.is_relative_to(p) for p in protected), "protected output directory")
    validation = {"protocol": args.protocol, "protocol_sha256": args.protocol_sha256,
                  "wp1_run": args.wp1_run}
    if args.include_r1000:
        groups, checks, input_hashes = combined_inputs(args.run, args.r1000_run, **validation)
    else:
        groups, checks, input_hashes = validate_inputs(args.run, **validation)
    horizons = (*HORIZONS, 1000) if args.include_r1000 else HORIZONS
    results, recommended, exp3_at_500 = analyze(groups, horizons)
    stop_cells = [f"{r['router']} × {r['learner']}" for r in results
                  if r["n_rounds"] == 1000 and r["router"] in ("pilot", "strongest")
                  and r["learner"] in ("egreedy", "fictitious_play") and not r["converged"]]
    stop = bool(stop_cells)
    recommendation = (f"Recommended n_rounds: **{recommended}**."
                      if recommended is not None else
                      "**No recommended n_rounds:** no tested horizon satisfies all three learners "
                      "on both PILOT and strongest.")
    exp3_note = (
        "EXP3 converges on both decision routers at 500 rounds; the §1.3 nonconvergence "
        "exclusion is not triggered at that horizon."
        if exp3_at_500 else
        "EXP3 does not converge on both decision routers even at 500 rounds. Per §1.3, "
        "report EXP3 but do not count it toward direction consistency; Decision A then "
        "requires both egreedy and fictitious_play to satisfy the significant same-direction "
        "criterion, with no eligible significant opposite direction. This exception does not "
        "relax §2's three-learner horizon recommendation rule."
    )
    payload = {
        "protocol_sha256": args.protocol_sha256, "B": B, "rng_seed": RNG_SEED,
        "bootstrap": "same-seed Q3-Q4 differences; 10000 seed resamples; 95% percentile CI",
        "rng_key": "sha256 of 20261111:<router>:<learner>:R<n>; first 8 bytes little endian",
        "equivalence_margin": [-MARGIN, MARGIN],
        "convergence": "whole CI inside inclusive [-0.05, 0.05] and Q identifiable",
        "identifiability": "last-quarter strategic-tail-trade run share > 0.5",
        "p_values": "descriptive two-sided bootstrap sign-tail values; no significance decision or Holm",
        "recommended_n_rounds": recommended,
        "EXP3_converged_both_decision_routers_at_500": exp3_at_500,
        "decision_A_note": exp3_note, "checks": checks, "input_sha256": input_hashes,
        "analysis_script_sha256": sha256(Path(__file__)),
        "groups": results,
    }
    if args.include_r1000:
        payload["stop_and_ask"] = stop
        payload["stop_cells"] = stop_cells
        payload["r1000_note"] = (
            f"STOP and ask: {', '.join(stop_cells)} still fails at 1000. No automatic re-voting."
            if stop else "All egreedy/fictitious_play decision cells pass at 1000; no automatic protocol changes.")
    lines = [
        "# Cross-Border v1.1 WP2 convergence analysis", "",
        recommendation, "", exp3_note, "",
        "## Method", "",
        "All cells use a=0.1, P=0.25, pi=1, trust_feedback=false; 20 seeds (0–19). "
        "Per seed d=Q3−Q4. Resample the 20 paired differences B=10000 times; report the "
        "2.5/97.5 percentiles of mean d. A CI must lie wholly inside the inclusive "
        "[−0.05, 0.05] bounds; containing zero alone is insufficient. Deterministic RNG: "
        "base 20261111, group-specific SHA256 seed (see JSON). All 20 differences are retained; "
        "missing/nonfinite pairs abort rather than silently reduce the sample.", "",
        "Q identifiability uses the final-quarter trade share >50%; unidentifiable cells "
        "are descriptive only and cannot pass convergence. Cascade never selects the "
        "recommended horizon: only PILOT and strongest, all three learners, determine it. "
        "Two-sided bootstrap p values in JSON are descriptive only; convergence uses no "
        "null-significance test, Holm adjustment, or test against zero.", "",
        "The 80-task pool is reused: 200/500 rounds repeat each task about 25/62 times "
        "(62.5 on average at 500); effective task diversity remains 80. These results are "
        "horizon diagnostics, not the audit-grid Decision-A experiment.", "",
        "## All groups", "", result_table(results), "",
        "## Validation", "", json.dumps(checks, indent=2), "",
        f"All input SHA256 values (including {checks['trajectories_checked']} trajectories) are recorded in wp2_eval.json. "
        f"Q4 equals official Q exactly for {checks['runs']}/{checks['runs']} runs; the 60 egreedy R48 runs match "
        "every WP1 shared field. Configuration hashes are independently reconstructed "
        "with frozen cell_config/scale_horizon. No raw runs were modified.", "",
    ]
    if args.include_r1000:
        lines[0] = "# Cross-Border WP2 convergence analysis — 1000-round extension"
        lines[5:5] = [payload["r1000_note"], ""]
        lines = [line.replace(
            "200/500 rounds repeat each task about 25/62 times (62.5 on average at 500)",
            "200/500/1000 rounds repeat each task 25/62.5/125 times on average")
                 for line in lines]
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "wp2_eval.json"
    md_path = out / "wp2_eval.md"
    json_path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    md_path.write_text("\n".join(lines))
    for path in (json_path, md_path):
        digest = sha256(path)
        path.with_suffix(path.suffix + ".sha256").write_text(f"{digest}  {path.name}\n")
        print(f"{digest}  {path.relative_to(ROOT)}")
    print(recommendation)
    print(exp3_note)
    if args.include_r1000:
        print(payload["r1000_note"])


if __name__ == "__main__":
    main()
