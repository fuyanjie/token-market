"""v3 / C + v4: STRATEGIC fraud seller (model swap AND token theft) and buyer-side audits under IMPERFECT detection.

Model swap (v3). A model-swap seller claims model H (e.g. Qwen2.5-1.5B) but can serve the cheaper model L
(Qwen2.5-0.5B). Each round (= epoch) it chooses a swap probability q in [0, 1]; every purchase is then served by L
with probability q (actual_model = L) and by H otherwise (actual_model = H, honest).

Token theft (v4). The same seller can also claim a long, high-effort generation and bill for it
(billed_tokens = the claimed model's advertised mean tokens, or an inflated factor x the full length) while
actually generating only `theft_max_new_tokens` tokens (early truncation). Revenue is computed on BILLED tokens,
serving cost on ACTUAL generated tokens. Per purchase the seller plays one of four attack modes
{none, swap, theft, both}: swap ~ Bernoulli(q_swap) and theft ~ Bernoulli(q_theft) independently.

Audits. Buyers audit a fraction a (audit_rate) of purchases, paying audit_cost per audited purchase (charged to
the buyer budget). An audit runs the checks of the buyer's audit regime (`identity`, `length` or both):
  * IdentityCheckDetector: detects a swapped answer with probability d (= detect_prob, identity).
    Miss rate / FALSE-NEGATIVE rate = 1 - d. False-positive rate = 0 (an honest answer is never flagged).
  * TokenLengthAuditor: flags theft when billed_tokens > actual_tokens * (1 + tol) (or billed - actual > abs_gap),
    with probability d_length (miss rate 1 - d_length; false positives 0 when compared to actual tokens).
    Optional reference cross-check: compare billed tokens with the claimed model's cached (greedy) reference
    generation for the same prompt (a real signal; can produce false positives on swapped answers).
Both detectors are SIMULATED (stand-ins for TEE attestation / fingerprinting / metered inference) unless the
reference cross-check is used. When caught by either check, the seller forfeits penalty P from its stake once per
purchase (slashed; NOT refunded to the buyer - conservative for the buyer) and, optionally, is delisted for
`reputation_rounds` rounds (loses all demand).

Per-purchase expected gain (analytic, risk-neutral, treating the two attacks independently):
    swap:  gain = cost_saving  - a * d        * (P + R),  cost_saving  = cost_gap_per_1k * E[tokens] / 1000
    theft: gain = theft_saving - a * d_length * (P + R),  theft_saving = (price * E[billed - full]
                                                                        + cost * E[full - actual]) / 1000
R = profit lost while delisted. Best response = 1 if gain > 0 else 0, i.e. the deterrence thresholds are
    a*(d) = cost_saving / (d * (P + R))     and     a*_theft(d_length) = theft_saving / (d_length * (P + R)).
"""
from __future__ import annotations

import itertools
import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

STRATEGIES = ("static", "analytic", "logit", "learning")
ATTACK_MODES = ("none", "swap", "theft", "both")
AUDIT_TYPES = ("none", "identity", "length", "both")
_CELLS = ((False, False), (True, False), (False, True), (True, True))   # (swap, theft) per purchase


def attack_mode(swapped: bool, theft: bool) -> str:
    return ATTACK_MODES[int(bool(swapped)) + 2 * int(bool(theft))]


def audit_type(checks) -> str:
    c = set(checks)
    if not c:
        return "none"
    return "both" if c >= {"identity", "length"} else next(iter(c))


def swap_gain(cost_saving: float, audit_rate: float, detect_prob: float, penalty: float,
              reputation_loss: float = 0.0) -> float:
    """Expected per-purchase gain of swapping vs serving honestly (also used for theft with theft_saving and
    d_length)."""
    return cost_saving - audit_rate * detect_prob * (penalty + reputation_loss)


theft_gain = swap_gain


def analytic_threshold(cost_saving: float, detect_prob: float, penalty: float, reputation_loss: float = 0.0) -> float:
    """Minimum audit rate a*(d) at which the attack stops being profitable (inf if detection/penalty is zero).
    Decreasing in the detection probability d: a miss rate 1 - d inflates the required audit rate by 1/d."""
    denom = detect_prob * (penalty + reputation_loss)
    return math.inf if denom <= 0 else cost_saving / denom


def best_response(cost_saving, audit_rate, detect_prob, penalty, reputation_loss=0.0) -> float:
    return 1.0 if swap_gain(cost_saving, audit_rate, detect_prob, penalty, reputation_loss) > 0 else 0.0


def logit_response(gain: float, temperature: float) -> float:
    """Smooth (quantal) best response q = sigmoid(gain / temperature)."""
    z = max(-60.0, min(60.0, gain / max(temperature, 1e-12)))
    return 1.0 / (1.0 + math.exp(-z))


class IdentityCheckDetector:
    """SIMULATED model-identity audit with IMPERFECT detection.
    * detects a swapped answer with probability d = detect_prob;
    * miss rate = FALSE-NEGATIVE rate = 1 - d (a swapped answer passes the audit);
    * false-positive rate = 0 by construction (an honest answer is never flagged).
    TODO(B1): replace with a real signal (TEE attestation quote, output fingerprint / watermark)."""

    def __init__(self, detect_prob: float):
        self.d = float(detect_prob)

    @property
    def miss_rate(self) -> float:
        """False-negative rate 1 - d."""
        return 1.0 - self.d

    false_positive_rate = 0.0

    def detect(self, swapped: bool, rng: random.Random, **_) -> bool:
        return bool(swapped) and rng.random() < self.d


class TokenFingerprintDetector(IdentityCheckDetector):
    """STUB of a real-signal detector: would compare the answer's token count / accuracy against the claimed
    model's fingerprint distribution. Not calibrated - falls back to the simulated identity check."""


class TokenLengthAuditor:
    """v4 length / reasoning-token audit against token theft (billing for tokens that were not generated).
    Signal: billed_tokens > actual_tokens * (1 + tol) or billed_tokens - actual_tokens > abs_gap (abs_gap <= 0
    disables the absolute rule). The auditor observes the signal with probability d = detect_prob_length:
    miss rate (false negative) = 1 - d_length, false positives = 0 for honest billing (billed == actual).
    SIMULATED: real buyers usually cannot see hidden reasoning tokens; this stands in for metered inference /
    TEE token counters. With `reference` (the claimed model's cached greedy generation length for the same prompt)
    the signal becomes billed > reference * (1 + tol): a REAL cross-check on cached outputs, which can flag
    honest-billed swapped answers that are longer than the claimed model's reference (false positives)."""

    def __init__(self, detect_prob: float, tol: float = 0.1, abs_gap: float = 0.0):
        self.d, self.tol, self.abs_gap = float(detect_prob), float(tol), float(abs_gap)

    @property
    def miss_rate(self) -> float:
        return 1.0 - self.d

    def overbilled(self, billed: int, actual: int, reference: Optional[int] = None) -> bool:
        base = actual if reference is None else reference
        if billed > base * (1.0 + self.tol):
            return True
        return self.abs_gap > 0 and billed - base > self.abs_gap

    def detect(self, billed: int, actual: int, rng: random.Random, reference: Optional[int] = None) -> bool:
        return self.overbilled(billed, actual, reference) and rng.random() < self.d


@dataclass
class AttackStrategy:
    """v4 attack policy of one strategic fraud seller: per epoch it picks (q_swap, q_theft) on a grid; per purchase
    swap ~ Bernoulli(q_swap), theft ~ Bernoulli(q_theft) -> attack mode none | swap | theft | both. Uses only
    information a seller has: its own realised per-purchase profits (learning) or the announced audit regime
    (analytic / logit). With theft disabled it reduces EXACTLY to the v3 SwapStrategy (same random draws)."""
    kind: str = "static"
    q_static: float = 1.0
    cost_saving: float = 0.0          # expected swap saving per purchase (used by analytic / logit)
    audit_rate: float = 0.0           # announced buyer audit rate (analytic / logit only)
    detect_prob: float = 0.9          # identity check d (0 if the buyers' audits do not include it)
    penalty: float = 0.0
    reputation_loss: float = 0.0
    temperature: float = 0.002        # logit
    grid: List[float] = field(default_factory=lambda: [i / 10 for i in range(11)])
    learner: str = "egreedy"          # learning: egreedy (default) | hedge
    eta: float = 1.0                  # learning (hedge): step size on profit normalised by `scale`
    epsilon: float = 0.1              # learning: uniform exploration over the grid
    scale: float = 0.01               # learning: typical per-purchase revenue (normalises rewards)
    # v4 attack modes
    swap_enabled: bool = True
    theft_enabled: bool = False
    q_theft_static: float = 1.0
    theft_saving: float = 0.0         # expected theft gain per purchase before penalties (analytic / logit)
    detect_prob_length: float = 0.9   # length audit d_length (0 if the buyers' audits do not include it)
    q: float = 1.0
    q_theft: float = 0.0
    history: List[float] = field(default_factory=list)         # q_swap played per epoch
    history_theft: List[float] = field(default_factory=list)   # q_theft played per epoch
    # learning state: realised profit sums / counts per (swapped, theft) cell
    _sum: Dict[Tuple[bool, bool], float] = field(default_factory=dict)
    _n: Dict[Tuple[bool, bool], int] = field(default_factory=dict)
    _ep_n: Dict[Tuple[bool, bool], int] = field(default_factory=dict)
    _logw: List[float] = field(default_factory=list)
    _pairs: List[Tuple[float, float]] = field(default_factory=list)

    def __post_init__(self):
        if self.kind not in STRATEGIES:
            raise ValueError(f"unknown attack strategy {self.kind}")
        gs = list(self.grid) if self.swap_enabled else [0.0]
        gt = list(self.grid) if self.theft_enabled else [0.0]
        self._pairs = [(qs, qt) for qs in gs for qt in gt]
        self._logw = [0.0] * len(self._pairs)
        self._sum = {c: 0.0 for c in _CELLS}
        self._n = {c: 0 for c in _CELLS}
        self._ep_n = {c: 0 for c in _CELLS}
        if self.kind == "static":
            self.q = self.q_static if self.swap_enabled else 0.0
            self.q_theft = self.q_theft_static if self.theft_enabled else 0.0
        else:
            self.q = 0.5 if self.swap_enabled else 0.0
            self.q_theft = 0.5 if self.theft_enabled else 0.0

    # ---------------------------------------------------------------- analytic quantities
    def gain(self) -> float:
        return swap_gain(self.cost_saving, self.audit_rate, self.detect_prob, self.penalty, self.reputation_loss)

    def gain_theft(self) -> float:
        return swap_gain(self.theft_saving, self.audit_rate, self.detect_prob_length, self.penalty,
                         self.reputation_loss)

    def _cells(self):
        return [c for c in _CELLS if (self.swap_enabled or not c[0]) and (self.theft_enabled or not c[1])]

    def mean_profit(self, swapped: bool, theft: bool = False) -> Optional[float]:
        c = (bool(swapped), bool(theft))
        return self._sum[c] / self._n[c] if self._n[c] else None

    def _reward(self, qs: float, qt: float, means: Dict) -> float:
        """Estimated per-purchase profit of playing (qs, qt): bilinear in (qs, qt)."""
        r = 0.0
        for (sw, th) in _CELLS:
            w = (qs if sw else 1 - qs) * (qt if th else 1 - qt)
            if w:
                r += w * means[(sw, th)]
        return r

    # ---------------------------------------------------------------- epochs
    def start_epoch(self, rng: random.Random) -> float:
        """Choose (q_swap, q_theft) for the next epoch (round); returns q_swap."""
        if self.kind == "static":
            self.q = self.q_static if self.swap_enabled else 0.0
            self.q_theft = self.q_theft_static if self.theft_enabled else 0.0
        elif self.kind == "analytic":
            self.q = (1.0 if self.gain() > 0 else 0.0) if self.swap_enabled else 0.0
            self.q_theft = (1.0 if self.gain_theft() > 0 else 0.0) if self.theft_enabled else 0.0
        elif self.kind == "logit":
            self.q = logit_response(self.gain(), self.temperature) if self.swap_enabled else 0.0
            self.q_theft = logit_response(self.gain_theft(), self.temperature) if self.theft_enabled else 0.0
        elif self.learner == "egreedy":
            # epsilon-greedy over the (q_swap, q_theft) grid: exploit the grid point with the highest estimated
            # per-purchase profit r(q) from the seller's own realised profits per attack cell
            self._ep_n = {c: 0 for c in _CELLS}
            means = {c: self.mean_profit(*c) for c in self._cells()}
            if any(v is None for v in means.values()) or rng.random() < self.epsilon:
                self.q, self.q_theft = rng.choice(self._pairs)
            else:
                self.q, self.q_theft = max(self._pairs, key=lambda p: (self._reward(p[0], p[1], means),
                                                                       -abs(p[0] - 0.5), -abs(p[1] - 0.5)))
        else:
            self._learn_update()
            if rng.random() < self.epsilon:
                self.q, self.q_theft = rng.choice(self._pairs)
            else:
                m = max(self._logw)
                w = [math.exp(x - m) for x in self._logw]
                self.q, self.q_theft = rng.choices(self._pairs, weights=w, k=1)[0]
        self.history.append(self.q)
        self.history_theft.append(self.q_theft)
        return self.q

    def _learn_update(self) -> None:
        """Full-information Hedge over the grid (fictitious-play style). Expected per-purchase profit is bilinear in
        (q_swap, q_theft), so the seller's running means of its OWN realised profits per attack cell (including
        stake actually slashed) give an estimated reward for every grid point. Using all-history means (not just
        this epoch's) keeps the estimate consistent despite rare, large penalties."""
        if not any(self._ep_n.values()):
            return
        self._ep_n = {c: 0 for c in _CELLS}
        means = {c: self.mean_profit(*c) for c in self._cells()}
        if any(v is None for v in means.values()):
            return
        for i, (qs, qt) in enumerate(self._pairs):
            self._logw[i] += self.eta * self._reward(qs, qt, means) / max(self.scale, 1e-12)

    def observe(self, swapped: bool, profit: float, theft: bool = False) -> None:
        """Realised profit of one purchase (revenue on billed tokens - serving cost of the served model on actual
        tokens - penalty if caught)."""
        c = (bool(swapped), bool(theft))
        self._sum[c] += profit
        self._n[c] += 1
        self._ep_n[c] += 1

    @staticmethod
    def _tail(h: List[float], tail: float, default: float) -> float:
        if not h:
            return default
        k = max(1, int(round(len(h) * tail)))
        return sum(h[-k:]) / k

    def learned_q(self, tail: float = 0.5) -> float:
        """Mean q_swap played over the last `tail` fraction of epochs (empirical learned swap rate)."""
        return self._tail(self.history, tail, self.q)

    def learned_q_theft(self, tail: float = 0.5) -> float:
        return self._tail(self.history_theft, tail, self.q_theft)


@dataclass
class SwapStrategy(AttackStrategy):
    """v3 swap-only strategy (back-compat thin wrapper): AttackStrategy with theft disabled."""

    def __post_init__(self):
        self.theft_enabled = False
        super().__post_init__()


def fraud_cfg(cfg: Dict) -> Dict:
    return cfg.get("fraud", {})


def attack_modes_enabled(cfg: Dict) -> List[str]:
    return list(fraud_cfg(cfg).get("attack_modes_enabled", ["swap"]))


def billed_tokens(policy: str, actual: int, full: int, claimed_mean: float, factor: float) -> int:
    """Tokens a THEFT purchase is billed for (never fewer than actually generated)."""
    if policy == "claimed_mean":
        b = int(round(claimed_mean))
    elif policy == "inflated_factor":
        b = int(round(factor * full))
    else:
        raise ValueError(f"unknown billed_token_policy {policy}")
    return max(int(actual), b)


def expected_theft_saving(cfg: Dict, seller_cfg: Dict, tokens: float) -> float:
    """Analytic per-purchase theft gain before penalties for an honest-model purchase:
    (price * E[billed - full] + honest_cost * E[full - actual]) / 1000 with full ~ claimed-model mean tokens."""
    f = fraud_cfg(cfg)
    price = float(seller_cfg["price_per_1k"])
    cost = float(seller_cfg.get("strategy", {}).get("honest_cost_per_1k", seller_cfg["cost_per_1k"]))
    tmax = f.get("theft_max_new_tokens")
    actual = tokens if tmax is None else min(tokens, float(tmax))
    billed = max(actual, billed_tokens(str(f.get("billed_token_policy", "claimed_mean")), int(actual), int(tokens),
                                       tokens, float(f.get("inflated_factor", 2.0))))
    return (price * (billed - tokens) + cost * (tokens - actual)) / 1000.0


def make_strategy(seller_cfg: Dict, cfg: Dict, audit_rate: float, rep=None,
                  audit_checks=("identity",)) -> Optional[AttackStrategy]:
    """AttackStrategy for a fraud-capable seller (claimed != actual), else None. `audit_checks` = the buyers'
    audit regime; the announced detection probability of a check the buyers do not run is 0 (analytic / logit)."""
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
    modes = attack_modes_enabled(cfg)
    checks = set(audit_checks)
    return AttackStrategy(kind=kind, q_static=float(f.get("q_static", 1.0)),
                          cost_saving=cost_gap * tokens / 1000.0, audit_rate=float(audit_rate),
                          detect_prob=float(f.get("detect_prob", 0.9)) if "identity" in checks else 0.0,
                          penalty=float(f.get("penalty", 0.0)),
                          reputation_loss=float(f.get("reputation_loss", 0.0)),
                          temperature=float(f.get("logit_temperature", 0.002)),
                          learner=str(lrn.get("learner", "egreedy")),
                          eta=float(lrn.get("eta", 1.0)), epsilon=float(lrn.get("epsilon", 0.1)),
                          scale=float(seller_cfg["price_per_1k"]) * tokens / 1000.0,
                          swap_enabled="swap" in modes, theft_enabled="theft" in modes,
                          q_theft_static=float(f.get("q_theft_static", 1.0)),
                          theft_saving=expected_theft_saving(cfg, seller_cfg, tokens),
                          detect_prob_length=float(f.get("detect_prob_length", 0.9)) if "length" in checks else 0.0)


class TrustModel:
    """D3 buyer-side per-seller trust from audit outcomes. Estimated swap rate
        q_hat = (detected + prior_a) / (audits * d + prior_a + prior_b)    (Beta-style smoothing, clipped)
    Once an audit has revealed that seller s serves model L instead of its claimed model H, the routing quality
    becomes (1 - q_hat) * rep(H) + q_hat * rep(L) (downgrade from claimed to estimated actual).
    v4: length audits give an analogous theft-rate estimate q_hat_theft (with d_length); once theft has been
    revealed the quality is further scaled by (1 - q_hat_theft * (1 - theft_quality_factor)) - the buyer's prior
    that a truncated answer is `theft_quality_factor` times as likely to be correct."""

    def __init__(self, rep, detect_prob: float, prior_a: float = 0.0, prior_b: float = 1.0,
                 detect_prob_length: float = 0.9, theft_quality_factor: float = 0.5):
        self.rep = rep
        self.d = max(float(detect_prob), 1e-9)
        self.d_len = max(float(detect_prob_length), 1e-9)
        self.theft_factor = float(theft_quality_factor)
        self.pa, self.pb = prior_a, prior_b
        self.audits: Dict[str, int] = {}
        self.detected: Dict[str, int] = {}
        self.revealed: Dict[str, str] = {}      # seller id -> actual model revealed by a detected audit
        self.length_audits: Dict[str, int] = {}
        self.theft_detected: Dict[str, int] = {}

    def record(self, seller_id: str, detected: bool, served_model: Optional[str]) -> None:
        self.audits[seller_id] = self.audits.get(seller_id, 0) + 1
        if detected:
            self.detected[seller_id] = self.detected.get(seller_id, 0) + 1
            self.revealed[seller_id] = served_model

    def record_length(self, seller_id: str, detected: bool) -> None:
        self.length_audits[seller_id] = self.length_audits.get(seller_id, 0) + 1
        if detected:
            self.theft_detected[seller_id] = self.theft_detected.get(seller_id, 0) + 1

    def q_hat(self, seller_id: str) -> float:
        n = self.audits.get(seller_id, 0)
        k = self.detected.get(seller_id, 0)
        return min(1.0, (k + self.pa) / (n * self.d + self.pa + self.pb))

    def q_hat_theft(self, seller_id: str) -> float:
        n = self.length_audits.get(seller_id, 0)
        k = self.theft_detected.get(seller_id, 0)
        return min(1.0, (k + self.pa) / (n * self.d_len + self.pa + self.pb))

    def quality(self, seller, difficulty: int) -> float:
        claimed = self.rep.accuracy(seller.claimed_model, difficulty)
        if seller.id in self.revealed:
            q = self.q_hat(seller.id)
            claimed = (1 - q) * claimed + q * self.rep.accuracy(self.revealed[seller.id], difficulty)
        if self.theft_detected.get(seller.id, 0):
            claimed *= 1 - self.q_hat_theft(seller.id) * (1 - self.theft_factor)
        return claimed
