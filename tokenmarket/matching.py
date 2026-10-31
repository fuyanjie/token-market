"""Matching mechanisms: posted price and sealed-bid (reverse) scoring auction, plus the candidate filter.

v2: compliance is a HARD constraint for *_compliant policies (infeasible sellers are removed before any
purchase, never just penalised); compliance_unaware_cheapest skips that filter.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

MECHANISMS = ("posted_price", "sealed_bid")


@dataclass
class Candidates:
    sellers: List
    filtered: int = 0                                   # sellers removed by the hard compliance filter
    filtered_by_rule: Dict[str, int] = field(default_factory=dict)
    reason: Optional[str] = None                        # MKT-* reason when empty


def candidate_sellers(buyer, sellers, task, hard_compliance: bool, precheck: Callable) -> Candidates:
    """Buyer preference (allowed_jurisdictions) and capacity always apply; compliance rules apply only if
    hard_compliance (precheck = side-effect-free rule-engine evaluation)."""
    cands = [s for s in sellers if s.jurisdiction in buyer.allowed_jurisdictions]
    if not cands:
        return Candidates([], reason="MKT-NO-ALLOWED-JURISDICTION")
    cands = [s for s in cands if s.has_capacity()]
    if not cands:
        return Candidates([], reason="MKT-NO-CAPACITY")
    out = Candidates(cands)
    if hard_compliance:
        keep = []
        for s in cands:
            d = precheck(buyer, s, task)
            if d.allowed:
                keep.append(s)
            else:
                out.filtered += 1
                out.filtered_by_rule[d.rule_id] = out.filtered_by_rule.get(d.rule_id, 0) + 1
        out.sellers = keep
        if not keep:
            out.reason = "MKT-NO-COMPLIANT-SELLER"
    return out


def run_auction(bids: Sequence[Tuple[str, float, float]], fmt: str = "second_price",
                reserve: Optional[float] = None) -> Optional[Tuple[str, float]]:
    """Procurement (reverse) sealed-bid scoring auction.

    bids: (seller_id, bid_price_per_1k, quality_weight); score = bid / quality (lower wins;
    quality=1 gives a pure price auction). Bids above `reserve` are rejected.
    first_price: winner is paid its own bid.
    second_price: winner is paid the price at which its score ties the runner-up
                  (= second_score * winner_quality), capped at reserve; a sole bidder gets the reserve
                  (or its own bid if no reserve).
    Returns (winner_id, clearing_price_per_1k) or None.
    """
    valid = [b for b in bids if reserve is None or b[1] <= reserve]
    if not valid:
        return None
    valid = [(i, b, max(q, 1e-6)) for i, b, q in valid]   # zero-quality guard
    ranked = sorted(valid, key=lambda b: (b[1] / b[2], b[0]))
    wid, wbid, wq = ranked[0]
    if fmt == "first_price":
        return wid, wbid
    if fmt != "second_price":
        raise ValueError(f"unknown auction format {fmt}")
    if len(ranked) == 1:
        return wid, reserve if reserve is not None else wbid
    _, b2, q2 = ranked[1]
    price = (b2 / q2) * wq
    if reserve is not None:
        price = min(price, reserve)
    return wid, price


def sealed_bid_select(cands: List, quality: Callable, rng: random.Random,
                      auction_cfg: Dict) -> Optional[Tuple[object, float]]:
    """Run the auction among candidate sellers. quality(seller) -> scoring weight (1.0 = price only)."""
    by_id = {s.id: s for s in cands}
    bids = [(s.id, s.sample_bid(rng, auction_cfg["markup_low"], auction_cfg["markup_high"]), quality(s))
            for s in sorted(cands, key=lambda s: s.id)]
    res = run_auction(bids, auction_cfg.get("format", "second_price"), auction_cfg.get("reserve_price_per_1k"))
    if res is None:
        return None
    return by_id[res[0]], res[1]
