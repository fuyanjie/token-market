"""v1.0 audit rules for the audited cascade (D3 pipeline), selected by market.audited.audit_rule.

  fixed          (default, = v0.1) every purchase is audited with probability a = market.audited.audit_rate.
                 Labelled "fixed-rate audit reference baseline" in v1.0 tables (protocol §3).
  random         random-intensity audit: at the start of every round the audit probability is redrawn
                 a_t ~ U(0, 2a) (clipped to [0, 1]); every purchase in that round is audited w.p. a_t. Same expected
                 audit rate a as `fixed`, but the intensity is unannounced and varies round to round. Draws come
                 from their own RNG stream ("audit-rate-<seed>").
  risk_adaptive  the audit probability of a purchase from seller s increases with the buyers' POSTERIOR estimate of
                 s's attack rate:
                     q_hat_s = (k_s + a0) / (n_s * d_bar + a0 + b0)      (clipped to [0, 1])
                     a_s     = a_min + (a_max - a_min) * q_hat_s
                 n_s = audits of s so far, k_s = audits of s that caught an attack (identity OR length check),
                 d_bar = mean detection probability of the checks run (identity d, length d_length), Beta(a0, b0)
                 prior (default Beta(1, 9): prior attack rate 0.1, so an unaudited seller starts at
                 a_min + 0.1 (a_max - a_min)). The posterior uses ONLY audit outcomes the buyers observe.
                 Defaults a_min = 0.05, a_max = 0.5. No budget normalisation: the realised audit rate is reported
                 (n_audits) so cost can be compared with the fixed-rate baselines.
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional

AUDIT_RULES = ("fixed", "random", "risk_adaptive")


def audit_v11(cfg: Dict) -> Optional[Dict]:
    """Explicit opt-in; disabled/missing blocks leave all legacy paths unchanged."""
    block = cfg.get("market", {}).get("audit_v11", {})
    return block if block.get("enabled", False) else None


def trust_feedback_on(cfg: Dict, policy: str, audited_policies) -> bool:
    block = audit_v11(cfg)
    return bool(block.get("trust_feedback", False)) if block is not None else policy in audited_policies


def audit_rule(cfg: Dict, policy: str, audited_policies) -> str:
    block = audit_v11(cfg)
    if block is None and policy not in audited_policies:
        return "fixed"
    source = block if block is not None else cfg.get("market", {}).get("audited", {})
    rule = str(source.get("audit_rule", "fixed"))
    if rule not in AUDIT_RULES:
        raise ValueError(f"unknown audit_rule {rule}; choose from {AUDIT_RULES}")
    return rule


class RandomAuditRate:
    """Per-round audit probability a_t ~ U(0, 2a), clipped to [0, 1]."""

    def __init__(self, a: float, rng: random.Random):
        self.a, self.rng = float(a), rng
        self.current = float(a)
        self.history: List[float] = []

    def start_round(self) -> float:
        self.current = min(1.0, max(0.0, self.rng.uniform(0.0, 2.0 * self.a)))
        self.history.append(self.current)
        return self.current


class RiskAdaptiveAudit:
    """Audit probability a_s = a_min + (a_max - a_min) * q_hat_s with a Beta(a0, b0) posterior on the attack rate
    corrected for imperfect detection (see module docstring)."""

    def __init__(self, checks, detect_prob: float, detect_prob_length: float, a_min: float = 0.05,
                 a_max: float = 0.5, prior_a: float = 1.0, prior_b: float = 9.0):
        ds = [float(detect_prob)] if "identity" in checks else []
        ds += [float(detect_prob_length)] if "length" in checks else []
        self.d_bar = max(sum(ds) / len(ds), 1e-9) if ds else 1.0
        self.a_min, self.a_max = float(a_min), float(a_max)
        self.pa, self.pb = float(prior_a), float(prior_b)
        self.n: Dict[str, int] = {}
        self.k: Dict[str, int] = {}

    @classmethod
    def from_config(cls, cfg: Dict, checks, detect_prob: float, detect_prob_length: float) -> "RiskAdaptiveAudit":
        block = audit_v11(cfg)
        source = block if block is not None else cfg.get("market", {}).get("audited", {})
        r = source.get("risk_adaptive", {})
        return cls(checks, detect_prob, detect_prob_length, float(r.get("a_min", 0.05)), float(r.get("a_max", 0.5)),
                   float(r.get("prior_a", 1.0)), float(r.get("prior_b", 9.0)))

    def q_hat(self, seller_id: str) -> float:
        n, k = self.n.get(seller_id, 0), self.k.get(seller_id, 0)
        return min(1.0, max(0.0, (k + self.pa) / (n * self.d_bar + self.pa + self.pb)))

    def rate(self, seller_id: str) -> float:
        return min(1.0, max(0.0, self.a_min + (self.a_max - self.a_min) * self.q_hat(seller_id)))

    def record(self, seller_id: str, caught: bool) -> None:
        self.n[seller_id] = self.n.get(seller_id, 0) + 1
        if caught:
            self.k[seller_id] = self.k.get(seller_id, 0) + 1


def compliance_filter_on(cfg: Dict) -> bool:
    """A2 switch (protocol §6): market.compliance_filter (default true). false = every policy runs WITHOUT the hard
    compliance filter and through the gateway in market.unaware_gateway_mode (audit_only by default), so breaching
    flows go through and are counted as violations."""
    return bool(cfg.get("market", {}).get("compliance_filter", True))


def present_rounds(n_rounds: int, banned_rounds, tail_frac: float = 0.25):
    """Protocol §1 Q window: (tail rounds, rounds in the tail where the seller is listed, delisted tail rounds)."""
    k = max(1, int(n_rounds * tail_frac))
    tail = list(range(n_rounds - k, n_rounds))
    banned = set(banned_rounds)
    return tail, [r for r in tail if r not in banned], [r for r in tail if r in banned]


def mean_or_none(xs) -> Optional[float]:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None
