"""Matching mechanisms: fixed posted price with routing policies, and sealed-bid (reverse) auction."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

POLICIES = ("cheapest", "quality_per_cost", "compliance_aware")
MECHANISMS = ("posted_price", "sealed_bid")


@dataclass
class Match:
    seller: object
    price_per_1k: float
    reason: Optional[str] = None     # set when no seller could be matched


def _score(seller, price: float, policy: str) -> float:
    """Lower is better. Buyers only observe ADVERTISED quality (claimed model), not actual."""
    if policy == "cheapest":
        return price
    return price / max(seller.advertised_accuracy, 1e-9)


def candidate_sellers(buyer, sellers, task, policy: str, precheck: Callable) -> Tuple[List, Optional[str]]:
    cands = [s for s in sellers if s.jurisdiction in buyer.allowed_jurisdictions]
    if not cands:
        return [], "MKT-NO-ALLOWED-JURISDICTION"
    cands = [s for s in cands if s.has_capacity()]
    if not cands:
        return [], "MKT-NO-CAPACITY"
    if policy == "compliance_aware":
        cands = [s for s in cands if precheck(buyer, s, task).allowed]
        if not cands:
            return [], "MKT-NO-COMPLIANT-SELLER"
    return cands, None


def posted_price(buyer, sellers, task, policy: str, precheck: Callable) -> Match:
    cands, reason = candidate_sellers(buyer, sellers, task, policy, precheck)
    if not cands:
        return Match(None, 0.0, reason)
    best = min(cands, key=lambda s: (_score(s, s.price_per_1k, policy), s.id))
    return Match(best, best.price_per_1k)


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


def sealed_bid(buyer, sellers, task, policy: str, precheck: Callable, rng: random.Random,
               auction_cfg: Dict) -> Match:
    cands, reason = candidate_sellers(buyer, sellers, task, policy, precheck)
    if not cands:
        return Match(None, 0.0, reason)
    by_id = {s.id: s for s in cands}
    bids = []
    for s in sorted(cands, key=lambda s: s.id):
        q = 1.0 if policy == "cheapest" else s.advertised_accuracy
        bids.append((s.id, s.sample_bid(rng, auction_cfg["markup_low"], auction_cfg["markup_high"]), q))
    res = run_auction(bids, auction_cfg.get("format", "second_price"), auction_cfg.get("reserve_price_per_1k"))
    if res is None:
        return Match(None, 0.0, "MKT-NO-BID-BELOW-RESERVE")
    return Match(by_id[res[0]], res[1])
