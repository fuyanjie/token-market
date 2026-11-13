#!/usr/bin/env python3
"""Analyze a completed frozen Decision A grid, writing only to an explicit fresh output."""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tokenmarket import decision_a as design  # noqa: E402
from tokenmarket.config import load_config  # noqa: E402
from tokenmarket.wp1 import cell_config  # noqa: E402

# Import definitions only: never invoke the legacy analyzer's main().
_spec = importlib.util.spec_from_file_location("wp1_statistics", Path(__file__).with_name("analyze_wp1.py"))
stats = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stats)

METRICS = ("E", "E_tok", "Q", "q_swap", "q_theft", "q_downgrade", "accuracy", "cost_per_task")
WP2_PATH = ROOT / "results/v1.1/v1.2_wp2_eval_r1000/wp2_eval.json"
DECISION_FAMILY = "decisionA::pilot+strongest::all_learners::P0.25::pi1"


def read_json(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def wp2_fact():
    """Read the official decision fact, without recomputing/reopening WP2 inference."""
    fact = read_json(WP2_PATH)
    require(fact["protocol_sha256"] == design.PROTOCOL_SHA256
            and fact["recommended_n_rounds"] == 1000
            and not fact.get("stop_and_ask", False)
            and fact["EXP3_converged_both_decision_routers_at_500"] is True,
            "official WP2 decision fact mismatch; stop and ask")
    return {
        "path": str(WP2_PATH), "sha256": digest(WP2_PATH),
        "recommended_n_rounds": 1000, "stop_and_ask": False,
        "EXP3_included_in_direction_consistency": True,
        "decision_A_note": fact["decision_A_note"],
        "voting_learners": list(design.LEARNERS),
    }


def validate_inputs(run, protocol, protocol_sha256):
    require(protocol.resolve() == (ROOT / "docs/v1.1/PROTOCOL_v1.2.md").resolve()
            and digest(protocol) == protocol_sha256 == design.PROTOCOL_SHA256,
            "frozen protocol mismatch")
    meta = read_json(run / "run_meta.json")
    require(meta.get("mode") == "decision_a" and meta.get("dry_run") is False,
            "not a completed official Decision A run")
    expected_meta = {
        "protocol_sha256": design.PROTOCOL_SHA256, "n_rounds": 1000, "n_tasks": 10000,
        "budget_multiplier": design.BUDGET_MULTIPLIER, "seeds": list(range(20)),
        "learners": list(design.LEARNERS), "learner": "all", "backend_override": None,
        "n_cells": 48, "n_factorial_cells": 48, "n_control_cells": 0, "n_runs_planned": 2880,
    }
    require(all(meta.get(k) == v for k, v in expected_meta.items()), "run metadata mismatch")
    require(read_json(run / "completion.json")["n_runs_completed"] == 2880,
            "incomplete Decision A run")
    expected_cells = design.cells()
    require(read_json(run / "manifest.json") == [c.metadata() for c in expected_cells],
            "manifest grid mismatch")
    base = load_config(str(ROOT / "configs/v1.0/scale.yaml"))
    require(meta["base_config"] == json.loads(json.dumps(base)), "nonfrozen base configuration")
    rows = [json.loads(line) for line in (run / "completed_runs.jsonl").read_text().splitlines()]
    expected = set(itertools.product(
        [c.cell_id for c in expected_cells], design.LEARNERS, range(20)))
    keys = [(r["cell_id"], r["learner"], r["seed"]) for r in rows]
    require(len(keys) == 2880 and len(set(keys)) == 2880 and set(keys) == expected,
            "complete 48 x 3 x 20 grid required (no duplicates)")
    lookup = {c.cell_id: c for c in expected_cells}
    for row in rows:
        cell = lookup[row["cell_id"]]
        require(all(row[k] == v for k, v in cell.metadata().items()), "cell metadata mismatch")
        require(row["n_rounds"] == 1000 and row["n_tasks"] == 10000
                and row["budget_multiplier"] == design.BUDGET_MULTIPLIER
                and row["tail_rounds"] == 250, "row horizon/budget mismatch")
        require(type(row["tail_trade"]) is bool, "tail_trade must be boolean")
        require(row["audit_checks"] == ["identity", "length"]
                and row["audit_rule"] == ("risk_adaptive" if cell.audit == "risk_adaptive" else "fixed"),
                "row audit settings mismatch")
        require(all(isinstance(row[k], (float, int)) and np.isfinite(row[k]) for k in METRICS),
                "nonfinite metric")
        cfg = cell_config(base, cell, row["seed"], 1000, row["learner"])
        config_hash = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
        require(row["config_hash"] == config_hash, "row configuration hash mismatch")
    # Require exact agreement between runner artifacts, not merely plausible counts.
    with (run / "factorial/per_seed.csv").open(newline="") as fh:
        csv_rows = list(csv.DictReader(fh))
    serialized = [
        {k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list))
         else ("" if v is None else str(v))
         for k, v in r.items()} for r in rows]
    require(csv_rows == serialized, "CSV/JSONL mismatch")
    require(read_json(run / "factorial/cells.json") == design.summarize(rows),
            "learner-specific summary mismatch")
    paths = ("run_meta.json", "manifest.json", "completed_runs.jsonl", "completion.json",
             "factorial/per_seed.csv", "factorial/cells.json")
    hashes = {str(run / name): digest(run / name) for name in paths}
    hashes[str(protocol)] = digest(protocol)
    return rows, meta, hashes


def astar(audit, penalty, realised):
    rel = stats.a_vs_astar(audit, penalty, realised)
    return dict(relation=rel[0], a_source=rel[1], a_star_lo=rel[2],
                a_star_hi=rel[3], a_used=rel[4])


def estimate(values, key):
    mean, lo, hi, p = stats.boot_mean_ci(values, stats.contrast_rng(key))
    return dict(mean=mean, lo=lo, hi=hi, p=p)


def direction_vote(contrasts, significance):
    """All three rules vote; an identifiable significant opposite effect vetoes."""
    require({c["learner"] for c in contrasts} == set(design.LEARNERS)
            and len(contrasts) == 3, "direction vote requires all three learners")
    down = [c["learner"] for c in contrasts
            if c["testable"] and c.get(significance) and c["delta_mean"] < 0]
    up = [c["learner"] for c in contrasts
          if c["testable"] and c.get(significance) and c["delta_mean"] > 0]
    return dict(down_learners=down, up_learners=up, included_learners=list(design.LEARNERS),
                consistent_down=len(down) >= 2 and not up,
                consistent_up=len(up) >= 2 and not down)


def correct_families(contrasts):
    report = defaultdict(list)
    decision = []
    for c in contrasts:
        c.update(report_family=None, p_holm_report=None, significant_report=False,
                 decision_a_family=None, p_holm_decision_a=None, significant_decision_a=False)
        if not c["testable"]:
            continue
        name = f"report::{c['router']}::{c['learner']}::pi1"
        report[name].append(c)
        c["report_family"] = name
        if c["penalty"] == 0.25 and c["audit_efficacy_evidence_allowed"]:
            decision.append(c)
            c["decision_a_family"] = DECISION_FAMILY
    for group, suffix in [(g, "report") for g in report.values()] + [(decision, "decision_a")]:
        for c, p in zip(group, stats.holm([c["p_raw"] for c in group])):
            c["p_holm_" + suffix] = float(p)
            c["significant_" + suffix] = bool(p < stats.ALPHA)
    return {k: len(v) for k, v in report.items()}, len(decision)


def classify(contrasts):
    groups = defaultdict(list)
    for c in contrasts:
        groups[c["router"], c["audit"], c["penalty"], c["metric"]].append(c)
    votes = []
    for (router, audit, penalty, metric), group in groups.items():
        report = direction_vote(group, "significant_report")
        decision = direction_vote(group, "significant_decision_a")
        allowed = penalty != 0.015625 and all(c["audit_efficacy_evidence_allowed"] for c in group)
        default_hit = (allowed and penalty == 0.25 and audit in stats.RESULT1_AUDITS
                       and report["consistent_down"] and decision["consistent_down"])
        votes.append(dict(router=router, audit=audit, penalty=penalty, metric=metric,
                          audit_efficacy_evidence_allowed=allowed,
                          report=report, decision_a=decision, result1_hit=default_hit,
                          report_hit=allowed and report["consistent_down"],
                          astar_by_learner={c["learner"]: c["astar_relation"] for c in group},
                          all_supporting_learners_at_or_above_astar=report["consistent_down"] and all(
                              c["astar_relation"]["relation"] == "at_or_above"
                              for c in group if c["learner"] in report["down_learners"])))
    routers = {}
    for router in ("pilot", "strongest"):
        default_hits = [v for v in votes if v["router"] == router and v["result1_hit"]]
        some_hits = [v for v in votes if v["router"] == router and v["report_hit"]]
        routers[router] = dict(result=1 if default_hits else (2 if some_hits else 3),
                               default_parameter_audit_works=bool(default_hits),
                               default_hits=default_hits, report_hits=some_hits,
                               all_report_hits_at_or_above_astar=bool(some_hits) and all(
                                   v["all_supporting_learners_at_or_above_astar"] for v in some_hits))
    overall = min(r["result"] for r in routers.values())
    return dict(result=overall, routers=routers, direction_consistency=votes,
                both_routers_default_pass=all(r["result"] == 1 for r in routers.values()),
                overall_rule="1 if any router passes AFTER merged correction; routers reported separately; "
                             "else 2 if any eligible report-family hit, else 3",
                cascade_contrast_included=False, paper_title_or_claims_changed=False)


def analyze(rows):
    by_cell = defaultdict(list)
    for row in rows:
        by_cell[row["cell_id"], row["learner"]].append(row)
    cells = []
    contrasts = []
    for (cid, learner), group in by_cell.items():
        group.sort(key=lambda r: r["seed"])
        first = group[0]
        identifiable = sum(r["tail_trade"] for r in group) / len(group) > 0.5
        realised = float(np.mean([r["audit_rate_realised"] for r in group]))
        rec = dict(design_cell_metadata(first), learner=learner, n_runs=len(group),
                   tail_trade_runs=sum(r["tail_trade"] for r in group),
                   tail_trade_rate=sum(r["tail_trade"] for r in group) / len(group),
                   Q_identifiable=identifiable, audit_rate_realised_mean=realised,
                   per_run_strategic_tail_counts=[
                       dict(seed=r["seed"], tail_sales=r["tail_sales"],
                            by_seller=r["strategic_tail_counts"]) for r in group],
                   astar_relation=astar(first["audit"], first["penalty"], realised))
        for metric in METRICS:
            est = estimate([r[metric] for r in group], f"cellmean:{cid}:{learner}:{metric}")
            rec[metric] = {k: est[k] for k in ("mean", "lo", "hi")}
        cells.append(rec)
        if first["audit"] == "a0":
            continue
        base_id = next(c.cell_id for c in design.cells()
                       if c.router == first["router"] and c.audit == "a0" and c.penalty == first["penalty"])
        baseline = sorted(by_cell[base_id, learner], key=lambda r: r["seed"])
        require([r["seed"] for r in group] == [r["seed"] for r in baseline] == list(range(20)),
                "same-seed pairing mismatch")
        base_identifiable = sum(r["tail_trade"] for r in baseline) / len(baseline) > 0.5
        for metric in ("E", "Q"):
            testable = metric != "Q" or (identifiable and base_identifiable)
            delta = estimate([r[metric] - b[metric] for r, b in zip(group, baseline)],
                             f"delta:{cid}:{learner}:{metric}")
            contrasts.append(dict(
                design_cell_metadata(first), learner=learner, metric=metric, baseline_cell_id=base_id,
                delta_mean=delta["mean"], delta_lo=delta["lo"], delta_hi=delta["hi"],
                p_raw=delta["p"] if testable else None,
                testable=testable, skip_reason=None if testable else "Q_not_identifiable",
                Q_identifiable=identifiable, baseline_Q_identifiable=base_identifiable,
                astar_relation=rec["astar_relation"]))
    families, n_decision = correct_families(contrasts)
    return dict(cells=cells, contrasts=contrasts, report_family_sizes=families,
                decision_a_family=dict(name=DECISION_FAMILY, n_tests=n_decision,
                                       scope="both routers, all three learners, P=0.25, pi=1, all nonzero audits, E+Q"),
                classification=classify(contrasts))


def design_cell_metadata(row):
    return {k: row[k] for k in design.cells()[0].metadata()}


def write_csv(path, rows):
    with path.open("x", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows({k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v
                          for k, v in r.items()} for r in rows)


def report(payload):
    verdict = payload["classification"]
    lines = [
        "# Cross-Border v1.2 Decision A",
        "",
        f"§1.4 classification: **{verdict['result']}**. No paper title or claims changed.",
        "2880 runs; 48 factorial cells × 3 learners × 20 seeds; 1000 rounds / 10000 tasks.",
        "Same-seed paired bootstrap B=10000, 95% percentile CI; two-sided sign-tail p; Holm α=0.05.",
        "EXP3 participates in every direction vote: the WP2 nonconvergence exclusion is NOT triggered.",
        "Q is reported for every cell; tested only when both contrast cells have tail-trade share >50%.",
        "Report families: router × learner × π, all (a,P), E+Q. P/16 is descriptive only.",
        "Decision A family: both routers AND all three learners, default P=0.25, π=1, all audits, E+Q.",
        "P/16 cannot support result 1, result 2, or any audit-efficacy conclusion.",
        verdict["overall_rule"],
        "Cascade a=0 vs a>0 is outside this grid and is not used in this verdict.",
        "",
        "## Router-specific decisions",
    ]
    for router, value in verdict["routers"].items():
        lines.append(f"- {router}: result {value['result']}; "
                     f"{len(value['default_hits'])} merged-corrected default hits, "
                     f"{len(value['report_hits'])} eligible report hits; "
                     f"all eligible hits at/above frozen a*: {value['all_report_hits_at_or_above_astar']}.")
    lines += ["", "## Cells (20-seed estimates and 95% CIs)"]
    for c in payload["cells"]:
        estimates = "; ".join(f"{k}={stats.fmt_est(c[k]['mean'], c[k]['lo'], c[k]['hi'], 5)}"
                              for k in METRICS)
        lines.append(f"- {c['cell_id']} / {c['learner']}: {estimates}; "
                     f"tail trades {c['tail_trade_runs']}/20; Q identifiable={c['Q_identifiable']}; "
                     f"a*={json.dumps(c['astar_relation'])}.")
    lines += ["", "## Contrasts vs same-router/P/π/learner a=0"]
    for c in payload["contrasts"]:
        lines.append(f"- {c['cell_id']} / {c['learner']} / {c['metric']}: "
                     f"Δ={stats.fmt_est(c['delta_mean'], c['delta_lo'], c['delta_hi'], 5)}; "
                     f"p={c['p_raw']}; report Holm={c['p_holm_report']}; "
                     f"Decision A Holm={c['p_holm_decision_a']}; tested={c['testable']}; "
                     f"evidence allowed={c['audit_efficacy_evidence_allowed']}.")
    lines += ["", "## Direction consistency (all three learners; significant opposite sign vetoes)"]
    for v in verdict["direction_consistency"]:
        lines.append(f"- {v['router']} / {v['audit']} / P={v['penalty']} / {v['metric']}: "
                     f"report={json.dumps(v['report'])}; merged={json.dumps(v['decision_a'])}; "
                     f"result1_hit={v['result1_hit']}.")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--protocol", required=True, type=Path)
    ap.add_argument("--protocol-sha256", required=True)
    args = ap.parse_args(argv)
    run = args.run.resolve()
    out = design.fresh_output(ROOT, args.out, run)
    rows, meta, hashes = validate_inputs(run, args.protocol.resolve(), args.protocol_sha256)
    fact = wp2_fact()
    payload = analyze(rows)
    payload.update(protocol_sha256=design.PROTOCOL_SHA256, run=str(run), run_meta=meta,
                   input_sha256=hashes, wp2_fact=fact, B=stats.B, alpha=stats.ALPHA,
                   rng_seed=stats.RNG_SEED,
                   bootstrap="paired same-seed differences; 95% percentile CI; "
                             "two-sided p=2*min(P*(delta<=0), P*(delta>=0)) capped at 1",
                   rng_key="sha256 of 20261110:delta:<cell_id>:<learner>:<metric>; first 8 bytes little endian",
                   checks={"runs": 2880, "cells": 48, "learner_groups": 144, "seeds_per_group": 20,
                           "CSV_JSONL_and_summaries_equal": True, "config_hashes_recomputed": 2880})
    out.mkdir(parents=True, exist_ok=True)
    with (out / "decision_a_eval.json").open("x") as fh:
        json.dump(payload, fh, indent=2, allow_nan=False)
        fh.write("\n")
    with (out / "decision_a_eval.md").open("x") as fh:
        fh.write(report(payload))
    write_csv(out / "contrasts.csv", payload["contrasts"])
    write_csv(out / "cells.csv", payload["cells"])
    write_csv(out / "direction_consistency.csv", payload["classification"]["direction_consistency"])
    for name in ("decision_a_eval.json", "decision_a_eval.md", "contrasts.csv",
                 "cells.csv", "direction_consistency.csv"):
        with (out / (name + ".sha256")).open("x") as fh:
            fh.write(f"{digest(out / name)}  {name}\n")
    print(json.dumps(dict(out=str(out), result=payload["classification"]["result"],
                          n_decision_a_tests=payload["decision_a_family"]["n_tests"])))


if __name__ == "__main__":
    main()
