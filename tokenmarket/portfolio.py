"""C2: compliance-constrained multi-model PORTFOLIO purchasing policies.

A policy decides, per task, which (compliant) sellers to buy answers from and how to combine them.
Policies only see what a buyer can see: posted / clearing prices, the CLAIMED model's public reputation
(estimated quality, advertised expected tokens) and the seller's per-answer confidence signal. They never see
the actual model, so a model-swap seller fools quality-based routing (C2 <-> B2).

Every policy works through a `buy(seller, price_per_1k, step) -> Purchase | None` callback supplied by the
simulator, which performs the budget check (expected cost), the gateway call and logging. `None` means the
purchase was not made because it would exceed the remaining budget.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

HARD_POLICIES = ("single_cheapest_compliant", "single_best_compliant", "cascade_compliant", "vote_k_compliant")
BASELINE_POLICIES = ("compliance_unaware_cheapest",)
POLICIES = HARD_POLICIES + BASELINE_POLICIES
SINGLE_POLICIES = ("single_cheapest_compliant", "single_best_compliant", "compliance_unaware_cheapest")


def is_hard(policy: str) -> bool:
    if policy not in POLICIES:
        raise ValueError(f"unknown policy {policy}")
    return policy in HARD_POLICIES


@dataclass
class Purchase:
    seller: object
    answer: Optional[int]
    confidence: Optional[float]
    quality: float              # buyer's estimated quality of this seller (claimed-model reputation)
    served: bool = True         # False if blocked at the gateway


@dataclass
class Decision:
    final_answer: Optional[int]
    purchases: List[Purchase]
    stop_reason: str            # confident | exhausted | budget | single | vote | no_purchase


def majority_vote(purchases: Sequence[Purchase]) -> Optional[int]:
    """Majority over served, parsed answers. Tie -> the tied answer backed by the highest estimated-quality
    seller (earliest purchase on equal quality)."""
    votes = [p for p in purchases if p.served and p.answer is not None]
    if not votes:
        return None
    counts = Counter(p.answer for p in votes)
    top = max(counts.values())
    tied = {a for a, c in counts.items() if c == top}
    if len(tied) == 1:
        return next(iter(tied))
    best = None
    for p in votes:  # first max wins -> earliest purchase among equal quality
        if p.answer in tied and (best is None or p.quality > best.quality):
            best = p
    return best.answer


def run_policy(policy: str, cands: List, price: Callable, exp_cost: Callable, quality: Callable,
               buy: Callable, cfg_market: dict) -> Decision:
    """cands: compliant (or, for the baseline, all) candidate sellers. price(s) -> price_per_1k,
    exp_cost(s) -> expected cost, quality(s) -> estimated quality."""
    by_cost = sorted(cands, key=lambda s: (exp_cost(s), -quality(s), s.id))

    if policy in ("single_cheapest_compliant", "compliance_unaware_cheapest", "single_best_compliant"):
        s = by_cost[0] if policy != "single_best_compliant" else \
            sorted(cands, key=lambda s: (-quality(s), exp_cost(s), s.id))[0]
        p = buy(s, price(s), 0)
        if p is None:
            return Decision(None, [], "budget")
        return Decision(p.answer if p.served else None, [p], "single")

    if policy == "cascade_compliant":
        c = cfg_market.get("cascade", {})
        thr = float(c.get("confidence_threshold", 0.7))
        max_steps = int(c.get("max_steps", 3))
        bought: List[Purchase] = []
        cur = by_cost[0]
        reason = "exhausted"
        while cur is not None and len(bought) < max_steps:
            p = buy(cur, price(cur), len(bought))
            if p is None:
                reason = "budget"
                break
            bought.append(p)
            if p.served and p.answer is not None and (p.confidence or 0.0) >= thr:
                reason = "confident"
                break
            # escalate: cheapest not-yet-bought seller whose estimated quality >= the current one's
            used = {b.seller.id for b in bought}
            nxt = [s for s in by_cost if s.id not in used and quality(s) >= quality(cur)]
            cur = nxt[0] if nxt else None
        if not bought:
            return Decision(None, [], "budget")
        served = [b for b in bought if b.served and b.answer is not None]
        if reason == "confident":
            final = bought[-1].answer
        elif served:  # no confident answer: highest confidence, later (stronger) purchase on ties
            final = max(enumerate(served), key=lambda ib: ((ib[1].confidence or 0.0), ib[0]))[1].answer
        else:
            final = None
        return Decision(final, bought, reason)

    if policy == "vote_k_compliant":
        k = int(cfg_market.get("vote", {}).get("k", 3))
        order = sorted(cands, key=lambda s: (-quality(s), exp_cost(s), s.id))[:k]
        bought = []
        reason = "vote"
        for s in order:
            p = buy(s, price(s), len(bought))
            if p is None:
                reason = "budget"
                continue          # a cheaper later seller may still fit the budget
            bought.append(p)
        if not bought:
            return Decision(None, [], "budget")
        return Decision(majority_vote(bought), bought, reason)

    raise ValueError(f"unknown policy {policy}")
