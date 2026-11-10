"""v6 market-mechanism helpers: adaptive audit allocation, escrow settlement, audit trail.

Claim framing: deterrence lowers seller attack rate q* via audits; adaptive audit is a
cost-reduction improvement under a FIXED expected audit budget (same mean spend as rate a).
Escrow holds seller payout until the audit decision; feedback delay L (labels) is separate.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


def d3_reputation_rounds(cfg: Dict, policy: str, audited_policies) -> int:
    """Rounds of delisting after a catch. D3 reads market.audited.reputation_rounds (falls back to
    fraud.reputation_rounds); every other policy uses fraud.reputation_rounds only."""
    f = int(cfg.get("fraud", {}).get("reputation_rounds", 0))
    if policy in audited_policies:
        return int(cfg.get("market", {}).get("audited", {}).get("reputation_rounds", f))
    return f


def d3_adaptive_audit(cfg: Dict, policy: str, audited_policies) -> bool:
    if policy not in audited_policies:
        return False
    return bool(cfg.get("market", {}).get("audited", {}).get("adaptive_audit", False))


def d3_escrow(cfg: Dict, policy: str, audited_policies) -> bool:
    if policy not in audited_policies:
        return False
    return bool(cfg.get("market", {}).get("audited", {}).get("escrow", False))


@dataclass
class AdaptiveAuditAllocator:
    """Allocate a fixed expected audit budget (≈ rate · N purchases) preferentially to high-risk sellers.

    Online approximation of 'audit top-scoring purchases until budget is used; leftover → random':
    each purchase adds `rate` credit; when credit ≥ 1 we spend on this purchase if its risk score is
    in the upper tail of recent scores, otherwise with a small random leftover probability; if credit
    piles up (≥ 1.5) we force-spend so the long-run audit count tracks rate · N.
    """
    rate: float
    rng: random.Random
    credit: float = 0.0
    n_audits: int = 0
    n_purchases: int = 0
    recent_scores: List[float] = field(default_factory=list)
    detect_counts: Dict[str, int] = field(default_factory=dict)
    audit_counts: Dict[str, int] = field(default_factory=dict)
    inflation_ema: Dict[str, float] = field(default_factory=dict)
    window: int = 64
    leftover_p: float = 0.15

    def score(self, seller_id: str, trust, billed: int, actual: int) -> float:
        q = float(trust.q_hat(seller_id)) if trust is not None else 0.0
        qt = float(trust.q_hat_theft(seller_id)) if trust is not None else 0.0
        infl = (billed / actual) if actual else 1.0
        prev = self.inflation_ema.get(seller_id, 1.0)
        ema = 0.7 * prev + 0.3 * infl
        self.inflation_ema[seller_id] = ema
        det = self.detect_counts.get(seller_id, 0)
        aud = max(1, self.audit_counts.get(seller_id, 0))
        return q + qt + max(0.0, ema - 1.0) + det / aud

    def decide(self, seller_id: str, risk: float) -> bool:
        self.n_purchases += 1
        self.credit += self.rate
        self.recent_scores.append(float(risk))
        if len(self.recent_scores) > self.window:
            self.recent_scores.pop(0)
        if self.credit < 1.0:
            return False
        # Upper-tail threshold: audit if score is among the top ~max(rate, 0.2) recent scores
        xs = sorted(self.recent_scores)
        frac = max(self.rate, 0.2)
        idx = max(0, int(round((1.0 - frac) * (len(xs) - 1))))
        thresh = xs[idx]
        spend = False
        if risk >= thresh - 1e-12:
            spend = True
        elif self.credit >= 1.5:          # leftover budget: force spend
            spend = True
        elif self.rng.random() < self.leftover_p:
            spend = True
        if spend:
            self.credit -= 1.0
            self.n_audits += 1
            return True
        return False

    def note_outcome(self, seller_id: str, detected_any: bool) -> None:
        self.audit_counts[seller_id] = self.audit_counts.get(seller_id, 0) + 1
        if detected_any:
            self.detect_counts[seller_id] = self.detect_counts.get(seller_id, 0) + 1


@dataclass
class EscrowBook:
    """Hold seller payout until audit decision; slash from escrow then release remainder."""
    held: float = 0.0
    released: float = 0.0
    slashed: float = 0.0
    pending: List[Dict] = field(default_factory=list)  # unresolved holds (should be empty online)

    def settle(self, seller_receives: float, audited: bool, slash_amount: float
               ) -> Tuple[float, float, float, float]:
        """Returns (escrow_held, escrow_released, escrow_slashed, seller_cash).

        Online path: every purchase is either selected for audit or not immediately, so we always
        resolve in the same call. Slash comes out of escrow first; remainder is released to seller.
        `seller_cash` is what the seller receives after slash (serving cost still subtracted outside).
        """
        held = float(seller_receives)
        if not audited:
            self.held += held
            self.released += held
            return held, held, 0.0, held
        slashed = min(max(0.0, float(slash_amount)), held)
        released = held - slashed
        self.held += held
        self.released += released
        self.slashed += slashed
        return held, released, slashed, released

    def flush_end(self) -> float:
        """Release any still-pending holds (none in the online Bernoulli/adaptive path)."""
        total = 0.0
        for p in self.pending:
            total += p.get("amount", 0.0)
            self.released += p.get("amount", 0.0)
        self.pending.clear()
        return total


def make_purchase_id(run_id: str, task_id: str, step: int, seller_id: str) -> str:
    return f"{run_id}|{task_id}|{step}|{seller_id}"


def audit_trail_record(purchase_id: str, seller_id: str, checks, swap_detected, theft_detected,
                       slash: float, ban_until: Optional[int], risk_score: Optional[float] = None,
                       adaptive: bool = False) -> Dict:
    return {
        "purchase_id": purchase_id,
        "seller_id": seller_id,
        "checks": list(checks),
        "swap_detected": swap_detected,
        "theft_detected": theft_detected,
        "slash": float(slash),
        "ban_until": ban_until,
        "risk_score": risk_score,
        "adaptive": bool(adaptive),
    }
