"""v5: delayed / sparse OUTCOME feedback for the online-learning buyers.

Outcome feedback = whether a purchased answer was correct (the PILOT / StageRoute bandit reward). In v2-v4 it was
immediate. Here every served purchase goes through a FeedbackBuffer:

  * the label of a purchase made at global step t (= task index of the run) is REVEALED with probability pi
    (reveal_prob; drawn on a dedicated RNG stream, so no other random draw changes), otherwise never;
  * a revealed label becomes due at step t + L (delay_L) and is delivered, FIFO by due step, either right after the
    purchase (L = 0) or at the start of task t + L, BEFORE the router chooses for that task;
  * labels still pending when the episode ends are flushed (delivered with their true labels) at step n_tasks if L
    is finite; with L = inf ("never") nothing is ever delivered.

Only the LABEL is delayed / dropped. What the buyer observes on its own bill - the realised cost of a purchase
(PILOT's budget-bin spend, StageRoute's cost estimate) - stays immediate. Audits (D3) are a SEPARATE signal: they
run, slash the seller and update D3's TrustModel immediately whatever the outcome-feedback regime is.

Config (market.feedback): {mode: immediate|delayed|sparse|delayed_sparse|never, delay_L: 0, reveal_prob: 1.0}.
  immediate      -> L = 0,        pi = 1      (default; reproduces v4 exactly)
  delayed        -> L = delay_L,  pi = 1      (delay_L null / "inf" -> never)
  sparse         -> L = 0,        pi = reveal_prob
  delayed_sparse -> L = delay_L,  pi = reveal_prob
  never          -> L = inf
"""
from __future__ import annotations

import heapq
import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

MODES = ("immediate", "delayed", "sparse", "delayed_sparse", "never")
INF = math.inf


def _as_delay(v) -> float:
    if v is None or (isinstance(v, str) and v.lower() in ("inf", "never", "null", "none")):
        return INF
    v = float(v)
    if v < 0:
        raise ValueError(f"feedback delay_L must be >= 0, got {v}")
    return INF if math.isinf(v) else float(int(v))


def feedback_params(cfg: Dict) -> Tuple[str, float, float]:
    """(mode, L, pi) from cfg['market']['feedback'] (missing -> immediate)."""
    f = (cfg.get("market", {}) or {}).get("feedback", {}) or {}
    mode = str(f.get("mode", "immediate"))
    if mode not in MODES:
        raise ValueError(f"unknown feedback mode {mode} (expected one of {MODES})")
    L = 0.0 if mode in ("immediate", "sparse") else (INF if mode == "never" else _as_delay(f.get("delay_L", 0)))
    pi = 1.0 if mode in ("immediate", "delayed", "never") else float(f.get("reveal_prob", 1.0))
    if not 0.0 <= pi <= 1.0:
        raise ValueError(f"feedback reveal_prob must be in [0, 1], got {pi}")
    return mode, L, pi


def delay_label(L: float):
    """JSON / log representation of L: int, or None for inf."""
    return None if math.isinf(L) else int(L)


@dataclass
class Label:
    step: int               # global step (task index) of the purchase
    due: float              # step at which it is delivered (inf: never)
    task: object
    buyer: object
    seller: object
    correct: bool
    cost: float


class FeedbackBuffer:
    def __init__(self, delay_L: float = 0.0, reveal_prob: float = 1.0, rng: Optional[random.Random] = None):
        self.L, self.pi = float(delay_L), float(reveal_prob)
        self.rng = rng or random.Random(0)
        self._heap: List[Tuple[float, int, Label]] = []
        self._seq = 0
        self.n_pushed = self.n_revealed = self.n_delivered_online = self.n_flushed = 0

    def push(self, step: int, task, buyer, seller, correct: bool, cost: float, horizon: int):
        """Register a served purchase. Returns (revealed, delivered_at) where delivered_at is the step at which
        the label will be delivered (horizon for an end-of-episode flush) or None if it never will be."""
        self.n_pushed += 1
        revealed = self.pi >= 1.0 or (self.pi > 0.0 and self.rng.random() < self.pi)
        if not revealed:
            return False, None
        self.n_revealed += 1
        if math.isinf(self.L):
            return True, None
        due = step + self.L
        heapq.heappush(self._heap, (due, self._seq, Label(step, due, task, buyer, seller, bool(correct), cost)))
        self._seq += 1
        return True, int(due) if due < horizon else int(horizon)

    def pop_ready(self, t: float) -> List[Label]:
        """Labels due at or before step t, FIFO by (due step, push order)."""
        out = []
        while self._heap and self._heap[0][0] <= t:
            out.append(heapq.heappop(self._heap)[2])
        self.n_delivered_online += len(out)
        return out

    def flush_at_end(self) -> List[Label]:
        """End of episode: finite L delivers every pending label; L = inf delivers nothing."""
        if math.isinf(self.L):
            return []
        out = [heapq.heappop(self._heap)[2] for _ in range(len(self._heap))]
        self.n_flushed += len(out)
        return out

    def pending(self) -> int:
        return len(self._heap)


class FeedbackRouter:
    """Wraps a PilotRouter / StageRouteRouter: run_policy's `update(..., correct, cost)` only passes the
    immediately-observable cost to the router; the correctness label reaches `router.learn` through the buffer."""

    def __init__(self, inner, buffer: FeedbackBuffer):
        self.inner, self.buffer = inner, buffer
        self.step = 0
        self.n_label_updates_online = 0
        self.n_label_updates_flush = 0

    def choose(self, task, buyer, cands, exp_cost):
        return self.inner.choose(task, buyer, cands, exp_cost)

    def update(self, task, buyer, seller, correct: Optional[bool], actual_cost: float):
        # correct is None <=> the purchase was blocked (not served): no cost observation, no label (as in v3/v4)
        self.inner.observe_cost(buyer, seller, actual_cost, served=correct is not None)
        self.deliver(self.step)

    def deliver(self, t: int) -> int:
        labels = self.buffer.pop_ready(t)
        for lb in labels:
            self.inner.learn(lb.task, lb.seller, lb.correct, lb.cost)
        self.n_label_updates_online += len(labels)
        return len(labels)

    def flush(self) -> int:
        labels = self.buffer.flush_at_end()
        for lb in labels:
            self.inner.learn(lb.task, lb.seller, lb.correct, lb.cost)
        self.n_label_updates_flush += len(labels)
        return len(labels)

    def end_query(self, buyer):
        self.inner.end_query(buyer)
