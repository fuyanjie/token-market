#!/usr/bin/env python3
"""PROTOCOL_v1.1 WP1 official readout: same-seed paired bootstrap + Holm.

Reads results/v1.1/wp1/ (runner output). Writes results/v1.1/wp1_eval/.
Does not overwrite the run directory. No figures.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path

import numpy as np

B = 10_000
RNG_SEED = 20261110
ALPHA = 0.05
PROTOCOL_SHA256 = "e9c84494a7031d7023d4861c02a5786a59fbc74541007978a13b9882f209c179"
A_STAR = {
    0.25: (0.044, 0.050),
    0.0625: (0.18, 0.20),
    0.015625: (0.71, 0.80),
}
P_LABEL = {0.25: "P", 0.0625: "P/4", 0.015625: "P/16"}
AUDIT_ORDER = ["a0", "a0.01", "a0.02", "a0.03", "a0.05", "a0.1", "a0.2", "risk_adaptive"]
AUDIT_NUMERIC = {
    "a0": 0.0,
    "a0.01": 0.01,
    "a0.02": 0.02,
    "a0.03": 0.03,
    "a0.05": 0.05,
    "a0.1": 0.10,
    "a0.2": 0.20,
    "risk_adaptive": None,
}
RESULT1_AUDITS = {"a0.05", "a0.1", "a0.2", "risk_adaptive"}
ROUTER_ORDER = ["pilot", "strongest", "stageroute", "cascade", "cheapest", "cascade+trust"]
ROUTER_LABEL = {
    "pilot": "PILOT",
    "strongest": "strongest",
    "stageroute": "StageRoute",
    "cascade": "cascade",
    "cheapest": "cheapest",
    "cascade+trust": "cascade+trust",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_bool(x) -> bool:
    if isinstance(x, bool):
        return x
    s = str(x).strip().lower()
    if s in ("1", "true", "yes"):
        return True
    if s in ("0", "false", "no", ""):
        return False
    raise ValueError(x)


def parse_float(x, default=np.nan) -> float:
    if x is None or str(x).strip() == "":
        return default
    return float(x)


def holm(ps):
    m = len(ps)
    order = np.argsort(ps)
    adj = [0.0] * m
    run = 0.0
    for k, i in enumerate(order):
        run = max(run, min(1.0, (m - k) * ps[i]))
        adj[i] = run
    return adj


def contrast_rng(key: str) -> np.random.Generator:
    digest = hashlib.sha256(f"{RNG_SEED}:{key}".encode()).digest()
    seed = int.from_bytes(digest[:8], "little")
    return np.random.default_rng(seed)


def boot_mean_ci(x, rng):
    x = np.asarray(x, float)
    n = len(x)
    if n == 0 or np.any(~np.isfinite(x)):
        return float("nan"), float("nan"), float("nan"), float("nan")
    idx = rng.integers(0, n, size=(B, n))
    bm = x[idx].mean(axis=1)
    lo, hi = np.percentile(bm, [2.5, 97.5])
    p = min(1.0, 2 * min((bm <= 0).mean(), (bm >= 0).mean()))
    return float(np.mean(x)), float(lo), float(hi), float(p)


def fmt_est(mean, lo=None, hi=None, digits=3):
    if mean is None or (isinstance(mean, float) and not np.isfinite(mean)):
        return "—"
    if lo is None:
        return f"{mean:.{digits}f}"
    if not np.isfinite(lo) or not np.isfinite(hi):
        return f"{mean:.{digits}f}"
    return f"{mean:.{digits}f} [{lo:.{digits}f}, {hi:.{digits}f}]"


def a_vs_astar(audit, penalty, realised=None):
    lo, hi = A_STAR[penalty]
    a = AUDIT_NUMERIC[audit]
    if a is None:
        a = realised
        source = "realised"
    else:
        source = "nominal"
    if a is None or not np.isfinite(a):
        return None, source, lo, hi
    if a + 1e-12 < lo:
        rel = "below"
    elif a + 1e-12 < hi:
        rel = "in_interval"
    else:
        rel = "at_or_above"
    return rel, source, lo, hi, float(a)


def load_per_seed(path: Path):
    rows = list(csv.DictReader(open(path)))
    out = []
    for r in rows:
        d = dict(r)
        d["pi"] = float(r["pi"])
        d["seed"] = int(r["seed"])
        d["penalty"] = float(r["penalty"])
        d["n_rounds"] = int(r["n_rounds"])
        d["n_tasks"] = int(r["n_tasks"])
        for k in (
            "E", "E_tok", "Q", "q_swap", "q_theft", "q_downgrade",
            "accuracy", "cost_per_task", "audit_rate_realised", "tail_sales",
            "Q_swap", "Q_theft", "Q_downgrade",
        ):
            d[k] = parse_float(r.get(k, ""))
        d["tail_trade"] = parse_bool(r["tail_trade"])
        d["audit_efficacy_evidence_allowed"] = parse_bool(r["audit_efficacy_evidence_allowed"])
        out.append(d)
    return out


def load_cells(path: Path):
    return json.loads(Path(path).read_text())


def main():
    root = Path(__file__).resolve().parents[2]
    run_dir = root / "results/v1.1/wp1"
    out_dir = root / "results/v1.1/wp1_eval"
    out_dir.mkdir(parents=True, exist_ok=True)

    checks = []
    completion = json.loads((run_dir / "completion.json").read_text())
    meta = json.loads((run_dir / "run_meta.json").read_text())
    protocol_path = root / "docs/v1.1/PROTOCOL_v1.1.md"
    protocol_sha = sha256_file(protocol_path)
    checks.append({
        "name": "protocol_sha256",
        "ok": protocol_sha == PROTOCOL_SHA256 == meta.get("protocol_sha256"),
        "detail": {"file": protocol_sha, "frozen": PROTOCOL_SHA256, "run_meta": meta.get("protocol_sha256")},
    })
    fact_rows = load_per_seed(run_dir / "factorial/per_seed.csv")
    ctrl_rows = load_per_seed(run_dir / "control/per_seed.csv")
    rows = fact_rows + ctrl_rows
    fact_cells = load_cells(run_dir / "factorial/cells.json")
    ctrl_cells = load_cells(run_dir / "control/cells.json")
    cells = fact_cells + ctrl_cells

    n_runs = len(rows)
    n_unique = len({(r["cell_id"], r["seed"]) for r in rows})
    n_cells = len({r["cell_id"] for r in rows})
    seeds_ok = all(
        sorted(r["seed"] for r in rows if r["cell_id"] == cid) == list(range(20))
        for cid in {r["cell_id"] for r in rows}
    )
    checks.append({
        "name": "run_count",
        "ok": n_runs == 4800 and n_unique == 4800 and completion["n_runs_completed"] == 4800
        and meta["n_runs_planned"] == 4800 and n_cells == 240,
        "detail": {
            "per_seed_rows": n_runs, "unique_cell_seed": n_unique,
            "cells": n_cells, "completion": completion["n_runs_completed"],
            "planned": meta["n_runs_planned"],
        },
    })
    checks.append({"name": "all_20_seeds_per_cell", "ok": seeds_ok, "detail": {}})
    checks.append({
        "name": "grid_shape",
        "ok": meta["n_factorial_cells"] == 216 and meta["n_control_cells"] == 24
        and len(fact_cells) == 216 and len(ctrl_cells) == 24
        and meta["n_rounds"] == 48 and meta["n_tasks"] == 480
        and meta["learner"] == "egreedy" and meta["seeds"] == list(range(20)),
        "detail": {
            "n_factorial_cells": meta["n_factorial_cells"],
            "n_control_cells": meta["n_control_cells"],
            "n_rounds": meta["n_rounds"], "n_tasks": meta["n_tasks"],
            "learner": meta["learner"],
        },
    })

    # Recompute cell means from per-seed and compare to cells.json
    by_cell_rows = defaultdict(list)
    for r in rows:
        by_cell_rows[r["cell_id"]].append(r)
    cell_by_id = {c["cell_id"]: c for c in cells}
    max_abs = 0.0
    mismatches = []
    for cid, rs in by_cell_rows.items():
        c = cell_by_id[cid]
        tail_runs = sum(1 for r in rs if r["tail_trade"])
        tail_rate = tail_runs / len(rs)
        q_id = tail_rate > 0.5
        for key in ("E", "E_tok", "Q", "q_swap", "q_theft", "q_downgrade", "accuracy", "cost_per_task"):
            rec = float(np.mean([r[key] for r in rs]))
            listed = c[key]
            err = abs(rec - listed)
            max_abs = max(max_abs, err)
            if err > 1e-10:
                mismatches.append((cid, key, rec, listed, err))
        if c["n_runs"] != 20 or c["tail_trade_runs"] != tail_runs:
            mismatches.append((cid, "tail_counts", tail_runs, c["tail_trade_runs"], None))
        if bool(c["Q_identifiable"]) != q_id:
            mismatches.append((cid, "Q_identifiable", q_id, c["Q_identifiable"], None))
    checks.append({
        "name": "cells_json_matches_per_seed",
        "ok": len(mismatches) == 0,
        "detail": {"max_abs_mean_err": max_abs, "n_mismatch": len(mismatches), "sample": mismatches[:5]},
    })

    # Index (router, audit, penalty, pi, seed) -> row
    idx = {}
    for r in rows:
        idx[(r["router"], r["audit"], r["penalty"], r["pi"], r["seed"])] = r

    # Attach bootstrap CI for cell-level means (reporting)
    cell_ci = {}
    for c in cells:
        cid = c["cell_id"]
        rs = sorted(by_cell_rows[cid], key=lambda r: r["seed"])
        rec = {
            "cell_id": cid,
            "router": c["router"],
            "audit": c["audit"],
            "penalty": c["penalty"],
            "penalty_label": c["penalty_label"],
            "pi": c["pi"],
            "arm": c["arm"],
            "policy": c["policy"],
            "trust_feedback": c["trust_feedback"],
            "audit_efficacy_evidence_allowed": c["audit_efficacy_evidence_allowed"],
            "n_runs": 20,
            "tail_trade_runs": c["tail_trade_runs"],
            "tail_trade_rate": c["tail_trade_rate"],
            "Q_identifiable": c["Q_identifiable"],
            "audit_rate_realised_mean": float(np.mean([r["audit_rate_realised"] for r in rs])),
        }
        for key in ("E", "E_tok", "Q", "q_swap", "q_theft", "q_downgrade", "accuracy", "cost_per_task"):
            vals = np.array([r[key] for r in rs], float)
            mean, lo, hi, p = boot_mean_ci(vals, contrast_rng(f"cellmean:{cid}:{key}"))
            rec[key] = {"mean": mean, "lo": lo, "hi": hi, "p_vs_zero": p}
        rec["astar_relation"] = None
        if c["audit"] != "a0":
            rel = a_vs_astar(c["audit"], c["penalty"], rec["audit_rate_realised_mean"])
            rec["astar_relation"] = {
                "relation": rel[0], "a_source": rel[1], "a_star_lo": rel[2],
                "a_star_hi": rel[3], "a_used": rel[4],
            }
        cell_ci[cid] = rec

    # Build contrasts vs a=0
    contrasts = []
    keys_seen = set()
    for c in cells:
        if c["audit"] == "a0":
            continue
        base_id = None
        for b in cells:
            if (b["router"] == c["router"] and b["audit"] == "a0"
                    and b["penalty"] == c["penalty"] and b["pi"] == c["pi"]
                    and b["trust_feedback"] == c["trust_feedback"]):
                base_id = b["cell_id"]
                base = b
                break
        if base_id is None:
            raise RuntimeError(f"missing a=0 for {c['cell_id']}")
        for metric in ("E", "Q"):
            diffs = []
            for seed in range(20):
                t = idx[(c["router"], c["audit"], c["penalty"], c["pi"], seed)]
                s = idx[(c["router"], "a0", c["penalty"], c["pi"], seed)]
                diffs.append(t[metric] - s[metric])
            testable = True
            skip_reason = None
            if metric == "Q":
                if not c["Q_identifiable"] or not base["Q_identifiable"]:
                    testable = False
                    skip_reason = "Q_not_identifiable"
            mean, lo, hi, p = boot_mean_ci(diffs, contrast_rng(f"delta:{c['cell_id']}:{metric}"))
            key = (c["router"], c["audit"], c["penalty"], c["pi"], c["trust_feedback"], metric)
            keys_seen.add(key)
            contrasts.append({
                "cell_id": c["cell_id"],
                "baseline_cell_id": base_id,
                "router": c["router"],
                "audit": c["audit"],
                "penalty": c["penalty"],
                "penalty_label": c["penalty_label"],
                "pi": c["pi"],
                "trust_feedback": c["trust_feedback"],
                "arm": c["arm"],
                "metric": metric,
                "delta_mean": mean,
                "delta_lo": lo,
                "delta_hi": hi,
                "p_raw": p,
                "testable": testable,
                "skip_reason": skip_reason,
                "audit_efficacy_evidence_allowed": c["audit_efficacy_evidence_allowed"],
                "direction_down": bool(np.isfinite(mean) and mean < 0),
            })

    # Report Holm families: same router, same learner (all egreedy), same π, all (a,P), E+Q
    # cascade+trust is its own router label, so its own family.
    families = defaultdict(list)
    for i, ct in enumerate(contrasts):
        if not ct["testable"]:
            continue
        fam = f"report::{ct['router']}::egreedy::pi{ct['pi']}"
        families[fam].append(i)
        ct["report_family"] = fam

    # Decision-A family: PILOT and strongest, P=0.25, π=1, all audits except P/16, E+Q
    da_members = []
    for i, ct in enumerate(contrasts):
        if not ct["testable"]:
            continue
        if ct["router"] not in ("pilot", "strongest"):
            continue
        if abs(ct["penalty"] - 0.25) > 1e-12 or abs(ct["pi"] - 1.0) > 1e-12:
            continue
        if not ct["audit_efficacy_evidence_allowed"]:
            continue
        da_members.append(i)
        ct["decision_a_family"] = "decisionA::PILOT+strongest::P::pi1"

    def apply_holm(member_indices, field):
        if not member_indices:
            return
        ps = [contrasts[i]["p_raw"] for i in member_indices]
        adj = holm(ps)
        for i, p_adj in zip(member_indices, adj):
            contrasts[i][field] = float(p_adj)
            contrasts[i][field.replace("p_holm", "significant")] = p_adj < ALPHA

    for fam, idxs in families.items():
        apply_holm(idxs, "p_holm_report")
    apply_holm(da_members, "p_holm_decision_a")

    for ct in contrasts:
        ct.setdefault("report_family", None)
        ct.setdefault("p_holm_report", None)
        ct.setdefault("significant_report", False if not ct["testable"] else None)
        ct.setdefault("decision_a_family", None)
        ct.setdefault("p_holm_decision_a", None)
        ct.setdefault("significant_decision_a", None)
        rel = a_vs_astar(
            ct["audit"], ct["penalty"],
            cell_ci[ct["cell_id"]]["audit_rate_realised_mean"],
        )
        ct["astar_relation"] = {
            "relation": rel[0], "a_source": rel[1], "a_star_lo": rel[2],
            "a_star_hi": rel[3], "a_used": rel[4],
        }

    # Diagnostic Result-1 reading on this 48-round egreedy grid only.
    # Official Decision A still requires §1.3 (WP2 recommended rounds, 3 learners).
    def result1_hits(router):
        hits = []
        for ct in contrasts:
            if ct["router"] != router:
                continue
            if abs(ct["penalty"] - 0.25) > 1e-12 or abs(ct["pi"] - 1.0) > 1e-12:
                continue
            if ct["audit"] not in RESULT1_AUDITS:
                continue
            if not ct["audit_efficacy_evidence_allowed"]:
                continue
            if not ct["testable"]:
                continue
            if ct["significant_decision_a"] and ct["direction_down"]:
                hits.append(ct)
        return hits

    diag = {
        "caveat": (
            "This is the 48-round egreedy diagnostic grid only. "
            "PROTOCOL §1.3 Decision A requires the WP2 recommended horizon and "
            "direction-consistent effects under at least two learners; that test has not been run."
        ),
        "pilot_default_hits": [
            {"audit": h["audit"], "metric": h["metric"],
             "delta": h["delta_mean"], "ci": [h["delta_lo"], h["delta_hi"]],
             "p_holm_decision_a": h["p_holm_decision_a"]}
            for h in result1_hits("pilot")
        ],
        "strongest_default_hits": [
            {"audit": h["audit"], "metric": h["metric"],
             "delta": h["delta_mean"], "ci": [h["delta_lo"], h["delta_hi"]],
             "p_holm_decision_a": h["p_holm_decision_a"]}
            for h in result1_hits("strongest")
        ],
    }
    diag["pilot_passes_stat_part"] = len(diag["pilot_default_hits"]) > 0
    diag["strongest_passes_stat_part"] = len(diag["strongest_default_hits"]) > 0
    diag["both_routers_stat_part"] = (
        diag["pilot_passes_stat_part"] and diag["strongest_passes_stat_part"]
    )

    # Within-router significant cells (report family), P/16 flagged
    sig_report = [ct for ct in contrasts if ct["testable"] and ct.get("significant_report")]
    sig_down = [ct for ct in sig_report if ct["direction_down"]]
    sig_down_allowed = [ct for ct in sig_down if ct["audit_efficacy_evidence_allowed"]]

    hashes = {
        "PROTOCOL_v1.1.md": protocol_sha,
        "completion.json": sha256_file(run_dir / "completion.json"),
        "run_meta.json": sha256_file(run_dir / "run_meta.json"),
        "manifest.json": sha256_file(run_dir / "manifest.json"),
        "factorial/cells.json": sha256_file(run_dir / "factorial/cells.json"),
        "factorial/per_seed.csv": sha256_file(run_dir / "factorial/per_seed.csv"),
        "control/cells.json": sha256_file(run_dir / "control/cells.json"),
        "control/per_seed.csv": sha256_file(run_dir / "control/per_seed.csv"),
        "completed_runs.jsonl": sha256_file(run_dir / "completed_runs.jsonl"),
    }

    payload = {
        "protocol_sha256": PROTOCOL_SHA256,
        "git_head_run": meta.get("git_head"),
        "learner": meta["learner"],
        "n_rounds": meta["n_rounds"],
        "n_tasks": meta["n_tasks"],
        "seeds": meta["seeds"],
        "B": B,
        "rng_seed": RNG_SEED,
        "alpha": ALPHA,
        "bootstrap": "same-seed paired percentile CI, two-sided p = 2*min(P*(δ≤0), P*(δ≥0))",
        "holm": "step-down, capped at 1; report family = router × learner × π, all (a,P), E and Q together; Decision-A family = PILOT+strongest, P=0.25, π=1, P/16 excluded",
        "elapsed_s": completion["elapsed_s"],
        "checks": checks,
        "hashes": hashes,
        "argv": meta.get("argv"),
        "diagnostic_result1": diag,
        "n_contrasts": len(contrasts),
        "n_report_families": len(families),
        "n_decision_a_tests": len(da_members),
        "n_significant_report_down": len(sig_down),
        "n_significant_report_down_efficacy_allowed": len(sig_down_allowed),
        "cells": list(cell_ci.values()),
        "contrasts": contrasts,
        "report_family_sizes": {k: len(v) for k, v in families.items()},
    }

    (out_dir / "wp1_eval.json").write_text(json.dumps(payload, indent=2, default=float))

    # Markdown
    L = []
    L.append("# Cross-Border v1.1 WP1 official readout (48-round egreedy diagnostic)")
    L.append("")
    L.append("This file is the official cell-level report for the 4800-run WP1 grid. ")
    L.append("It is a diagnostic result under PROTOCOL_v1.1 §1.1. ")
    L.append("Decision point A is **not** declared here: §1.3 still requires the WP2 recommended horizon and at least two learners.")
    L.append("")
    L.append("## Verification")
    L.append("")
    L.append(f"- Run dir: `results/v1.1/wp1/`")
    L.append(f"- Completion: {completion['n_runs_completed']}/4800 in {completion['elapsed_s']:.1f} s, ended 2026-11-11 02:46 Asia/Shanghai.")
    L.append(f"- Runner git_head: `{meta.get('git_head')}`")
    L.append(f"- PROTOCOL_v1.1 sha256: `{PROTOCOL_SHA256}`")
    L.append(f"- Learner egreedy, n_rounds=48, n_tasks=480, seeds 0–19, jobs 8, `--log-transactions`.")
    L.append(f"- Stats: same-seed paired bootstrap, B={B}, 95% percentile CI, two-sided p; Holm α={ALPHA}.")
    L.append(f"- RNG base seed {RNG_SEED}; each contrast uses an independent generator seeded by sha256 of `{RNG_SEED}:delta:<cell_id>:<metric>`.")
    for ch in checks:
        mark = "PASS" if ch["ok"] else "FAIL"
        L.append(f"- Check `{ch['name']}`: **{mark}**")
    L.append("")
    L.append("sha256 of inputs:")
    L.append("")
    for name, h in hashes.items():
        L.append(f"- `{name}`: `{h}`")
    L.append("")
    L.append("Audit checks are identity+length on every arm. Do not compare these numbers directly to v1.0 audit-arm results.")
    L.append("P/16 cells are retained but `audit_efficacy_evidence_allowed=false`; they are excluded from the Decision-A family and from any Result-1 reading.")
    L.append("")
    L.append("## Diagnostic reading (not Decision A)")
    L.append("")
    L.append(diag["caveat"])
    L.append("")
    def hit_line(router, hits):
        if not hits:
            return f"- {ROUTER_LABEL[router]} at default P=0.25, π=1: no (audit, metric) in {{a=0.05, 0.10, 0.20, risk-adaptive}} significantly reduced after the Decision-A Holm family."
        bits = ", ".join(
            f"{h['audit']} {h['metric']} Δ={h['delta']:.3f} [{h['ci'][0]:.3f}, {h['ci'][1]:.3f}] p_Holm={h['p_holm_decision_a']:.4g}"
            for h in hits
        )
        return f"- {ROUTER_LABEL[router]} at default P=0.25, π=1: statistical part of Result 1 would pass on this grid — {bits}."
    L.append(hit_line("pilot", diag["pilot_default_hits"]))
    L.append(hit_line("strongest", diag["strongest_default_hits"]))
    if diag["both_routers_stat_part"]:
        L.append("- Both PILOT and strongest have at least one default-parameter hit after the merged Decision-A family. Official Result 1 still waits on §1.3.")
    else:
        L.append("- The merged-family default-parameter statistical part does not hold on both routers in this diagnostic grid. Official Result 1/2/3 waits on §1.3.")
    L.append("")
    L.append(f"- Within-router report families: {len(sig_down)} significant reductions (E or Q vs a=0, Holm-adjusted); {len(sig_down_allowed)} of these are on efficacy-allowed (non-P/16) cells.")
    L.append("")
    L.append("## Decision-A family (PILOT + strongest, P=0.25, π=1, P/16 excluded)")
    L.append("")
    L.append("| router | audit | metric | Δ vs a=0 | raw p | Holm p | significant |")
    L.append("|---|---|---|---|---:|---:|---|")
    da_rows = [ct for ct in contrasts if ct.get("decision_a_family")]
    da_rows += [ct for ct in contrasts
                if ct["router"] in ("pilot", "strongest")
                and abs(ct["penalty"] - 0.25) < 1e-12 and abs(ct["pi"] - 1.0) < 1e-12
                and ct["audit_efficacy_evidence_allowed"]
                and not ct["testable"]]
    # unique
    seen = set()
    ordered = []
    for ct in contrasts:
        if ct["router"] not in ("pilot", "strongest"):
            continue
        if abs(ct["penalty"] - 0.25) > 1e-12 or abs(ct["pi"] - 1.0) > 1e-12:
            continue
        if not ct["audit_efficacy_evidence_allowed"]:
            continue
        key = (ct["router"], AUDIT_ORDER.index(ct["audit"]), ct["metric"])
        if key in seen:
            continue
        seen.add(key)
        ordered.append((key, ct))
    for _, ct in sorted(ordered, key=lambda x: (ROUTER_ORDER.index(x[1]["router"]), AUDIT_ORDER.index(x[1]["audit"]), x[1]["metric"])):
        dgs = 3 if abs(ct["delta_mean"]) >= 0.01 or not np.isfinite(ct["delta_mean"]) else 4
        holm_s = "—" if ct["p_holm_decision_a"] is None else f"{ct['p_holm_decision_a']:.4g}"
        raw_s = "—" if not ct["testable"] else f"{ct['p_raw']:.4g}"
        sig = "—" if not ct["testable"] else ("yes" if ct["significant_decision_a"] else "no")
        if not ct["testable"]:
            sig = f"not tested ({ct['skip_reason']})"
        L.append(
            f"| {ROUTER_LABEL[ct['router']]} | {ct['audit']} | {ct['metric']} | "
            f"{fmt_est(ct['delta_mean'], ct['delta_lo'], ct['delta_hi'], dgs)} | {raw_s} | {holm_s} | {sig} |"
        )
    L.append("")
    L.append("## All cells (point estimates, 20-seed means and 95% CI)")
    L.append("")
    L.append("| cell | E | E_tok | Q | Q ident. | tail runs | q_swap / q_theft / q_downgrade | accuracy | cost/task | a realised | vs a* | allowed |")
    L.append("|---|---|---|---|---|---:|---|---|---|---|---|---|")
    def cell_sort(c):
        return (
            0 if c["arm"] == "factorial" else 1,
            ROUTER_ORDER.index(c["router"]),
            {1.0: 0, 0.1: 1, 0.0: 2}[c["pi"]],
            {0.25: 0, 0.0625: 1, 0.015625: 2}[c["penalty"]],
            AUDIT_ORDER.index(c["audit"]),
        )
    for rec in sorted(cell_ci.values(), key=cell_sort):
        dgs_e = 4 if rec["E"]["mean"] < 0.05 else 3
        astar = "—"
        if rec["astar_relation"]:
            r = rec["astar_relation"]
            astar = f"{r['relation']} (a={r['a_used']:.3f} vs [{r['a_star_lo']}, {r['a_star_hi']}])"
        L.append(
            f"| `{rec['cell_id']}` | {fmt_est(rec['E']['mean'], rec['E']['lo'], rec['E']['hi'], dgs_e)} | "
            f"{fmt_est(rec['E_tok']['mean'], rec['E_tok']['lo'], rec['E_tok']['hi'], dgs_e)} | "
            f"{fmt_est(rec['Q']['mean'], rec['Q']['lo'], rec['Q']['hi'], 3)} | "
            f"{'yes' if rec['Q_identifiable'] else 'no'} | {rec['tail_trade_runs']}/20 | "
            f"{rec['q_swap']['mean']:.3f} / {rec['q_theft']['mean']:.3f} / {rec['q_downgrade']['mean']:.3f} | "
            f"{fmt_est(rec['accuracy']['mean'], rec['accuracy']['lo'], rec['accuracy']['hi'], 3)} | "
            f"{fmt_est(rec['cost_per_task']['mean'], rec['cost_per_task']['lo'], rec['cost_per_task']['hi'], 4)} | "
            f"{rec['audit_rate_realised_mean']:.3f} | {astar} | "
            f"{'yes' if rec['audit_efficacy_evidence_allowed'] else 'no'} |"
        )
    L.append("")
    L.append("## All contrasts vs a=0 (same router, P, π)")
    L.append("")
    L.append("| cell | metric | Δ vs a=0 | raw p | Holm p (report family) | sig (report) | Holm p (Decision A) | vs a* | allowed | tested |")
    L.append("|---|---|---|---:|---:|---|---:|---|---|---|")
    def ct_sort(ct):
        return (
            0 if ct["arm"] == "factorial" else 1,
            ROUTER_ORDER.index(ct["router"]),
            {1.0: 0, 0.1: 1, 0.0: 2}[ct["pi"]],
            {0.25: 0, 0.0625: 1, 0.015625: 2}[ct["penalty"]],
            AUDIT_ORDER.index(ct["audit"]),
            0 if ct["metric"] == "E" else 1,
        )
    for ct in sorted(contrasts, key=ct_sort):
        dgs = 3 if abs(ct["delta_mean"]) >= 0.01 or not np.isfinite(ct["delta_mean"]) else 4
        holm_r = "—" if ct["p_holm_report"] is None else f"{ct['p_holm_report']:.4g}"
        holm_a = "—" if ct["p_holm_decision_a"] is None else f"{ct['p_holm_decision_a']:.4g}"
        raw_s = "—" if not ct["testable"] else f"{ct['p_raw']:.4g}"
        if not ct["testable"]:
            sig_r = f"not tested ({ct['skip_reason']})"
        else:
            sig_r = "yes" if ct["significant_report"] else "no"
        rel = ct["astar_relation"]
        astar = f"{rel['relation']} (a={rel['a_used']:.3f})"
        L.append(
            f"| `{ct['cell_id']}` | {ct['metric']} | "
            f"{fmt_est(ct['delta_mean'], ct['delta_lo'], ct['delta_hi'], dgs)} | {raw_s} | {holm_r} | {sig_r} | {holm_a} | "
            f"{astar} | {'yes' if ct['audit_efficacy_evidence_allowed'] else 'no'} | "
            f"{'yes' if ct['testable'] else 'no'} |"
        )
    L.append("")
    L.append("cascade a=0 vs a>0 is reported in the tables above and, per §1.4, does not enter the Decision-A judgment.")
    L.append("cheapest Q is not identifiable on this grid (0/20 tail-trade runs) and is not tested.")
    L.append("")

    (out_dir / "wp1_eval.md").write_text("\n".join(L) + "\n")

    # Compact CSV of contrasts for later use
    with open(out_dir / "contrasts.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "cell_id", "baseline_cell_id", "router", "audit", "penalty", "penalty_label",
            "pi", "metric", "delta_mean", "delta_lo", "delta_hi", "p_raw",
            "p_holm_report", "significant_report", "p_holm_decision_a",
            "significant_decision_a", "testable", "skip_reason",
            "audit_efficacy_evidence_allowed", "direction_down", "report_family",
            "astar_relation", "a_used",
        ])
        w.writeheader()
        for ct in sorted(contrasts, key=ct_sort):
            w.writerow({
                **{k: ct.get(k) for k in w.fieldnames if k not in ("astar_relation", "a_used")},
                "astar_relation": ct["astar_relation"]["relation"],
                "a_used": ct["astar_relation"]["a_used"],
            })

    all_ok = all(ch["ok"] for ch in checks)
    print(json.dumps({
        "ok": all_ok,
        "out": str(out_dir),
        "checks": {ch["name"]: ch["ok"] for ch in checks},
        "diagnostic_result1": {
            "pilot": diag["pilot_passes_stat_part"],
            "strongest": diag["strongest_passes_stat_part"],
            "n_pilot_hits": len(diag["pilot_default_hits"]),
            "n_strongest_hits": len(diag["strongest_default_hits"]),
        },
        "n_contrasts": len(contrasts),
        "n_sig_report_down": len(sig_down),
        "n_sig_report_down_allowed": len(sig_down_allowed),
        "n_decision_a_tests": len(da_members),
        "n_decision_a_sig_down": sum(
            1 for ct in contrasts
            if ct.get("significant_decision_a") and ct["direction_down"]
        ),
    }, indent=2))
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
