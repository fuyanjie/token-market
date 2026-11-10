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
# v1.0: + selective downgrade (serve the cheap model ONLY on hard tasks, difficulty >= downgrade_min_difficulty).
# A purchase is never both swapped and downgraded (a swap draw wins), so the modes stay disjoint.
ATTACK_MODES = ("none", "swap", "theft", "both", "downgrade", "downgrade+theft")
THEFT_MODES = ("theft", "both", "downgrade+theft")
SWAP_MODES = ("swap", "both")
DOWNGRADE_MODES = ("downgrade", "downgrade+theft")
LEARNERS = ("egreedy", "hedge", "exp3", "fictitious_play")
AUDIT_TYPES = ("none", "identity", "length", "both")
_CELLS = ((False, False), (True, False), (False, True), (True, True))   # (swap, theft) per purchase
# v1.0 learning cells (swap, theft, downgrade); the downgrade=False half is _CELLS in the same order
_CELLS3 = tuple((sw, th, False) for sw, th in _CELLS) + tuple((sw, th, True) for sw, th in _CELLS if not sw)


def attack_mode(swapped: bool, theft: bool, downgraded: bool = False) -> str:
    if downgraded and not swapped:
        return "downgrade+theft" if theft else "downgrade"
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
    learner: str = "egreedy"          # learning: egreedy (default) | hedge | exp3 | fictitious_play (v1.0)
    eta: float = 1.0                  # learning (hedge): step size on profit normalised by `scale`
    epsilon: float = 0.1              # learning: uniform exploration over the grid
    scale: float = 0.01               # learning: typical per-purchase revenue (normalises rewards)
    # v4 attack modes
    swap_enabled: bool = True
    theft_enabled: bool = False
    q_theft_static: float = 1.0
    theft_saving: float = 0.0         # expected theft gain per purchase before penalties (analytic / logit)
    detect_prob_length: float = 0.9   # length audit d_length (0 if the buyers' audits do not include it)
    # v1.0 selective downgrade: serve the cheap model with prob q_downgrade, only on tasks with
    # difficulty >= downgrade_min_difficulty (detected by the identity check like a swap)
    downgrade_enabled: bool = False
    downgrade_min_difficulty: int = 3
    q_downgrade_static: float = 1.0
    exp3_gamma: float = 0.1           # learning (exp3): uniform mixing / step size
    fp_temperature: float = 0.1       # learning (fictitious_play): logit smoothing, in units of `scale`
    q: float = 1.0
    q_theft: float = 0.0
    q_downgrade: float = 0.0
    history: List[float] = field(default_factory=list)         # q_swap played per epoch
    history_theft: List[float] = field(default_factory=list)   # q_theft played per epoch
    history_downgrade: List[float] = field(default_factory=list)   # v1.0: q_downgrade played per epoch
    # learning state: realised profit sums / counts per (swapped, theft, downgraded) cell
    _sum: Dict[Tuple[bool, bool, bool], float] = field(default_factory=dict)
    _n: Dict[Tuple[bool, bool, bool], int] = field(default_factory=dict)
    _ep_n: Dict[Tuple[bool, bool, bool], int] = field(default_factory=dict)
    _logw: List[float] = field(default_factory=list)
    _pairs: List[Tuple[float, float, float]] = field(default_factory=list)
    _n_hard: int = 0                  # v1.0: purchases on downgrade-eligible (hard) tasks
    _n_all: int = 0
    _arm: Optional[int] = None        # exp3: arm played this epoch and its probability
    _arm_p: float = 1.0
    _ep_profit: float = 0.0
    _ep_count: int = 0

    def __post_init__(self):
        if self.kind not in STRATEGIES:
            raise ValueError(f"unknown attack strategy {self.kind}")
        if self.learner not in LEARNERS:
            raise ValueError(f"unknown seller learner {self.learner}")
        gs = list(self.grid) if self.swap_enabled else [0.0]
        gt = list(self.grid) if self.theft_enabled else [0.0]
        gd = list(self.grid) if self.downgrade_enabled else [0.0]
        self._pairs = [(qs, qt, qd) for qs in gs for qt in gt for qd in gd]
        self._logw = [0.0] * len(self._pairs)
        self._sum = {c: 0.0 for c in _CELLS3}
        self._n = {c: 0 for c in _CELLS3}
        self._ep_n = {c: 0 for c in _CELLS3}
        if self.kind == "static":
            self._set_static()
        else:
            self.q = 0.5 if self.swap_enabled else 0.0
            self.q_theft = 0.5 if self.theft_enabled else 0.0
            self.q_downgrade = 0.5 if self.downgrade_enabled else 0.0

    def _set_static(self):
        self.q = self.q_static if self.swap_enabled else 0.0
        self.q_theft = self.q_theft_static if self.theft_enabled else 0.0
        self.q_downgrade = self.q_downgrade_static if self.downgrade_enabled else 0.0

    def _set(self, arm: Tuple[float, float, float]):
        self.q, self.q_theft, self.q_downgrade = arm

    def can_downgrade(self, difficulty) -> bool:
        return self.downgrade_enabled and int(difficulty) >= self.downgrade_min_difficulty

    def note_task(self, difficulty) -> None:
        """v1.0: track the share of this seller's purchases that are downgrade-eligible (hard)."""
        if self.downgrade_enabled:
            self._n_all += 1
            self._n_hard += int(int(difficulty) >= self.downgrade_min_difficulty)

    @property
    def hard_share(self) -> float:
        return self._n_hard / self._n_all if self._n_all else 0.5

    # ---------------------------------------------------------------- analytic quantities
    def gain(self) -> float:
        return swap_gain(self.cost_saving, self.audit_rate, self.detect_prob, self.penalty, self.reputation_loss)

    def gain_theft(self) -> float:
        return swap_gain(self.theft_saving, self.audit_rate, self.detect_prob_length, self.penalty,
                         self.reputation_loss)

    def gain_downgrade(self) -> float:
        """Per downgrade-eligible purchase: same saving / detection as a swap (identity check)."""
        return self.gain()

    def _cells(self):
        return [c for c in _CELLS3 if (self.swap_enabled or not c[0]) and (self.theft_enabled or not c[1])
                and (self.downgrade_enabled or not c[2])]

    def mean_profit(self, swapped: bool, theft: bool = False, downgraded: bool = False) -> Optional[float]:
        c = (bool(swapped), bool(theft), bool(downgraded))
        return self._sum[c] / self._n[c] if self._n[c] else None

    def _reward(self, qs: float, qt: float, means: Dict, qd: float = 0.0) -> float:
        """Estimated per-purchase profit of playing (qs, qt[, qd]): multilinear in the attack probabilities.
        A downgrade happens only on a hard task the seller did not swap, so its effective weight is
        (1 - qs) * hard_share * qd (exactly 0 when downgrade is disabled: then this is the v4 bilinear reward)."""
        hd = self.hard_share * qd if qd else 0.0
        r = 0.0
        for (sw, th, dg) in _CELLS3:
            if dg:
                w = (1 - qs) * hd * (qt if th else 1 - qt)
            else:
                w = (qs if sw else 1 - qs) * (qt if th else 1 - qt)
                if hd and not sw:
                    w *= 1 - hd
            if w:
                r += w * means[(sw, th, dg)]
        return r

    def _arm_reward(self, p, means) -> float:
        return self._reward(p[0], p[1], means, p[2])

    # ---------------------------------------------------------------- epochs
    def start_epoch(self, rng: random.Random) -> float:
        """Choose (q_swap, q_theft, q_downgrade) for the next epoch (round); returns q_swap."""
        if self.kind == "static":
            self._set_static()
        elif self.kind == "analytic":
            self.q = (1.0 if self.gain() > 0 else 0.0) if self.swap_enabled else 0.0
            self.q_theft = (1.0 if self.gain_theft() > 0 else 0.0) if self.theft_enabled else 0.0
            self.q_downgrade = (1.0 if self.gain_downgrade() > 0 else 0.0) if self.downgrade_enabled else 0.0
        elif self.kind == "logit":
            self.q = logit_response(self.gain(), self.temperature) if self.swap_enabled else 0.0
            self.q_theft = logit_response(self.gain_theft(), self.temperature) if self.theft_enabled else 0.0
            self.q_downgrade = logit_response(self.gain_downgrade(), self.temperature) \
                if self.downgrade_enabled else 0.0
        elif self.learner == "egreedy":
            # epsilon-greedy over the (q_swap, q_theft[, q_downgrade]) grid: exploit the grid point with the highest
            # estimated per-purchase profit r(q) from the seller's own realised profits per attack cell
            self._ep_n = {c: 0 for c in _CELLS3}
            means = {c: self.mean_profit(*c) for c in self._cells()}
            if any(v is None for v in means.values()) or rng.random() < self.epsilon:
                self._set(rng.choice(self._pairs))
            else:
                self._set(max(self._pairs, key=lambda p: (self._arm_reward(p, means), -abs(p[0] - 0.5),
                                                          -abs(p[1] - 0.5), -abs(p[2] - 0.5))))
        elif self.learner == "exp3":
            self._exp3_epoch(rng)
        elif self.learner == "fictitious_play":
            self._fp_epoch()
        else:
            self._learn_update()
            if rng.random() < self.epsilon:
                self._set(rng.choice(self._pairs))
            else:
                m = max(self._logw)
                w = [math.exp(x - m) for x in self._logw]
                self._set(rng.choices(self._pairs, weights=w, k=1)[0])
        self.history.append(self.q)
        self.history_theft.append(self.q_theft)
        self.history_downgrade.append(self.q_downgrade)
        return self.q

    # ---------------------------------------------------------------- v1.0 alternative learning rules
    def _exp3_reward(self) -> float:
        """Epoch reward in [0, 1]: mean realised per-purchase profit of the epoch, normalised by the typical
        revenue `scale` and the stake penalty, r = clip(0.5 + 0.5 * profit / R, 0, 1), R = max(scale, penalty)."""
        x = self._ep_profit / self._ep_count
        r_scale = max(self.scale, self.penalty, 1e-12)
        return min(1.0, max(0.0, 0.5 + 0.5 * x / r_scale))

    def _exp3_epoch(self, rng: random.Random) -> None:
        """EXP3 (Auer et al. 2002) over the grid of attack-probability tuples: BANDIT feedback - only the arm
        played in the last epoch is updated, with the importance-weighted epoch reward. Epochs without a
        served purchase give no feedback (no update)."""
        k, g = len(self._pairs), self.exp3_gamma
        if self._arm is not None and self._ep_count > 0:
            self._logw[self._arm] += g * (self._exp3_reward() / self._arm_p) / k
        self._ep_profit, self._ep_count = 0.0, 0
        m = max(self._logw)
        w = [math.exp(x - m) for x in self._logw]
        tot = sum(w)
        probs = [(1 - g) * wi / tot + g / k for wi in w]
        i = rng.choices(range(k), weights=probs, k=1)[0]
        self._arm, self._arm_p = i, probs[i]
        self._set(self._pairs[i])

    def _fp_epoch(self) -> None:
        """Smooth fictitious play (Fudenberg & Kreps 1993): the seller best-responds to the EMPIRICAL behaviour
        of the buyers (their realised audit / catch frequency is embedded in its running mean profit per
        attack cell, penalties included). For each enabled mode the marginal gain is
            gain_m = r(q with q_m = 1) - r(q with q_m = 0)   (r = estimated per-purchase profit, others fixed)
        and q_m = sigmoid(gain_m / (fp_temperature * scale)). No exploration noise; until every enabled cell has
        been observed the seller keeps its current mixed strategy (0.5 at start)."""
        means = {c: self.mean_profit(*c) for c in self._cells()}
        if any(v is None for v in means.values()):
            return
        cur = [self.q, self.q_theft, self.q_downgrade]
        new = list(cur)
        tau = max(self.fp_temperature * self.scale, 1e-12)
        for j, on in enumerate((self.swap_enabled, self.theft_enabled, self.downgrade_enabled)):
            if not on:
                continue
            hi, lo = list(cur), list(cur)
            hi[j], lo[j] = 1.0, 0.0
            new[j] = logit_response(self._arm_reward(hi, means) - self._arm_reward(lo, means), tau)
        self._set(tuple(new))

    def _learn_update(self) -> None:
        """Full-information Hedge over the grid (fictitious-play style). Expected per-purchase profit is bilinear in
        (q_swap, q_theft), so the seller's running means of its OWN realised profits per attack cell (including
        stake actually slashed) give an estimated reward for every grid point. Using all-history means (not just
        this epoch's) keeps the estimate consistent despite rare, large penalties."""
        if not any(self._ep_n.values()):
            return
        self._ep_n = {c: 0 for c in _CELLS3}
        means = {c: self.mean_profit(*c) for c in self._cells()}
        if any(v is None for v in means.values()):
            return
        for i, p in enumerate(self._pairs):
            self._logw[i] += self.eta * self._arm_reward(p, means) / max(self.scale, 1e-12)

    def observe(self, swapped: bool, profit: float, theft: bool = False, downgraded: bool = False) -> None:
        """Realised profit of one purchase (revenue on billed tokens - serving cost of the served model on actual
        tokens - penalty if caught)."""
        c = (bool(swapped), bool(theft), bool(downgraded) and not swapped)
        self._sum[c] += profit
        self._n[c] += 1
        self._ep_n[c] += 1
        self._ep_profit += profit
        self._ep_count += 1

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

    def learned_q_downgrade(self, tail: float = 0.5) -> float:
        return self._tail(self.history_downgrade, tail, self.q_downgrade)

    def enabled_modes(self) -> List[str]:
        return [m for m, on in (("swap", self.swap_enabled), ("theft", self.theft_enabled),
                                ("downgrade", self.downgrade_enabled)) if on]


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
    # v1.0: a seller may override the global attack modes (strategy.attack_modes) and downgrade threshold
    modes = list(st["attack_modes"]) if "attack_modes" in st else attack_modes_enabled(cfg)
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
                          detect_prob_length=float(f.get("detect_prob_length", 0.9)) if "length" in checks else 0.0,
                          downgrade_enabled="downgrade" in modes,
                          downgrade_min_difficulty=int(st.get("downgrade_min_difficulty",
                                                              f.get("downgrade_min_difficulty", 3))),
                          q_downgrade_static=float(f.get("q_downgrade_static", 1.0)),
                          exp3_gamma=float(lrn.get("exp3_gamma", 0.1)),
                          fp_temperature=float(lrn.get("fp_temperature", 0.1)))


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
