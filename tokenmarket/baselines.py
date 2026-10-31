"""v3 / D: budgeted LLM-routing baselines from the literature — OUR SIMPLIFIED REIMPLEMENTATIONS.

D1 `pilot` / `pilot_compliant` — our simplified reimplementation of PILOT (Panda et al., arXiv:2508.21141,
   "Adaptive LLM Routing Under Budget Constraints"):
   * contextual bandit LinUCB over sellers (arms). Context x = [one-hot difficulty (1..5), one-hot task type /
     source, log(prompt chars)/10, bias]. The paper uses query embeddings and a preference prior learned from
     human-preference data; we use the CLAIMED model's public reputation as the "preference prior":
     A_a = lambda * I, b_a = lambda * theta_prior with theta_prior[difficulty d] = rep(claimed, d).
   * reward = correctness observed after purchase (as in the paper we trust observed outcomes).
   * online cost policy ON-MCKP with the ZCL threshold: arm a is eligible iff
         est_cost_a <= est_reward_a / psi(z),   psi(z) = (UB * e / LB) ** z * (LB / e)
     z = budget utilisation of the current bin. The buyer budget B is split into `n_bins` equal bins over its
     query horizon; unspent budget spills over into the next bin. If no arm is eligible, fall back to arms
     with est_cost <= B_left / Q_left; if still none, the cheapest arm. Pick the highest-UCB eligible arm.
   * NO audit-cost accounting, NO strategic-seller model, NO compliance filter (pilot_compliant adds the hard
     compliance filter for a fair comparison).

D2 `stageroute` / `stageroute_compliant` — budgeted bandit in the spirit of StageRoute (Li & Li,
   arXiv:2506.17254, "Near-Optimal Online Deployment and Routing for Streaming LLMs"):
   * per-query routing LP  max_p sum_m mu^U_m p_m  s.t.  sum_m c^L_m p_m <= b,  sum_m p_m = 1,
     0 <= p_m <= alpha_m (throughput cap = seller capacity share), then sample m ~ p.
     b = B / T (per-query budget = buyer budget / buyer's query horizon).
   * mu^U = min(1, mu_hat + f_rad(mu_hat, n)), c^L = max(0, c_hat - f_rad(c_hat, n)),
     f_rad(v, n) = sqrt(gamma * v / n) + gamma / n; unplayed arms: mu^U = 1, c^L = 0.
   * the stage-wise deployment MIP of the paper is SKIPPED (we only have 3 fixed sellers).
   * the LP is solved exactly by vertex enumeration (numpy only, no solver dependency).
   * same omissions as D1; stageroute_compliant adds the compliance filter.
"""
from __future__ import annotations

import itertools
import math
import random
from typing import Dict, List, Optional, Sequence

import numpy as np

N_DIFF = 5
TYPES = ("arithmetic", "word_problem", "sequence", "logic", "gsm8k", "math500")


def context(task) -> np.ndarray:
    x = np.zeros(N_DIFF + len(TYPES) + 2)
    x[min(N_DIFF, max(1, int(task.difficulty))) - 1] = 1.0
    if task.task_type in TYPES:
        x[N_DIFF + TYPES.index(task.task_type)] = 1.0
    x[-2] = math.log(max(1, len(task.question))) / 10.0
    x[-1] = 1.0
    return x


def zcl_psi(z: float, lb: float, ub: float) -> float:
    """ZCL threshold on the reward/cost efficiency at budget utilisation z in [0, 1]."""
    z = min(1.0, max(0.0, z))
    return (ub * math.e / lb) ** z * (lb / math.e)


def zcl_eligible(est_cost: float, est_reward: float, z: float, lb: float, ub: float) -> bool:
    return est_cost <= est_reward / zcl_psi(z, lb, ub)


class BudgetBins:
    """Split budget B over a horizon of Q queries into n bins; unspent budget spills into the next bin."""

    def __init__(self, budget: float, horizon: int, n_bins: int):
        self.B, self.Q = float(budget), max(1, int(horizon))
        self.n = max(1, min(int(n_bins), self.Q))
        self.t = 0                  # queries seen
        self.spent_total = 0.0
        self.bin_idx = 0
        self.bin_budget = self.B / self.n
        self.bin_spent = 0.0

    def _advance(self):
        while self.bin_idx < self.n - 1 and self.t >= (self.bin_idx + 1) * self.Q / self.n:
            left = self.bin_budget - self.bin_spent
            self.bin_idx += 1
            self.bin_budget = self.B / self.n + max(0.0, left)    # spillover
            self.bin_spent = 0.0

    def utilisation(self) -> float:
        self._advance()
        return self.bin_spent / self.bin_budget if self.bin_budget > 0 else 1.0

    def per_query_left(self) -> float:
        return max(0.0, self.B - self.spent_total) / max(1, self.Q - self.t)

    def spend(self, c: float):
        self.bin_spent += c
        self.spent_total += c

    def next_query(self):
        self.t += 1


class PilotRouter:
    def __init__(self, sellers: Sequence, rep, buyers: Sequence, horizon: Dict[str, int], cfg: Dict):
        p = cfg.get("market", {}).get("pilot", {})
        self.alpha = float(p.get("alpha", 0.5))
        self.lam = float(p.get("prior_lambda", 5.0))
        self.n_bins = int(p.get("n_bins", 4))
        self.lb = p.get("lb")
        self.ub = p.get("ub")
        self.rep = rep
        dim = N_DIFF + len(TYPES) + 2
        self.A, self.b = {}, {}
        for s in sellers:
            theta = np.zeros(dim)
            for d in range(1, N_DIFF + 1):
                try:
                    theta[d - 1] = rep.accuracy(s.claimed_model, d)
                except KeyError:
                    theta[d - 1] = 0.5
            self.A[s.id] = self.lam * np.eye(dim)
            self.b[s.id] = self.lam * theta
        self.bins = {b.id: BudgetBins(b.budget, horizon.get(b.id, 1), self.n_bins) for b in buyers}

    def scores(self, task, s):
        x = context(task)
        Ainv = np.linalg.inv(self.A[s.id])
        theta = Ainv @ self.b[s.id]
        mean = float(theta @ x)
        return mean, mean + self.alpha * math.sqrt(float(x @ Ainv @ x))

    def _bounds(self, cands, exp_cost, task):
        if self.lb is not None and self.ub is not None:
            return float(self.lb), float(self.ub)
        eff = [min(1.0, max(0.01, self.scores(task, s)[0])) / max(exp_cost(s), 1e-9) for s in cands]
        cmin = min(max(exp_cost(s), 1e-9) for s in cands)
        return 0.5 * min(eff), 1.0 / cmin

    def choose(self, task, buyer, cands: List, exp_cost):
        bins = self.bins[buyer.id]
        if not cands:
            return None
        z = bins.utilisation()
        lb, ub = self._bounds(cands, exp_cost, task)
        sc = {s.id: self.scores(task, s) for s in cands}
        reward = {k: min(1.0, max(0.01, v[0])) for k, v in sc.items()}
        elig = [s for s in cands if zcl_eligible(exp_cost(s), reward[s.id], z, lb, ub)]
        if not elig:
            cap = bins.per_query_left()
            elig = [s for s in cands if exp_cost(s) <= cap]
        if not elig:
            elig = [min(cands, key=lambda s: (exp_cost(s), s.id))]
        return max(elig, key=lambda s: (sc[s.id][1], -exp_cost(s), s.id))

    def update(self, task, buyer, seller, correct: Optional[bool], actual_cost: float):
        self.bins[buyer.id].spend(actual_cost)
        if correct is None:
            return
        x = context(task)
        self.A[seller.id] += np.outer(x, x)
        self.b[seller.id] += float(correct) * x

    def end_query(self, buyer):
        self.bins[buyer.id].next_query()


def f_rad(v: float, n: int, gamma: float) -> float:
    return math.sqrt(gamma * max(v, 0.0) / n) + gamma / n


def solve_routing_lp(mu: Sequence[float], cost: Sequence[float], b: float,
                     alpha: Sequence[float]) -> Optional[np.ndarray]:
    """max mu.p s.t. cost.p <= b, sum p = 1, 0 <= p <= alpha, by vertex enumeration. None if infeasible."""
    n = len(mu)
    mu, cost, alpha = np.asarray(mu, float), np.asarray(cost, float), np.asarray(alpha, float)
    # inequality rows G p <= h
    G = np.vstack([cost[None, :], -np.eye(n), np.eye(n)])
    h = np.concatenate([[b], np.zeros(n), alpha])
    best, best_v = None, -np.inf
    for act in itertools.combinations(range(len(h)), n - 1):
        M = np.vstack([np.ones((1, n)), G[list(act)]])
        rhs = np.concatenate([[1.0], h[list(act)]])
        if abs(np.linalg.det(M)) < 1e-12:
            continue
        p = np.linalg.solve(M, rhs)
        if np.all(G @ p <= h + 1e-9) and abs(p.sum() - 1) < 1e-9:
            v = float(mu @ p)
            if v > best_v + 1e-12:
                best, best_v = np.clip(p, 0, None), v
    return None if best is None else best / best.sum()


class StageRouteRouter:
    def __init__(self, sellers: Sequence, buyers: Sequence, horizon: Dict[str, int], cfg: Dict,
                 tasks_per_round: float, rng: random.Random):
        p = cfg.get("market", {}).get("stageroute", {})
        self.gamma = float(p.get("gamma", 0.5))
        self.b_scale = float(p.get("budget_scale", 1.0))
        self.rng = rng
        self.n = {s.id: 0 for s in sellers}
        self.mu = {s.id: 0.0 for s in sellers}
        self.c = {s.id: 0.0 for s in sellers}
        self.alpha = {s.id: min(1.0, s.capacity_per_round / max(1.0, tasks_per_round)) for s in sellers}
        self.b = {b.id: self.b_scale * b.budget / max(1, horizon.get(b.id, 1)) for b in buyers}
        self.last_p = None

    def bounds(self, s):
        n = self.n[s.id]
        if n == 0:
            return 1.0, 0.0
        return (min(1.0, self.mu[s.id] + f_rad(self.mu[s.id], n, self.gamma)),
                max(0.0, self.c[s.id] - f_rad(self.c[s.id], n, self.gamma)))

    def distribution(self, buyer, cands):
        ub = [self.bounds(s) for s in cands]
        alpha = [self.alpha[s.id] for s in cands]
        if sum(alpha) < 1:     # caps infeasible for this candidate set: relax proportionally
            alpha = [a / sum(alpha) for a in alpha] if sum(alpha) > 0 else [1.0] * len(cands)
        p = solve_routing_lp([u for u, _ in ub], [c for _, c in ub], self.b[buyer.id], alpha)
        if p is None:          # budget infeasible even at LCB costs: cheapest arm (within caps)
            p = solve_routing_lp([-c for _, c in ub], [0.0] * len(cands), 1.0, alpha)
        return p

    def choose(self, task, buyer, cands: List, exp_cost):
        if not cands:
            return None
        p = self.distribution(buyer, cands)
        self.last_p = p
        return self.rng.choices(cands, weights=list(p), k=1)[0]

    def update(self, task, buyer, seller, correct: Optional[bool], actual_cost: float):
        if correct is None:
            return
        k = seller.id
        self.n[k] += 1
        self.mu[k] += (float(correct) - self.mu[k]) / self.n[k]
        self.c[k] += (actual_cost - self.c[k]) / self.n[k]

    def end_query(self, buyer):
        pass
