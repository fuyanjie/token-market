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

v5: both routers split `update` into `observe_cost` (immediate: it is on the buyer's own bill) and `learn` (the
correctness label, which tokenmarket.feedback may delay or drop). `update` = observe_cost + learn = v3/v4 behaviour.
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
        self.n_label_updates = 0

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
        """Immediate feedback (v3/v4): observe the cost, then learn from the label (skipped if None)."""
        self.observe_cost(buyer, seller, actual_cost)
        if correct is not None:
            self.learn(task, seller, correct, actual_cost)

    def observe_cost(self, buyer, seller, actual_cost: float, served: bool = True):
        """v5: the realised cost is on the buyer's own bill -> always immediate (budget-bin accounting)."""
        self.bins[buyer.id].spend(actual_cost)

    def learn(self, task, seller, correct: bool, actual_cost: float = 0.0):
        """v5: LinUCB update from a correctness label (possibly delayed by the FeedbackBuffer)."""
        x = context(task)
        self.A[seller.id] += np.outer(x, x)
        self.b[seller.id] += float(correct) * x
        self.n_label_updates += 1

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
        self.n = {s.id: 0 for s in sellers}       # correctness labels received per arm
        self.n_c = {s.id: 0 for s in sellers}     # v5: cost observations per arm (== n under immediate feedback)
        self.n_label_updates = 0
        self.mu = {s.id: 0.0 for s in sellers}
        self.c = {s.id: 0.0 for s in sellers}
        self.alpha = {s.id: min(1.0, s.capacity_per_round / max(1.0, tasks_per_round)) for s in sellers}
        self.b = {b.id: self.b_scale * b.budget / max(1, horizon.get(b.id, 1)) for b in buyers}
        self.last_p = None

    def bounds(self, s):
        n, nc = self.n[s.id], self.n_c[s.id]
        mu_u = 1.0 if n == 0 else min(1.0, self.mu[s.id] + f_rad(self.mu[s.id], n, self.gamma))
        c_l = 0.0 if nc == 0 else max(0.0, self.c[s.id] - f_rad(self.c[s.id], nc, self.gamma))
        return mu_u, c_l

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
        """Immediate feedback (v3/v4): a served purchase (correct not None) updates cost and reward estimates."""
        if correct is None:
            return
        self.observe_cost(buyer, seller, actual_cost)
        self.learn(task, seller, correct, actual_cost)

    def observe_cost(self, buyer, seller, actual_cost: float, served: bool = True):
        """v5: realised cost is observed on the bill -> immediate (blocked purchases are skipped, as in v3)."""
        if not served:
            return
        k = seller.id
        self.n_c[k] += 1
        self.c[k] += (actual_cost - self.c[k]) / self.n_c[k]

    def learn(self, task, seller, correct: bool, actual_cost: float = 0.0):
        """v5: reward-mean update from a correctness label (possibly delayed by the FeedbackBuffer)."""
        k = seller.id
        self.n[k] += 1
        self.mu[k] += (float(correct) - self.mu[k]) / self.n[k]
        self.n_label_updates += 1

    def end_query(self, buyer):
        pass


# =====================================================================================================================
# v1.0 FAITHFUL reimplementations (protocol §3). The v3 classes above stay unchanged (policy ids pilot*/stageroute*
# keep v0.1 numbers); the v1.0 classes run under the policy ids pilot_v1* / stageroute_v1*. Every deviation from the
# papers is listed in docs/BASELINES_v1.0.md.
# =====================================================================================================================
V1_ROUTER_POLICIES = ("pilot_v1", "pilot_v1_compliant", "stageroute_v1", "stageroute_v1_compliant")


def is_v1_router(policy: str) -> bool:
    return policy in V1_ROUTER_POLICIES


def _unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def _cos(theta: np.ndarray, x_hat: np.ndarray) -> float:
    n = float(np.linalg.norm(theta))
    return float(theta @ x_hat) / n if n > 0 else 0.0


def _listed_mean_accuracy(rep, model: str, difficulties) -> float:
    acc = []
    for d in difficulties:
        try:
            acc.append(rep.accuracy(model, d))
        except KeyError:
            pass
    return float(np.mean(acc)) if acc else 0.5


def pilot_preference_prior(models: Sequence[str], rep, pool, iters: int = 400, lr: float = 0.5) -> Dict[str, np.ndarray]:
    """PILOT pretraining phase 2 (Panda et al. 2025, §2.2.1) on SYNTHETIC preference data.

    The paper learns LLM embeddings theta_i from human pairwise preferences (ChatArena) with
        p_i = exp(cos(theta_i, psi(q))) / sum_{k in {i,j}} exp(cos(theta_k, psi(q)))
    and binary cross-entropy. There is no human preference data for a token market, so the preference tuples are
    derived from the PUBLIC listing only: for every pool query q and every pair of distinct claimed models (i, j),
    the soft label is P(i preferred) = acc_i(1 - acc_j) + 0.5 [acc_i acc_j + (1 - acc_i)(1 - acc_j)], acc = listed
    accuracy of the claimed model at q's difficulty. psi(q) = our fixed normalised context (phase 1, the learned
    projection of a text embedding, is replaced by the hand-made context; see docs/BASELINES_v1.0.md).
    Full-batch gradient descent from a deterministic initialisation (no RNG)."""
    models = sorted(set(models))
    dim = N_DIFF + len(TYPES) + 2
    xs = [_unit(context(t)) for t in pool]
    pairs = []
    for t, x in zip(pool, xs):
        for i, mi in enumerate(models):
            for j, mj in enumerate(models):
                if i < j:
                    try:
                        ai, aj = rep.accuracy(mi, t.difficulty), rep.accuracy(mj, t.difficulty)
                    except KeyError:
                        continue
                    pairs.append((i, j, x, ai * (1 - aj) + 0.5 * (ai * aj + (1 - ai) * (1 - aj))))
    theta = np.zeros((len(models), dim))
    for i, m in enumerate(models):       # init: listed accuracy profile on the difficulty one-hots + bias
        for d in range(1, N_DIFF + 1):
            try:
                theta[i, d - 1] = rep.accuracy(m, d)
            except KeyError:
                theta[i, d - 1] = 0.5
        theta[i, -1] = 1.0
    if not pairs or len(models) < 2:
        return {m: theta[i] for i, m in enumerate(models)}

    def grad_cos(th, x):
        n = np.linalg.norm(th)
        return x / n - (th @ x) * th / n ** 3

    for _ in range(iters):
        g = np.zeros_like(theta)
        for i, j, x, y in pairs:
            ci, cj = _cos(theta[i], x), _cos(theta[j], x)
            p = 1.0 / (1.0 + math.exp(-(ci - cj)))
            g[i] += (p - y) * grad_cos(theta[i], x)
            g[j] -= (p - y) * grad_cos(theta[j], x)
        theta -= lr * g / len(pairs)
    return {m: theta[i] for i, m in enumerate(models)}


class PilotV1Router:
    """PILOT (Panda et al., EMNLP Findings 2025, arXiv:2508.21141), faithful where the market allows:
    * reward model E[r | a, q] = cos(psi_hat(q), theta_a)   (Eq. 1); r = observed correctness in {0, 1}.
    * prior A_a^0 = lambda_a I, b_a^0 = lambda_a theta_a^pref with lambda_a = 1 / (pretraining accuracy of a)
      (here: mean LISTED accuracy of the claimed model over the pool's difficulties); theta^pref from
      `pilot_preference_prior` (phase-2 BCE on cos-softmax).
    * ridge estimate theta~ = A^-1 b (Eq. 2); update of the CHOSEN arm only: A += psi_hat psi_hat^T, b += r psi_hat.
    * score = cos(psi_hat, theta~) + alpha * sqrt(psi_hat^T A^-1 psi_hat) (UCB) - `select: ucb` (default, online
      market: no separate learning bucket) or `select: greedy` = Algorithm 2/3's argmax cos.
    * budget = Algorithm 3 (App. C.2): bins of S queries (N = ceil(Q/S)), B_bin = B/N, B_left += B_bin per bin
      (carry-over), z reset to 0 per bin; eligible E = {l : C_l <= cos_l / ((UB e / LB)^z (LB / e))}; if E is empty,
      E = {l : C_l <= B_left / Q_left} (Q_left = remaining queries in the bin); if still empty the query is NOT
      bought ("insufficient budget"); after a purchase B_left -= C_l*, z += C_l* / B_bin (C = estimated cost).
    UB / LB (not reported in the paper): max / min over the market's sellers of listed accuracy / expected cost,
    overridable via market.pilot_v1.{ub, lb}."""

    def __init__(self, sellers: Sequence, rep, buyers: Sequence, horizon: Dict[str, int], cfg: Dict, pool):
        p = cfg.get("market", {}).get("pilot_v1", {})
        self.alpha = float(p.get("alpha", 2.0))
        self.select = str(p.get("select", "ucb"))
        self.n_bins = int(p.get("n_bins", 4))
        diffs = sorted({t.difficulty for t in pool}) or [1, 2, 3]
        claimed = sorted({s.claimed_model for s in sellers})
        prior = pilot_preference_prior(claimed, rep, pool, int(p.get("pretrain_iters", 400)))
        dim = N_DIFF + len(TYPES) + 2
        self.A, self.b, self.lam = {}, {}, {}
        for s in sellers:
            lam = 1.0 / max(_listed_mean_accuracy(rep, s.claimed_model, diffs), 1e-3)
            self.lam[s.id] = lam
            self.A[s.id] = lam * np.eye(dim)
            self.b[s.id] = lam * prior[s.claimed_model]
        tok = {m: rep.tokens_mean(m) for m in claimed}
        ratios = [_listed_mean_accuracy(rep, s.claimed_model, diffs) / max(s.price_per_1k * tok[s.claimed_model]
                                                                          / 1000.0, 1e-12) for s in sellers]
        self.lb = float(p["lb"]) if p.get("lb") is not None else min(ratios)
        self.ub = float(p["ub"]) if p.get("ub") is not None else max(ratios)
        if self.ub <= self.lb:
            self.ub = self.lb * 1.0001
        self.state = {}
        for bu in buyers:
            Q = max(1, int(horizon.get(bu.id, 1)))
            S = max(1, int(math.ceil(Q / max(1, self.n_bins))))
            self.state[bu.id] = {"B": float(bu.budget), "Q": Q, "S": S, "N": int(math.ceil(Q / S)), "t": 0,
                                 "B_left": 0.0, "z": 0.0, "bin": -1}
        self._pending: Dict[str, float] = {}
        self.n_label_updates = 0
        self.n_insufficient = 0

    def _bin(self, st):
        k = st["t"] // st["S"]
        while st["bin"] < k:               # new bin: carry over B_left, reset utilisation
            st["bin"] += 1
            st["B_left"] += st["B"] / st["N"]
            st["z"] = 0.0
        return k

    def scores(self, task, s):
        x = _unit(context(task))
        Ainv = np.linalg.inv(self.A[s.id])
        theta = Ainv @ self.b[s.id]
        mean = _cos(theta, x)
        return mean, mean + self.alpha * math.sqrt(max(0.0, float(x @ Ainv @ x)))

    def choose(self, task, buyer, cands: List, exp_cost):
        if not cands:
            return None
        st = self.state[buyer.id]
        k = self._bin(st)
        psi = (self.ub * math.e / self.lb) ** min(1.0, max(0.0, st["z"])) * (self.lb / math.e)
        sc = {s.id: self.scores(task, s) for s in cands}
        elig = [s for s in cands if exp_cost(s) <= sc[s.id][0] / psi]
        if not elig:
            q_left = max(1, min(st["Q"], (k + 1) * st["S"]) - st["t"])
            cap = st["B_left"] / q_left
            elig = [s for s in cands if exp_cost(s) <= cap]
        if not elig:
            self.n_insufficient += 1
            return None
        idx = 1 if self.select == "ucb" else 0
        best = max(elig, key=lambda s: (sc[s.id][idx], -exp_cost(s), s.id))
        self._pending[buyer.id] = exp_cost(best)
        return best

    def update(self, task, buyer, seller, correct: Optional[bool], actual_cost: float):
        self.observe_cost(buyer, seller, actual_cost, served=correct is not None)
        if correct is not None:
            self.learn(task, seller, correct, actual_cost)

    def observe_cost(self, buyer, seller, actual_cost: float, served: bool = True):
        st = self.state[buyer.id]
        c = self._pending.pop(buyer.id, None)
        if c is None or not served:
            return
        st["B_left"] -= c
        st["z"] += c / (st["B"] / st["N"]) if st["B"] > 0 else 1.0

    def learn(self, task, seller, correct: bool, actual_cost: float = 0.0):
        x = _unit(context(task))
        self.A[seller.id] += np.outer(x, x)
        self.b[seller.id] += float(correct) * x
        self.n_label_updates += 1

    def end_query(self, buyer):
        self._pending.pop(buyer.id, None)
        self.state[buyer.id]["t"] += 1


class StageRouteV1Router:
    """StageRoute (Li & Li, arXiv:2506.17254, ICLR 2026 per arXiv comments), faithful where the market allows:
    * K equal-length stages over the query stream (default K = round(T^(1/3)), the paper's guidance); at each stage
      start, DeployOPT (Eq. 3) - the MIP over (d, z) - selects the deployed set; within a stage, RouteOPT (Eq. 7) is
      solved per query over the deployed models and m ~ p*.
    * mu^U = proj_[0,1](mu_bar + 2 f_rad(mu_bar, N+1)), c^L = proj_[c1,c2](c_bar - 2 f_rad(c_bar, N+1)) (Eq. 4-5),
      f_rad(v, n) = sqrt(gamma v / n) + gamma / n; empirical means start at 0 (N = 0).
    * alpha_m = seller capacity share (capacity_per_round / tasks per round, capped at 1).
    * Deployed set: supp(d*) (Eq. 6) topped up to n_deploy = min(M_max, #sellers) with the remaining highest-mu^U
      sellers - the MIP's z picks M_max models but Eq. 6 deploys only supp(d*); the paper leaves this open and a
      buyer whose compliant candidates miss supp(d*) would otherwise get nothing (docs/BASELINES_v1.0.md).
    * Per-query budget b = budget_scale * B_buyer / T_buyer (per buyer); the stage MIP uses the market-wide mean
      b_bar = sum B / T (the paper has one budget stream).
    * Market fallbacks (not in the paper): if no deployed seller is a candidate for this query, route over all
      candidates; if RouteOPT is infeasible, the arm with the smallest c^L (= v0.1 behaviour)."""

    def __init__(self, sellers: Sequence, buyers: Sequence, horizon: Dict[str, int], cfg: Dict, n_queries: int,
                 tasks_per_round: float, rng: random.Random, rep=None):
        p = cfg.get("market", {}).get("stageroute_v1", {})
        self.gamma = float(p.get("gamma", 0.1))
        self.b_scale = float(p.get("budget_scale", 1.0))
        self.rng = rng
        n = len(sellers)
        self.T = max(1, int(n_queries))
        self.K = max(1, int(p["n_stages"]) if p.get("n_stages") else int(round(self.T ** (1.0 / 3.0))))
        m_max = p.get("m_max")
        self.m_max = int(m_max) if m_max else max(1, int(math.ceil(n ** (2.0 / 3.0))))
        self.sellers = list(sellers)
        self.n = {s.id: 0 for s in sellers}
        self.n_c = {s.id: 0 for s in sellers}
        self.mu = {s.id: 0.0 for s in sellers}
        self.c = {s.id: 0.0 for s in sellers}
        self.alpha = {s.id: min(1.0, s.capacity_per_round / max(1.0, tasks_per_round)) for s in sellers}
        self.b = {bu.id: self.b_scale * bu.budget / max(1, horizon.get(bu.id, 1)) for bu in buyers}
        self.b_bar = self.b_scale * sum(bu.budget for bu in buyers) / self.T
        if rep is not None:
            exp = [s.price_per_1k * rep.tokens_mean(s.claimed_model) / 1000.0 for s in sellers]
        else:
            exp = [s.price_per_1k * 0.15 for s in sellers]
        self.c1 = float(p["c1"]) if p.get("c1") is not None else 0.25 * min(exp)
        self.c2 = float(p["c2"]) if p.get("c2") is not None else 4.0 * max(exp)
        self.step = 0
        self.stage = -1
        self.deployed: List[str] = [s.id for s in sellers]
        self.deploy_log: List[Dict] = []
        self.n_label_updates = 0
        self.n_fallback_cands = 0
        self.n_fallback_infeasible = 0
        self.last_p = None

    def bounds(self, s):
        n, nc = self.n[s.id], self.n_c[s.id]
        mu_u = min(1.0, max(0.0, self.mu[s.id] + 2.0 * f_rad(self.mu[s.id], n + 1, self.gamma)))
        c_l = min(self.c2, max(self.c1, self.c[s.id] - 2.0 * f_rad(self.c[s.id], nc + 1, self.gamma)))
        return mu_u, c_l

    def _maybe_deploy(self):
        k = min(self.K - 1, self.step * self.K // self.T)
        if k == self.stage:
            return
        self.stage = k
        ids = [s.id for s in self.sellers]
        bd = [self.bounds(s) for s in self.sellers]
        mu_u = [u for u, _ in bd]
        n_dep = min(self.m_max, len(ids))
        from .lp import deploy_mip
        res = deploy_mip(mu_u, [c for _, c in bd], self.b_bar, [self.alpha[i] for i in ids], n_dep)
        if res is None:                   # infeasible at LCB costs: deploy the n_dep cheapest (c^L) sellers
            order = sorted(range(len(ids)), key=lambda i: (bd[i][1], -bd[i][0], ids[i]))
            dep = [ids[i] for i in order[:n_dep]]
            supp = []
        else:
            d, _z = res
            supp = [ids[i] for i in range(len(ids)) if d[i] > 1e-9]
            rest = sorted((i for i in range(len(ids)) if ids[i] not in supp), key=lambda i: (-mu_u[i], bd[i][1], ids[i]))
            dep = supp + [ids[i] for i in rest[:max(0, n_dep - len(supp))]]
        self.deployed = dep
        self.deploy_log.append({"stage": k, "step": self.step, "deployed": list(dep), "support": supp,
                                "feasible": res is not None})

    def distribution(self, buyer, cands):
        from .lp import box_lp_max
        ub = [self.bounds(s) for s in cands]
        alpha = [self.alpha[s.id] for s in cands]
        if sum(alpha) < 1:
            alpha = [a / sum(alpha) for a in alpha] if sum(alpha) > 0 else [1.0] * len(cands)
        p = box_lp_max([u for u, _ in ub], [c for _, c in ub], self.b[buyer.id], alpha)
        if p is None:
            self.n_fallback_infeasible += 1
            i = min(range(len(cands)), key=lambda i: (ub[i][1], -ub[i][0], cands[i].id))
            p = np.zeros(len(cands))
            p[i] = 1.0
        return p

    def choose(self, task, buyer, cands: List, exp_cost):
        if not cands:
            return None
        self._maybe_deploy()
        dep = set(self.deployed)
        sub = [s for s in cands if s.id in dep]
        if not sub:
            self.n_fallback_cands += 1
            sub = list(cands)
        p = self.distribution(buyer, sub)
        self.last_p = p
        return self.rng.choices(sub, weights=list(p), k=1)[0]

    def update(self, task, buyer, seller, correct: Optional[bool], actual_cost: float):
        if correct is None:
            return
        self.observe_cost(buyer, seller, actual_cost)
        self.learn(task, seller, correct, actual_cost)

    def observe_cost(self, buyer, seller, actual_cost: float, served: bool = True):
        if not served:
            return
        k = seller.id
        self.n_c[k] += 1
        self.c[k] += (actual_cost - self.c[k]) / self.n_c[k]

    def learn(self, task, seller, correct: bool, actual_cost: float = 0.0):
        k = seller.id
        self.n[k] += 1
        self.mu[k] += (float(correct) - self.mu[k]) / self.n[k]
        self.n_label_updates += 1

    def end_query(self, buyer):
        self.step += 1
