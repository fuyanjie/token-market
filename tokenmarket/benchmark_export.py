"""v1 publishable benchmark export: five JSONL layers for analysis.

Files (under exports/<run_tag>/ by default):
  sellers.jsonl, buyers.jsonl, orders.jsonl, audits.jsonl, episodes.jsonl

Primary board metrics live on episodes.jsonl: active_attack_rate + fraud_share.
active_attack_rate = attacked/served purchases (NOT epoch-mean learned q).
learned_q_swap / learned_q_theft are separate columns; with delist they can diverge from active_attack_rate.
J is secondary (mirrored on episodes for convenience). Immediate-feedback J is NOT the primary ranking.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import yaml

from .backends import MockLLM
from .buyers import load_buyers
from .config import deep_merge, load_config
from .feedback import feedback_params
from .logging_schema import validate_record
from .sellers import Reputation, load_sellers
from .sim import policy_audit_rate, run_single
from .strategic import fraud_cfg
from .tasks import build_task_pool

SELLER_FIELDS = [
    "seller_id", "jurisdiction", "claimed_model", "actual_model", "listed_quality",
    "latent_q_swap", "latent_q_theft", "list_price", "capacity", "stake",
    "stake_remaining", "banned_until_round", "run_id", "seed",
]
BUYER_FIELDS = [
    "buyer_id", "jurisdiction", "budget_total", "budget_remaining", "strategy_id",
    "compliance_profile", "run_id", "seed",
]
ORDER_FIELDS = [
    "order_id", "round", "t_submit", "t_deliver", "t_settle", "buyer_id", "seller_id",
    "task_id", "portfolio_id", "tokens_billed", "tokens_actual", "price", "amount_escrow",
    "amount_paid", "state", "attack_mode", "correct", "jurisdiction_path", "route_policy",
    "run_id", "seed", "config_hash",
]
AUDIT_FIELDS = [
    "audit_id", "order_id", "round", "mode", "sampled", "identity_check", "length_check",
    "hit", "miss", "slash_amount", "delist_rounds", "auditor_cost", "label_revealed",
    "label_delay_L", "reveal_pi", "label_correct", "fraud_realized", "run_id", "seed",
]
EPISODE_FIELDS = [
    "run_id", "seed", "a", "pi", "L", "reputation_rounds", "active_attack_rate",
    "learned_q_swap", "learned_q_theft", "fraud_share", "J", "n_audits", "config_hash",
]
LABEL_FIELDS = [
    "order_id", "attack_mode", "correct", "actual_model", "latent_q_swap", "latent_q_theft",
    "run_id", "seed",
]
# Evaluation-label columns that remain in the default five tables for convenience
# but MUST NOT be used as training features (see docs/DATA_SCHEMA.md Feature/Label).
SELLER_LABEL_FIELDS = ("actual_model", "latent_q_swap", "latent_q_theft")
ORDER_LABEL_FIELDS = ("attack_mode", "correct")
AUDIT_LABEL_FIELDS = ("fraud_realized", "label_correct")

LAYER_FILES = {
    "sellers": "sellers.jsonl",
    "buyers": "buyers.jsonl",
    "orders": "orders.jsonl",
    "audits": "audits.jsonl",
    "episodes": "episodes.jsonl",
}


def config_hash(cfg: Dict) -> str:
    blob = json.dumps(cfg, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def export_knobs(cfg: Dict) -> Dict:
    """One-click export of a, π, L, reputation_rounds (+ appendix switches)."""
    m = cfg.get("market", {})
    fb = m.get("feedback", {})
    aud = m.get("audited", {})
    f = cfg.get("fraud", {})
    return {
        "a": float(aud.get("audit_rate", m.get("audit", {}).get("rate", 0.0))),
        "audit_rate_default_policies": float(m.get("audit", {}).get("rate", 0.0)),
        "pi": float(fb.get("reveal_prob", 1.0)),
        "L": fb.get("delay_L", 0),
        "feedback_mode": fb.get("mode", "immediate"),
        "reputation_rounds": int(aud.get("reputation_rounds", f.get("reputation_rounds", 0))),
        "adaptive_audit": bool(aud.get("adaptive_audit", False)),
        "escrow": bool(aud.get("escrow", False)),
        "note": "adaptive_audit / reputation_rounds / escrow default OFF so legacy F/J stay reproducible",
    }


def write_jsonl(path: str, rows: Iterable[Dict]) -> int:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    n = 0
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
            n += 1
    return n


def _order_id(rec: Dict, idx: int) -> str:
    if rec.get("purchase_id"):
        return str(rec["purchase_id"])
    # blocked / unfilled lines have no purchase_id in the sim logger
    return f"{rec.get('run_id','run')}|{rec.get('task_id','t')}|{rec.get('portfolio_step', 0)}|{rec.get('seller_id') or 'none'}|line{idx}"


def _order_state(rec: Dict) -> str:
    st = rec.get("status")
    if st == "blocked":
        return "blocked"
    if st == "unfilled":
        return "unfilled"
    es = float(rec.get("escrow_slashed") or 0.0)
    er = float(rec.get("escrow_released") or 0.0)
    eh = float(rec.get("escrow_held") or 0.0)
    if es > 0:
        return "slashed"
    if rec.get("audited"):
        # audited then released (or escrow off)
        if eh > 0 and er == 0 and es == 0:
            return "audited"  # rare online path
        return "settled" if er > 0 or eh == 0 else "audited"
    if eh > 0 and er == 0:
        return "locked"
    if st == "allowed":
        # delivery happened; settled immediately when escrow off
        return "settled" if (eh == 0 or er > 0) else "delivered"
    return str(st or "unfilled")


def _listed_quality(cfg: Dict, model: str) -> Dict:
    acc = cfg.get("models", {}).get(model, {}).get("accuracy", {})
    return {str(k): float(v) for k, v in acc.items()}


def build_sellers_rows(cfg: Dict, metrics: Dict, run_id: str, seed: int) -> List[Dict]:
    fcfg = fraud_cfg(cfg)
    stake_unit = float(fcfg.get("penalty", 0.0))
    stake0 = float(fcfg.get("stake", stake_unit * 20.0 if stake_unit else 0.0))
    q_swap = metrics.get("learned_swap_q") or {}
    q_theft = metrics.get("learned_theft_q") or {}
    # end-of-run ban map is not kept; use 0 (per-purchase ban_until is on audits/orders)
    rows = []
    for scfg in cfg["sellers"]:
        sid = scfg["id"]
        is_fraud = (scfg.get("claimed_model") != scfg.get("actual_model")) or bool(scfg.get("strategy"))
        latent_swap = float(q_swap.get(sid, fcfg.get("q_static", 1.0) if is_fraud else 0.0))
        latent_theft = float(q_theft.get(sid, fcfg.get("q_theft_static", 0.0) if is_fraud and "theft" in fcfg.get("attack_modes_enabled", []) else 0.0))
        # stake_remaining: synthetic pool minus cumulative slash attributed in this episode
        # (sim tracks total slash globally; attribute all to fraud seller for export clarity)
        slash = float(metrics.get("total_stake_slashed", 0.0)) if is_fraud else 0.0
        rows.append({
            "seller_id": sid,
            "jurisdiction": scfg["jurisdiction"],
            "claimed_model": scfg["claimed_model"],
            "actual_model": scfg["actual_model"],
            "listed_quality": _listed_quality(cfg, scfg["claimed_model"]),
            "latent_q_swap": latent_swap,
            "latent_q_theft": latent_theft,
            "list_price": float(scfg["price_per_1k"]),
            "capacity": int(scfg["capacity_per_round"]),
            "stake": stake0,
            "stake_remaining": max(0.0, stake0 - slash),
            "banned_until_round": 0,
            "run_id": run_id,
            "seed": int(seed),
        })
    return rows


def build_buyers_rows(cfg: Dict, records: List[Dict], policy: str, run_id: str, seed: int) -> List[Dict]:
    # last budget_remaining observed per buyer (sim logs after each line)
    rem: Dict[str, float] = {}
    for r in records:
        rem[r["buyer_id"]] = float(r.get("budget_remaining", rem.get(r["buyer_id"], 0.0)))
    rows = []
    for b in cfg["buyers"]:
        bid = b["id"]
        profile = {
            "allowed_jurisdictions": list(b.get("allowed_jurisdictions", [])),
            "sensitivity_mix": dict(b.get("sensitivity_mix", {})),
            "consent_rate": float(b.get("consent_rate", 0.0)),
        }
        rows.append({
            "buyer_id": bid,
            "jurisdiction": b["jurisdiction"],
            "budget_total": float(b["budget"]) * float(cfg.get("market", {}).get("budget_multiplier", 1.0)),
            "budget_remaining": float(rem.get(bid, float(b["budget"]))),
            "strategy_id": policy,
            "compliance_profile": profile,
            "run_id": run_id,
            "seed": int(seed),
        })
    return rows


def build_orders_rows(records: List[Dict], policy: str, chash: str) -> List[Dict]:
    out = []
    for i, r in enumerate(records):
        oid = _order_id(r, i)
        bj, sj = r.get("buyer_jurisdiction"), r.get("seller_jurisdiction")
        path = f"{bj}->{sj}" if bj and sj else (bj or "")
        ts = r.get("ts")
        out.append({
            "order_id": oid,
            "round": int(r.get("round", 0)),
            "t_submit": ts,
            "t_deliver": ts if r.get("status") == "allowed" else None,
            "t_settle": ts if r.get("status") == "allowed" else None,
            "buyer_id": r.get("buyer_id"),
            "seller_id": r.get("seller_id"),
            "task_id": r.get("task_id"),
            "portfolio_id": r.get("task_id"),  # one portfolio per task instance
            "tokens_billed": int(r.get("billed_tokens") or 0),
            "tokens_actual": int(r.get("actual_tokens") or r.get("reasoning_tokens") or 0),
            "price": float(r.get("price_per_1k") or 0.0),
            "amount_escrow": float(r.get("escrow_held") or 0.0),
            "amount_paid": float(r.get("actual_cost") or 0.0),
            "state": _order_state(r),
            "attack_mode": r.get("attack_mode") if r.get("status") == "allowed" else "none",
            "correct": r.get("correct"),
            "jurisdiction_path": path,
            "route_policy": policy,
            "run_id": r.get("run_id"),
            "seed": int(r.get("seed", 0)),
            "config_hash": chash,
        })
    return out


def build_audits_rows(records: List[Dict], metrics: Dict, cfg: Dict, policy: str) -> List[Dict]:
    _, fb_L, fb_pi = feedback_params(cfg)
    if fb_L is None or (isinstance(fb_L, float) and fb_L == float("inf")):
        L = None
    else:
        try:
            L = int(fb_L)
        except (TypeError, ValueError):
            L = None
    adaptive = bool(metrics.get("adaptive_audit"))
    a_rate = float(metrics.get("audit_rate") or 0.0)
    if a_rate <= 0:
        mode = "none"
    elif adaptive:
        mode = "adaptive"
    else:
        mode = "fixed"
    trail_by_pid = {t["purchase_id"]: t for t in (metrics.get("audit_trail") or []) if t.get("purchase_id")}
    rows = []
    for i, r in enumerate(records):
        if r.get("status") != "allowed":
            continue
        oid = _order_id(r, i)
        sampled = 1 if r.get("audited") else 0
        atype = r.get("audit_type") or "none"
        identity = 1 if sampled and atype in ("identity", "both") else 0
        length = 1 if sampled and atype in ("length", "both") else 0
        swap_hit = bool(r.get("swap_detected")) if sampled and identity else False
        theft_hit = bool(r.get("theft_detected")) if sampled and length else False
        hit = 1 if (swap_hit or theft_hit) else 0
        # miss: audited an attacked purchase but did not detect
        attacked = (r.get("attack_mode") or "none") not in ("none", None)
        miss = 1 if (sampled and attacked and not hit) else 0
        tr = trail_by_pid.get(r.get("purchase_id") or oid, {})
        slash = float(tr.get("slash", 0.0) if tr else 0.0)
        if slash == 0.0 and hit:
            # trail may be absent when escrow off but slash still applied via stake
            slash = float(fraud_cfg(cfg).get("penalty", 0.0)) if hit else 0.0
        ban = r.get("ban_until")
        delist = 0
        if ban is not None:
            delist = max(0, int(ban) - int(r.get("round", 0)) - 1)
        elif tr.get("ban_until") is not None:
            delist = max(0, int(tr["ban_until"]) - int(r.get("round", 0)) - 1)
        rows.append({
            "audit_id": f"audit|{oid}",
            "order_id": oid,
            "round": int(r.get("round", 0)),
            "mode": mode if sampled or a_rate > 0 else "none",
            "sampled": sampled,
            "identity_check": identity,
            "length_check": length,
            "hit": hit,
            "miss": miss,
            "slash_amount": slash if hit else 0.0,
            "delist_rounds": int(delist) if hit else 0,
            "auditor_cost": float(r.get("audit_cost") or 0.0),
            "label_revealed": 1 if r.get("feedback_revealed") else 0,
            "label_delay_L": L if L is not None else r.get("feedback_delay_L"),
            "reveal_pi": float(fb_pi),
            "label_correct": r.get("correct"),
            "fraud_realized": 1 if attacked else 0,
            "run_id": r.get("run_id"),
            "seed": int(r.get("seed", 0)),
        })
    return rows


def _served_attack_rate(records: Optional[Sequence[Dict]], metrics: Dict) -> float:
    """Active trade attack rate: attacked / served purchases (status=allowed).

    This is NOT epoch-mean learned q. When delist is on, this can diverge from
    learned_q_swap / learned_q_theft; without delist they may be close (esp. D3).
    Falls back to metrics['fraud_share'] when records are unavailable.
    """
    if records:
        served = [r for r in records if r.get("status") == "allowed"]
        if served:
            attacked = [r for r in served
                        if (r.get("attack_mode") or "none") not in ("none", None)]
            return float(len(attacked) / len(served))
    return float(metrics.get("fraud_share", 0.0))


def _learned_q_pair(metrics: Dict, cfg: Dict) -> Tuple[Optional[float], Optional[float]]:
    """Epoch-mean learned q for the strategic fraud seller (else mean over map)."""
    q_swap = metrics.get("learned_swap_q") or {}
    q_theft = metrics.get("learned_theft_q") or {}
    sid = None
    try:
        from .experiments import fraud_seller_id
        sid = fraud_seller_id(cfg)
    except Exception:
        sid = None
    if sid and sid in q_swap:
        qs = float(q_swap[sid])
    elif q_swap:
        qs = float(sum(q_swap.values()) / len(q_swap))
    else:
        qs = None
    if sid and sid in q_theft:
        qt = float(q_theft[sid])
    elif q_theft:
        qt = float(sum(q_theft.values()) / len(q_theft))
    else:
        qt = None
    return qs, qt


def build_episode_row(metrics: Dict, cfg: Dict, run_id: str, seed: int, chash: str,
                      records: Optional[Sequence[Dict]] = None) -> Dict:
    mkt = cfg.get("market", {})
    fb = mkt.get("feedback", {})
    aud = mkt.get("audited", {})
    # Primary board: active_attack_rate (served attack share) + fraud_share.
    # learned_q_* are separate columns (epoch-mean policy); do not alias into active_attack_rate.
    active = _served_attack_rate(records, metrics)
    qs, qt = _learned_q_pair(metrics, cfg)
    L = fb.get("delay_L", 0)
    if L is None or (isinstance(L, float) and L == float("inf")):
        L_out = None
    else:
        L_out = int(L)
    return {
        "run_id": run_id,
        "seed": int(seed),
        "a": float(metrics.get("audit_rate", aud.get("audit_rate", 0.0))),
        "pi": float(fb.get("reveal_prob", 1.0)),
        "L": L_out,
        "reputation_rounds": int(metrics.get("reputation_rounds", aud.get("reputation_rounds", 0))),
        "active_attack_rate": active,
        "learned_q_swap": qs,
        "learned_q_theft": qt,
        "fraud_share": float(metrics.get("fraud_share", 0.0)),
        "J": float(metrics.get("joint_objective", 0.0)),
        "n_audits": int(metrics.get("n_audits", 0)),
        "config_hash": chash,
    }



def build_labels_rows(sellers: List[Dict], orders: List[Dict]) -> List[Dict]:
    """Optional held-out labels for fraud-detection tasks (join on order_id).

    Default five-table export still contains these values for leaderboard convenience;
    trainers must not use them as features — prefer this file as the supervision join.
    """
    qmap = {
        s["seller_id"]: (
            float(s.get("latent_q_swap", 0.0)),
            float(s.get("latent_q_theft", 0.0)),
            s.get("actual_model"),
        )
        for s in sellers
    }
    rows = []
    for o in orders:
        sid = o.get("seller_id")
        qs, qt, am = qmap.get(sid, (None, None, None)) if sid else (None, None, None)
        rows.append({
            "order_id": o["order_id"],
            "attack_mode": o.get("attack_mode"),
            "correct": o.get("correct"),
            "actual_model": am,
            "latent_q_swap": qs,
            "latent_q_theft": qt,
            "run_id": o.get("run_id"),
            "seed": int(o.get("seed", 0)),
        })
    return rows


class _MemLog:
    def __init__(self):
        self.records: List[Dict] = []

    def write(self, rec: Dict) -> None:
        errs = validate_record(rec)
        if errs:
            raise ValueError(f"invalid transaction record: {errs}")
        self.records.append(rec)


def run_export_episode(cfg: Dict, policy: str, seed: int, n_tasks: Optional[int] = None,
                       mechanism: str = "posted_price") -> Tuple[Dict, List[Dict], Dict]:
    """Run one mock episode and return (metrics, records, layers_dict)."""
    chash = config_hash(cfg)
    rep = Reputation(cfg["models"], {})
    lg = _MemLog()
    pool = build_task_pool(cfg)
    backends = {"mock": MockLLM(cfg["market"].get("mock_confidence"))}
    metrics = run_single(cfg, mechanism, policy, seed, backends, rep, lg, pool, n_tasks, "mock")
    run_id = f"{mechanism}__{policy}__seed{seed}"
    layers = {
        "sellers": build_sellers_rows(cfg, metrics, run_id, seed),
        "buyers": build_buyers_rows(cfg, lg.records, policy, run_id, seed),
        "orders": build_orders_rows(lg.records, policy, chash),
        "audits": build_audits_rows(lg.records, metrics, cfg, policy),
        "episodes": [build_episode_row(metrics, cfg, run_id, seed, chash, records=lg.records)],
    }
    return metrics, lg.records, layers


def write_layers(out_dir: str, layers: Dict[str, List[Dict]]) -> Dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for key, fname in LAYER_FILES.items():
        path = os.path.join(out_dir, fname)
        write_jsonl(path, layers.get(key, []))
        paths[key] = path
    return paths


def export_benchmark(cfg: Dict, out_dir: str, policy: str = "audited_compliance_cascade",
                     seed: int = 0, n_tasks: Optional[int] = 48,
                     knobs_path: Optional[str] = None,
                     with_labels: bool = False) -> Dict:
    """One-click: run mock episode, write five JSONL layers (+ optional knobs / labels)."""
    metrics, records, layers = run_export_episode(cfg, policy, seed, n_tasks=n_tasks)
    paths = write_layers(out_dir, layers)
    labels_path = None
    if with_labels:
        labels = build_labels_rows(layers["sellers"], layers["orders"])
        labels_path = os.path.join(out_dir, "labels.jsonl")
        write_jsonl(labels_path, labels)
        paths["labels"] = labels_path
    knobs = export_knobs(cfg)
    if knobs_path:
        os.makedirs(os.path.dirname(knobs_path) or ".", exist_ok=True)
        with open(knobs_path, "w", encoding="utf-8") as fh:
            yaml.safe_dump(knobs, fh, sort_keys=False, allow_unicode=True)
    return {
        "out_dir": out_dir,
        "paths": paths,
        "n_orders": len(layers["orders"]),
        "n_audits": len(layers["audits"]),
        "n_sellers": len(layers["sellers"]),
        "n_buyers": len(layers["buyers"]),
        "episode": layers["episodes"][0],
        "knobs": knobs,
        "knobs_path": knobs_path,
        "labels_path": labels_path,
        "metrics_summary": {
            "fraud_share": metrics.get("fraud_share"),
            "joint_objective": metrics.get("joint_objective"),
            "n_audits": metrics.get("n_audits"),
            "learned_swap_q": metrics.get("learned_swap_q"),
        },
    }
