"""v1.0 per-run metrics (docs/PROTOCOL_v1.0.md §1 + 口径补正 2026-11-10, items 1, 2, 7).

E      - buyer exposure, main column = fraud_share = attacked served purchases / served purchases (per PURCHASE; the
         v0.1 metric in metrics.py, kept for the regression baseline; 口径补正 7).
E_tok  - secondary column = billed tokens of attacked served purchases / billed tokens of all served purchases
         (also emitted by metrics.run_metrics as `E_tok`).
Q      - seller intent. For every strategic seller and every attack mode it has enabled, q_mode = UNWEIGHTED mean of
         the attack probability it played in the last quarter of rounds, over rounds where it was PRESENT (not
         suspended / delisted); columns Q_swap / Q_theft / Q_downgrade (q_swap, q_theft, q_downgrade) = mean over the strategic sellers with that mode
         enabled; Q = simple mean of the available per-mode values (口径补正 1). No token weighting anywhere.
         Delisted tail rounds and the q played in them are reported separately and never enter Q.
tail_trade - (口径补正 2) the run had >= 1 served purchase from a strategic seller in the last `tail_trade_rounds`
         (= 12) rounds; tail_trade_rate (per π x method, in scripts/run_v1.py) = fraction of runs with tail_trade.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .audit_v1 import mean_or_none, present_rounds
from .strategic import DOWNGRADE_MODES, SWAP_MODES, THEFT_MODES

MODES = ("swap", "theft", "downgrade")
_HIST = {"swap": "swap_q_history", "theft": "theft_q_history", "downgrade": "downgrade_q_history"}


def is_attack(r: Dict) -> bool:
    return (r.get("attack_mode") or "none") != "none"


def exposure(records: List[Dict]) -> Dict:
    served = [r for r in records if r.get("status") == "allowed"]
    tok = sum(int(r.get("billed_tokens") or 0) for r in served)
    att_tok = sum(int(r.get("billed_tokens") or 0) for r in served if is_attack(r))
    by_mode = {"swap": SWAP_MODES, "theft": THEFT_MODES, "downgrade": DOWNGRADE_MODES}
    out = {"E_tok": att_tok / tok if tok else 0.0,
           "fraud_share": sum(is_attack(r) for r in served) / len(served) if served else 0.0,
           "n_served": len(served), "billed_tokens_total": tok}
    for m, modes in by_mode.items():
        out[f"fraud_share_{m}"] = (sum(1 for r in served if r.get("attack_mode") in modes) / len(served)
                                   if served else 0.0)
    out["E"] = out["fraud_share"]
    return out


def intent(m: Dict, records: List[Dict], n_rounds: int, tail_frac: float = 0.25,
           tail_trade_rounds: int = 12) -> Dict:
    modes = m.get("strategic_modes") or {}
    banned = m.get("strategic_delisted_rounds") or {}
    trade_from = n_rounds - min(int(tail_trade_rounds), n_rounds)
    tail_sales = [r["seller_id"] for r in records
                  if r.get("status") == "allowed" and r.get("seller_id") in modes and int(r["round"]) >= trade_from]
    tail_sellers = set(tail_sales)
    per_mode: Dict[str, List[float]] = {k: [] for k in MODES}
    per_mode_del: Dict[str, List[float]] = {k: [] for k in MODES}
    n_del = n_present = 0
    del_q = []
    for sid, ms in sorted(modes.items()):
        hist = {mode: list((m.get(_HIST[mode]) or {}).get(sid, [])) for mode in ms}
        _, present, delisted = present_rounds(n_rounds, banned.get(sid, []), tail_frac)
        present = [r for r in present if all(r < len(h) for h in hist.values())]
        n_present += len(present)
        n_del += len(delisted)
        for mode in ms:
            v = mean_or_none(hist[mode][r] for r in present)
            if v is not None:
                per_mode[mode].append(v)
            vd = mean_or_none(hist[mode][r] for r in delisted if r < len(hist[mode]))
            if vd is not None:
                per_mode_del[mode].append(vd)
        for r in delisted:
            if all(r < len(h) for h in hist.values()):
                del_q.append(sum(hist[mode][r] for mode in ms) / len(ms))
    q = {f"Q_{k}": mean_or_none(v) for k, v in per_mode.items()}
    avail = [v for v in q.values() if v is not None]
    return {"Q": mean_or_none(avail), **q,
            "tail_trade": bool(tail_sellers), "tail_trade_sellers": len(tail_sellers),
            "tail_sales": len(tail_sales),
            "n_strategic": len(modes), "Q_present_rounds": n_present, "delisted_rounds_tail": n_del,
            "q_delisted_mean": mean_or_none(del_q),
            **{f"q_delisted_{k}": mean_or_none(v) for k, v in per_mode_del.items()}}
