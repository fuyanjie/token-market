"""Per-run metrics and cross-seed aggregation."""
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
    return statistics.fmean(xs) if xs else 0.0


def run_metrics(records: List[Dict], buyer_ids: List[str], seller_ids: List[str],
                models: Dict, audit_violations: int) -> Dict:
    allowed = [r for r in records if r["status"] == "allowed"]
    blocked = [r for r in records if r["status"] == "blocked"]
    unfilled = [r for r in records if r["status"] == "unfilled"]
    lat = [r["latency_ms"] for r in allowed]
    swapped = [r for r in allowed if r["claimed_model"] != r["actual_model"]]
    honest = [r for r in allowed if r["claimed_model"] == r["actual_model"]]
    exp_claimed = [models[r["claimed_model"]]["accuracy"][r["difficulty"]] for r in swapped]
    buyer_surplus = {b: 0.0 for b in buyer_ids}
    seller_profit = {s: 0.0 for s in seller_ids}
    for r in records:
        buyer_surplus[r["buyer_id"]] += r["buyer_surplus"]
        if r["seller_id"] is not None and r["status"] == "allowed":
            seller_profit[r["seller_id"]] += r["seller_profit"]
    blocked_by_rule = defaultdict(int)
    for r in blocked:
        blocked_by_rule[r["rule_id"]] += 1
    n = len(records)
    return {
        "n_tx": n,
        "n_allowed": len(allowed),
        "n_blocked": len(blocked),
        "n_unfilled": len(unfilled),
        "fill_rate": len(allowed) / n if n else 0.0,
        "accuracy": _mean([1.0 if r["correct"] else 0.0 for r in allowed]),
        "total_cost": sum(r["cost"] for r in allowed),
        "total_fee": sum(r["fee"] for r in allowed),
        "mean_latency_ms": _mean(lat),
        "p95_latency_ms": p95(lat),
        "blocked_attempts": len(blocked),
        "violating_flows_through": audit_violations,
        "compliance_violations": len(blocked) + audit_violations,
        "blocked_by_rule": dict(blocked_by_rule),
        "cross_border_share": _mean([1.0 if r["cross_border"] else 0.0 for r in allowed]),
        "fraud_exposure": len(swapped) / len(allowed) if allowed else 0.0,
        "fraud_accuracy_claimed": _mean(exp_claimed),
        "fraud_accuracy_actual": _mean([1.0 if r["correct"] else 0.0 for r in swapped]),
        "fraud_accuracy_gap": (_mean(exp_claimed) - _mean([1.0 if r["correct"] else 0.0 for r in swapped]))
        if swapped else 0.0,
        "honest_accuracy": _mean([1.0 if r["correct"] else 0.0 for r in honest]),
        "total_buyer_surplus": sum(buyer_surplus.values()),
        "total_seller_profit": sum(seller_profit.values()),
        "buyer_surplus": buyer_surplus,
        "seller_profit": seller_profit,
    }


def _ms(xs: List[float]) -> Dict:
    return {"mean": _mean(xs), "std": statistics.stdev(xs) if len(xs) > 1 else 0.0}


def aggregate(per_seed: List[Dict]) -> Dict:
    """mean/std over seeds for every numeric metric (nested dicts are aggregated per key)."""
    out = {}
    for k, v in per_seed[0].items():
        if isinstance(v, dict):
            keys = sorted({kk for m in per_seed for kk in m[k]})
            out[k] = {kk: _ms([m[k].get(kk, 0) for m in per_seed]) for kk in keys}
        else:
            out[k] = _ms([m[k] for m in per_seed])
    return out
