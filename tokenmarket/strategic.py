"""v3 / C: STRATEGIC model-swap seller and buyer-side audits (links C2 portfolio purchasing to B2 fraud detection).

A model-swap seller claims model H (e.g. Qwen2.5-1.5B) but can serve the cheaper model L (Qwen2.5-0.5B).
Each round (= epoch) it chooses a swap probability q in [0, 1]; every purchase is then served by L with
probability q (actual_model = L) and by H otherwise (actual_model = H, honest).

Buyers audit a fraction a (audit_rate) of purchases, paying audit_cost per audit (charged to the buyer budget).
An audit of a swapped answer detects the swap with probability d (detect_prob). The detector is SIMULATED as an
identity check that succeeds with probability d (stand-in for TEE attestation / fingerprinting, see
IdentityCheckDetector); an audit of an honest answer never raises a false positive. When caught, the seller
forfeits penalty P from its stake (slashed; NOT refunded to the buyer - conservative for the buyer) and,
optionally, is delisted for `reputation_rounds` rounds (loses all demand).

Per-purchase expected gain of swapping (analytic, risk-neutral, same token count assumed):
    gain = cost_saving - a * d * P - a * d * R,      cost_saving = cost_gap_per_1k * E[tokens] / 1000
where R = profit lost while delisted. Best response q* = 1 if gain > 0 else 0, i.e. the deterrence
threshold is  a* = cost_saving / (d * (P + R)).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

STRATEGIES = ("static", "analytic", "logit", "learning")


def swap_gain(cost_saving: float, audit_rate: float, detect_prob: float, penalty: float,
              reputation_loss: float = 0.0) -> float:
    """Expected per-purchase gain of swapping vs serving honestly."""
    return cost_saving - audit_rate * detect_prob * (penalty + reputation_loss)


def analytic_threshold(cost_saving: float, detect_prob: float, penalty: float, reputation_loss: float = 0.0) -> float:
    """Minimum audit rate a* at which swapping stops being profitable (inf if detection/penalty is zero)."""
    denom = detect_prob * (penalty + reputation_loss)
    return math.inf if denom <= 0 else cost_saving / denom


def best_response(cost_saving, audit_rate, detect_prob, penalty, reputation_loss=0.0) -> float:
    return 1.0 if swap_gain(cost_saving, audit_rate, detect_prob, penalty, reputation_loss) > 0 else 0.0


def logit_response(gain: float, temperature: float) -> float:
    """Smooth (quantal) best response q = sigmoid(gain / temperature)."""
    z = max(-60.0, min(60.0, gain / max(temperature, 1e-12)))
    return 1.0 / (1.0 + math.exp(-z))


class IdentityCheckDetector:
    """SIMULATED model-identity audit: detects a swapped answer with probability d; honest answers never flagged.
    TODO(B1): replace with a real signal (TEE attestation quote, output fingerprint / watermark)."""

    def __init__(self, detect_prob: float):
        self.d = float(detect_prob)

    def detect(self, swapped: bool, rng: random.Random, **_) -> bool:
        return bool(swapped) and rng.random() < self.d


class TokenFingerprintDetector(IdentityCheckDetector):
    """STUB of a real-signal detector: would compare the answer's token count / accuracy against the claimed
    model's fingerprint distribution. Not calibrated - falls back to the simulated identity check."""


@dataclass
class SwapStrategy:
    """Swap-probability policy of one model-swap seller. Uses only information a seller has: its own
    realised per-purchase profits (learning) or the announced audit regime (analytic / logit)."""
    kind: str = "static"
    q_static: float = 1.0
    cost_saving: float = 0.0          # expected saving per purchase (used by analytic / logit)
    audit_rate: float = 0.0           # announced buyer audit rate (analytic / logit only)
    detect_prob: float = 0.9
    penalty: float = 0.0
    reputation_loss: float = 0.0
    temperature: float = 0.002        # logit
    grid: List[float] = field(default_factory=lambda: [i / 10 for i in range(11)])
    learner: str = "egreedy"          # learning: egreedy (default) | hedge
    eta: float = 1.0                  # learning (hedge): step size on profit normalised by `scale`
    epsilon: float = 0.1              # learning: uniform exploration over the grid
    scale: float = 0.01               # learning: typical per-purchase revenue (normalises rewards)
    q: float = 1.0
    history: List[float] = field(default_factory=list)   # q played per epoch
    # learning state: realised profit sums / counts of swapped vs honest purchases
    _sum: Dict[bool, float] = field(default_factory=lambda: {True: 0.0, False: 0.0})
    _n: Dict[bool, int] = field(default_factory=lambda: {True: 0, False: 0})
    _ep_sum: Dict[bool, float] = field(default_factory=lambda: {True: 0.0, False: 0.0})
    _ep_n: Dict[bool, int] = field(default_factory=lambda: {True: 0, False: 0})
    _logw: List[float] = field(default_factory=list)

    def __post_init__(self):
        if self.kind not in STRATEGIES:
            raise ValueError(f"unknown swap strategy {self.kind}")
        self._logw = [0.0] * len(self.grid)
        self.q = self.q_static if self.kind == "static" else 0.5

    def gain(self) -> float:
        return swap_gain(self.cost_saving, self.audit_rate, self.detect_prob, self.penalty, self.reputation_loss)

    def mean_profit(self, swapped: bool) -> Optional[float]:
        return self._sum[swapped] / self._n[swapped] if self._n[swapped] else None

    def start_epoch(self, rng: random.Random) -> float:
        """Choose q for the next epoch (round)."""
        if self.kind == "static":
            self.q = self.q_static
        elif self.kind == "analytic":
            self.q = 1.0 if self.gain() > 0 else 0.0
        elif self.kind == "logit":
            self.q = logit_response(self.gain(), self.temperature)
        elif self.learner == "egreedy":
            # epsilon-greedy over the q-grid: exploit the grid point with the highest estimated per-purchase
            # profit r(q) = (1-q)*pi_honest + q*pi_swap from the seller's own realised profits
            self._ep_sum, self._ep_n = {True: 0.0, False: 0.0}, {True: 0, False: 0}
            ps, ph = self.mean_profit(True), self.mean_profit(False)
            if ps is None or ph is None or rng.random() < self.epsilon:
                self.q = rng.choice(self.grid)
            else:
                self.q = max(self.grid, key=lambda q: ((1 - q) * ph + q * ps, -abs(q - 0.5)))
        else:
            self._learn_update()
            if rng.random() < self.epsilon:
                self.q = rng.choice(self.grid)
            else:
                m = max(self._logw)
                w = [math.exp(x - m) for x in self._logw]
                self.q = rng.choices(self.grid, weights=w, k=1)[0]
        self.history.append(self.q)
        return self.q

    def _learn_update(self) -> None:
        """Full-information Hedge over the q-grid (fictitious-play style). Expected per-purchase profit is linear
        in q, so the seller's running means of its OWN realised profits of swapped / honest purchases (including
        stake actually slashed) give an estimated reward for every grid point:
            r(q) = (1 - q) * pi_honest + q * pi_swap.
        Using all-history means (not just this epoch's) keeps the estimate consistent despite rare, large
        penalties."""
        if not any(self._ep_n.values()):
            return
        self._ep_sum, self._ep_n = {True: 0.0, False: 0.0}, {True: 0, False: 0}
        ps, ph = self.mean_profit(True), self.mean_profit(False)
        if ps is None or ph is None:
            return
        for i, q in enumerate(self.grid):
            self._logw[i] += self.eta * ((1 - q) * ph + q * ps) / max(self.scale, 1e-12)

    def observe(self, swapped: bool, profit: float) -> None:
        """Realised profit of one purchase (revenue - serving cost of served model - penalty if caught)."""
        self._sum[swapped] += profit
        self._n[swapped] += 1
        self._ep_sum[swapped] += profit
        self._ep_n[swapped] += 1

    def learned_q(self, tail: float = 0.5) -> float:
        """Mean q played over the last `tail` fraction of epochs (empirical learned swap rate)."""
        if not self.history:
            return self.q
        k = max(1, int(round(len(self.history) * tail)))
        return sum(self.history[-k:]) / k


def fraud_cfg(cfg: Dict) -> Dict:
    return cfg.get("fraud", {})


def make_strategy(seller_cfg: Dict, cfg: Dict, audit_rate: float, rep=None) -> Optional[SwapStrategy]:
    """SwapStrategy for a model-swap seller (claimed != actual), else None."""
    if seller_cfg["claimed_model"] == seller_cfg["actual_model"]:
        return None
    f = fraud_cfg(cfg)
    st = dict(seller_cfg.get("strategy", {}))
    kind = str(f.get("strategy", st.get("kind", "static")))
    honest_cost = float(st.get("honest_cost_per_1k", seller_cfg["cost_per_1k"]))
    cost_gap = float(f.get("cost_gap_per_1k", honest_cost - float(seller_cfg["cost_per_1k"])))
    tokens = rep.tokens_mean(seller_cfg["claimed_model"]) if rep is not None else \
        float(cfg["models"][seller_cfg["claimed_model"]]["tokens_mean"])
    lrn = f.get("learning", {})
    return SwapStrategy(kind=kind, q_static=float(f.get("q_static", 1.0)),
                        cost_saving=cost_gap * tokens / 1000.0, audit_rate=float(audit_rate),
                        detect_prob=float(f.get("detect_prob", 0.9)), penalty=float(f.get("penalty", 0.0)),
                        reputation_loss=float(f.get("reputation_loss", 0.0)),
                        temperature=float(f.get("logit_temperature", 0.002)),
                        learner=str(lrn.get("learner", "egreedy")),
                        eta=float(lrn.get("eta", 1.0)), epsilon=float(lrn.get("epsilon", 0.1)),
                        scale=float(seller_cfg["price_per_1k"]) * tokens / 1000.0)


class TrustModel:
    """D3 buyer-side per-seller trust from audit outcomes. Estimated swap rate
        q_hat = (detected + prior_a) / (audits * d + prior_a + prior_b)    (Beta-style smoothing, clipped)
    Once an audit has revealed that seller s serves model L instead of its claimed model H, the routing quality
    becomes (1 - q_hat) * rep(H) + q_hat * rep(L) (downgrade from claimed to estimated actual)."""

    def __init__(self, rep, detect_prob: float, prior_a: float = 0.0, prior_b: float = 1.0):
        self.rep = rep
        self.d = max(float(detect_prob), 1e-9)
        self.pa, self.pb = prior_a, prior_b
        self.audits: Dict[str, int] = {}
        self.detected: Dict[str, int] = {}
        self.revealed: Dict[str, str] = {}      # seller id -> actual model revealed by a detected audit

    def record(self, seller_id: str, detected: bool, served_model: Optional[str]) -> None:
        self.audits[seller_id] = self.audits.get(seller_id, 0) + 1
        if detected:
            self.detected[seller_id] = self.detected.get(seller_id, 0) + 1
            self.revealed[seller_id] = served_model

    def q_hat(self, seller_id: str) -> float:
        n = self.audits.get(seller_id, 0)
        k = self.detected.get(seller_id, 0)
        return min(1.0, (k + self.pa) / (n * self.d + self.pa + self.pb))

    def quality(self, seller, difficulty: int) -> float:
        claimed = self.rep.accuracy(seller.claimed_model, difficulty)
        if seller.id not in self.revealed:
            return claimed
        q = self.q_hat(seller.id)
        return (1 - q) * claimed + q * self.rep.accuracy(self.revealed[seller.id], difficulty)
