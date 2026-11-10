"""Per-run metrics (v2, task- and purchase-level) and cross-seed aggregation."""
from __future__ import annotations

import math
import statistics
from collections import defaultdict
from typing import Dict, List


def p95(xs: List[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    k = (len(s) - 1) * 0.95
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def _mean(xs):
    xs = list(xs)
    return statistics.fmean(xs) if xs else 0.0


def run_metrics(records: List[Dict], buyers, seller_ids: List[str], rep, policy: str) -> Dict:
    served = [r for r in records if r["status"] == "allowed"]
    blocked = [r for r in records if r["status"] == "blocked"]
    unfilled = [r for r in records if r["status"] == "unfilled"]
    finals = [r for r in records if r["final"]]
    n_tasks = len(finals)
    swapped = [r for r in served if r["claimed_model"] != r["actual_model"]]
    # v4: token theft = billed materially above actually generated tokens; attacked = swapped OR theft
    thefts = [r for r in served if r.get("attack_mode") in ("theft", "both", "downgrade+theft")]
    attacked = [r for r in served if r.get("attack_mode", "swap" if r["claimed_model"] != r["actual_model"]
                                           else "none") not in ("none", None)]

    by_task = defaultdict(list)
    for r in served:
        by_task[r["task_id"]].append(r["latency_ms"])
    agg = sum if policy.startswith(("cascade", "audited")) else max
    task_lat = [agg(v) for v in by_task.values()]

    buyer_surplus = {b.id: 0.0 for b in buyers}
    spend = {b.id: 0.0 for b in buyers}
    seller_profit = {s: 0.0 for s in seller_ids}
    seller_correct = defaultdict(list)
    viol_by_rule, blocked_by_rule = defaultdict(int), defaultdict(int)
    for r in records:
        buyer_surplus[r["buyer_id"]] += r["buyer_surplus"]
        spend[r["buyer_id"]] += r["actual_cost"] + r.get("audit_cost", 0.0)
        if r["status"] == "allowed":
            seller_profit[r["seller_id"]] += r["seller_profit"]
            seller_correct[r["seller_id"]].append(1.0 if r["correct"] else 0.0)
            if r["violation"]:
                viol_by_rule[r["rule_id"]] += 1
        elif r["status"] == "blocked":
            blocked_by_rule[r["rule_id"]] += 1
    budgets = {b.id: b.budget for b in buyers}

    exp_claimed = [rep.accuracy(r["claimed_model"], r["difficulty"]) for r in swapped]
    acc_swapped = _mean(1.0 if r["correct"] else 0.0 for r in swapped)
    total_cost = sum(r["actual_cost"] for r in served)
    audited = [r for r in served if r["audited"]]
    audit_cost = sum(r["audit_cost"] for r in records)
    total_exp = sum(r["expected_cost"] for r in served)
    n_bv = sum(1 for r in served if r["budget_overrun"])
    overpay = sum(r["price_per_1k"] * (r.get("billed_tokens", r["reasoning_tokens"]) - r["reasoning_tokens"])
                  / 1000.0 for r in served)
    n_viol = sum(1 for r in served if r["violation"])
    billed_all = sum(r.get("billed_tokens", r["reasoning_tokens"]) for r in served)
    billed_att = sum(r.get("billed_tokens", r["reasoning_tokens"]) for r in attacked)
    return {
        # v4 joint-objective ingredients
        "compliance_violation_rate": n_viol / n_tasks if n_tasks else 0.0,   # per TASK
        "fraud_share": len(attacked) / len(served) if served else 0.0,       # per PURCHASE (swap OR theft)
        "E_tok": billed_att / billed_all if billed_all else 0.0,           # v1.0: per BILLED TOKEN (secondary E)
        "theft_share": len(thefts) / len(served) if served else 0.0,
        "thefts_served": len(thefts),
        "thefts_detected": sum(1 for r in served if r.get("theft_detected")),
        "length_audits": sum(1 for r in served if r.get("audit_type") in ("length", "both")),
        "identity_audits": sum(1 for r in served if r.get("audit_type") in ("identity", "both")),
        "attacks_detected": sum(1 for r in served if r["swap_detected"] or r.get("theft_detected")),
        "total_billed_tokens": billed_all,
        "total_actual_tokens": sum(r["reasoning_tokens"] for r in served),
        "buyer_overpayment": overpay,                                          # price * (billed - actual), excl. fee
        "mean_theft_inflation": _mean(r["token_inflation"] for r in thefts),
        "theft_accuracy": _mean(1.0 if r["correct"] else 0.0 for r in thefts),
        "attack_mode_counts": {m: sum(1 for r in served if r.get("attack_mode") == m)
                               for m in ("none", "swap", "theft", "both")
                               + tuple(x for x in ("downgrade", "downgrade+theft")      # v1.0, only when present
                                       if any(r.get("attack_mode") == x for r in served))},
        "seller_theft_rate": {s: _mean(1.0 if r.get("attack_mode") in ("theft", "both", "downgrade+theft") else 0.0
                                       for r in served if r["seller_id"] == s) for s in seller_ids},
        "n_tasks": n_tasks,
        "n_purchases": len(served),
        "n_lines": len(records),
        "n_blocked": len(blocked),
        "n_unfilled": len(unfilled),
        "purchases_per_task": len(served) / n_tasks if n_tasks else 0.0,
        "fill_rate": len({r["task_id"] for r in served}) / n_tasks if n_tasks else 0.0,
        "task_accuracy": _mean(1.0 if r["final_correct"] else 0.0 for r in finals),
        "purchase_accuracy": _mean(1.0 if r["correct"] else 0.0 for r in served),
        "total_cost": total_cost,
        "total_fee": sum(r["fee"] for r in served),
        "mean_cost_per_task": total_cost / n_tasks if n_tasks else 0.0,
        "total_audit_cost": audit_cost,
        "total_cost_incl_audit": total_cost + audit_cost,
        "mean_cost_per_task_incl_audit": (total_cost + audit_cost) / n_tasks if n_tasks else 0.0,
        "n_audits": len(audited),
        "swaps_detected": sum(1 for r in audited if r["swap_detected"]),
        "swaps_served": len(swapped),
        "mean_price_per_1k": _mean(r["price_per_1k"] for r in served),
        "total_expected_cost": total_exp,
        "total_cost_gap": total_cost - total_exp,
        "cost_gap_rel": (total_cost - total_exp) / total_exp if total_exp else 0.0,
        "mean_abs_cost_overrun": _mean(abs(r["cost_overrun"]) for r in served),
        "budget_violations": n_bv,
        "budget_violation_rate": n_bv / len(served) if served else 0.0,
        "buyers_over_budget": sum(1 for b in budgets if spend[b] > budgets[b] + 1e-12),
        "budget_exhausted_tasks": sum(1 for r in unfilled if r["rule_id"] == "MKT-BUDGET-EXHAUSTED"),
        "no_compliant_seller_tasks": sum(1 for r in unfilled if r["rule_id"] == "MKT-NO-COMPLIANT-SELLER"),
        "compliance_violations": sum(1 for r in served if r["violation"]),
        "blocked_at_gateway": len(blocked),
        "violations_by_rule": dict(viol_by_rule),
        "blocked_by_rule": dict(blocked_by_rule),
        "cross_border_share": _mean(1.0 if r["cross_border"] else 0.0 for r in served),
        "fraud_seller_share": len(swapped) / len(served) if served else 0.0,
        "fraud_accuracy_claimed": _mean(exp_claimed),
        "fraud_accuracy_actual": acc_swapped,
        "fraud_accuracy_gap": (_mean(exp_claimed) - acc_swapped) if swapped else 0.0,
        "mean_task_latency_ms": _mean(task_lat),
        "p95_task_latency_ms": p95(task_lat),
        "total_buyer_surplus": sum(buyer_surplus.values()),
        "total_seller_profit": sum(seller_profit.values()),
        "buyer_surplus": buyer_surplus,
        "seller_profit": seller_profit,
        "budget_utilisation": {b: spend[b] / budgets[b] if budgets[b] else 0.0 for b in budgets},
        "seller_accuracy": {s: _mean(v) for s, v in seller_correct.items()},
        "seller_purchases": {s: sum(1 for r in served if r["seller_id"] == s) for s in seller_ids},
        "seller_swap_rate": {s: _mean(1.0 if r["claimed_model"] != r["actual_model"] else 0.0
                                      for r in served if r["seller_id"] == s) for s in seller_ids},
        "overrun_purchases": sum(1 for r in served if r["cost_overrun"] > 1e-12),
        "max_rel_cost_overrun": max((r["actual_cost"] / r["expected_cost"] - 1.0 for r in served
                                     if r["expected_cost"] > 0), default=0.0),
    }


def _ms(xs: List[float]) -> Dict:
    return {"mean": _mean(xs), "std": statistics.stdev(xs) if len(xs) > 1 else 0.0}


def aggregate(per_seed: List[Dict]) -> Dict:
    """mean/std over seeds for every numeric metric (nested dicts are aggregated per key; a key missing in a
    seed counts as 0)."""
    out = {}
    keys = []
    for m in per_seed:
        keys += [k for k in m if k not in keys]
    for k in keys:
        vals = [m.get(k) for m in per_seed]
        if any(isinstance(v, (list, str)) for v in vals) or \
                any(isinstance(vv, list) for v in vals if isinstance(v, dict) for vv in v.values()):
            continue                     # per-epoch histories etc. stay in per_seed only
        if any(isinstance(v, dict) for v in vals):
            sub = sorted({kk for v in vals if isinstance(v, dict) for kk in v})
            out[k] = {kk: _ms([(v or {}).get(kk, 0) for v in vals]) for kk in sub}
        else:
            out[k] = _ms([v or 0 for v in vals])
    return out
