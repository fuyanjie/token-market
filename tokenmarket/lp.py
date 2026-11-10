"""Small exact LP / MIP solvers in numpy (no scipy dependency) for the v1.0 StageRoute reimplementation.

linprog: dense two-phase tableau simplex with Bland's anti-cycling rule.
    minimise c.x  s.t.  A_ub x <= b_ub,  A_eq x = b_eq,  0 <= x <= ub (ub optional, per variable, inf allowed).
milp_binary: depth-first branch and bound on a set of binary variables using linprog for the relaxations.
Sizes in this repo are tiny (<= ~100 variables), so dense pivoting is fine.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np

TOL = 1e-9


@dataclass
class LPResult:
    status: str                  # optimal | infeasible | unbounded
    x: Optional[np.ndarray] = None
    fun: Optional[float] = None


def _pivot(T: np.ndarray, basis: List[int], r: int, c: int) -> None:
    T[r] /= T[r, c]
    for i in range(T.shape[0]):
        if i != r and abs(T[i, c]) > 0:
            T[i] -= T[i, c] * T[r]
    basis[r] = c


def _simplex(T: np.ndarray, basis: List[int], allowed: np.ndarray, max_iter: int = 10000) -> str:
    """Minimise the objective in the LAST row of T (reduced costs; T[-1, -1] = -objective). Bland's rule."""
    m = T.shape[0] - 1
    for _ in range(max_iter):
        red = T[-1, :-1]
        cand = np.where((red < -TOL) & allowed)[0]
        if cand.size == 0:
            return "optimal"
        c = int(cand[0])
        col = T[:m, c]
        pos = col > TOL
        if not pos.any():
            return "unbounded"
        ratios = np.full(m, np.inf)
        ratios[pos] = T[:m, -1][pos] / col[pos]
        best = ratios.min()
        rows = np.where(np.abs(ratios - best) <= TOL * max(1.0, abs(best)))[0]
        r = int(min(rows, key=lambda i: basis[i]))     # Bland: leaving variable with the smallest index
        _pivot(T, basis, r, c)
    raise RuntimeError("simplex iteration limit")


def linprog(c: Sequence[float], A_ub=None, b_ub=None, A_eq=None, b_eq=None, ub=None) -> LPResult:
    c = np.asarray(c, float)
    n = c.size
    rows, rhs, kinds = [], [], []          # kind: 'le' | 'eq'
    if A_ub is not None and len(A_ub):
        for a, b in zip(np.atleast_2d(np.asarray(A_ub, float)), np.asarray(b_ub, float)):
            rows.append(a), rhs.append(b), kinds.append("le")
    if ub is not None:
        for j, u in enumerate(np.asarray(ub, float)):
            if np.isfinite(u):
                a = np.zeros(n)
                a[j] = 1.0
                rows.append(a), rhs.append(u), kinds.append("le")
    if A_eq is not None and len(A_eq):
        for a, b in zip(np.atleast_2d(np.asarray(A_eq, float)), np.asarray(b_eq, float)):
            rows.append(a), rhs.append(b), kinds.append("eq")
    m = len(rows)
    n_slack = sum(k == "le" for k in kinds)
    # columns: x (n) | slacks (n_slack) | artificials (m) | rhs
    T = np.zeros((m + 1, n + n_slack + m + 1))
    si = 0
    for i, (a, b, k) in enumerate(zip(rows, rhs, kinds)):
        T[i, :n] = a
        if k == "le":
            T[i, n + si] = 1.0
            si += 1
        T[i, -1] = b
        if b < 0:
            T[i] *= -1
        T[i, n + n_slack + i] = 1.0
    basis = [n + n_slack + i for i in range(m)]
    # phase 1: minimise the sum of artificials
    T[-1, :] = -T[:m].sum(axis=0)
    T[-1, n + n_slack:n + n_slack + m] = 0.0
    allowed = np.ones(n + n_slack + m, bool)
    _simplex(T, basis, allowed)
    if -T[-1, -1] > 1e-7:
        return LPResult("infeasible")
    # drive artificials out of the basis where possible
    art0 = n + n_slack
    for r in range(m):
        if basis[r] >= art0:
            nz = np.where(np.abs(T[r, :art0]) > TOL)[0]
            if nz.size:
                _pivot(T, basis, r, int(nz[0]))
    allowed[art0:] = False
    # phase 2
    T[-1, :] = 0.0
    T[-1, :n] = c
    for r in range(m):
        if basis[r] < n + n_slack and abs(T[-1, basis[r]]) > 0:
            T[-1] -= T[-1, basis[r]] * T[r]
    st = _simplex(T, basis, allowed)
    if st != "optimal":
        return LPResult(st)
    x = np.zeros(n + n_slack + m)
    for r in range(m):
        x[basis[r]] = T[r, -1]
    x = np.clip(x[:n], 0.0, None)
    return LPResult("optimal", x, float(c @ x))


def milp_binary(c, A_ub=None, b_ub=None, A_eq=None, b_eq=None, ub=None, binary: Sequence[int] = (),
                max_nodes: int = 20000) -> LPResult:
    """Minimise c.x with x[j] in {0, 1} for j in `binary` (their ub must be 1). Depth-first branch and bound,
    branching on the most fractional binary variable; exact up to max_nodes (raises if exceeded)."""
    c = np.asarray(c, float)
    n = c.size
    base_ub = np.full(n, np.inf) if ub is None else np.asarray(ub, float).copy()
    best: Optional[LPResult] = None
    stack = [(np.zeros(n), base_ub.copy())]            # (lower bounds via shift, upper bounds)
    nodes = 0
    A_ub_ = None if A_ub is None else np.atleast_2d(np.asarray(A_ub, float))
    A_eq_ = None if A_eq is None else np.atleast_2d(np.asarray(A_eq, float))
    while stack:
        lo, hi = stack.pop()
        nodes += 1
        if nodes > max_nodes:
            raise RuntimeError("milp_binary node limit")
        # fixed-to-1 binaries are handled by the substitution x = lo + y, y >= 0
        bu = None if b_ub is None else np.asarray(b_ub, float) - (A_ub_ @ lo if A_ub_ is not None else 0)
        be = None if b_eq is None else np.asarray(b_eq, float) - (A_eq_ @ lo if A_eq_ is not None else 0)
        res = linprog(c, A_ub_, bu, A_eq_, be, hi - lo)
        if res.status != "optimal":
            continue
        x = res.x + lo
        val = float(c @ x)
        if best is not None and val >= best.fun - 1e-12:
            continue
        frac = [(abs(x[j] - round(x[j])), j) for j in binary if abs(x[j] - round(x[j])) > 1e-7]
        if not frac:
            best = LPResult("optimal", x, val)
            continue
        _, j = max(frac)
        lo1, hi0 = lo.copy(), hi.copy()
        lo1[j] = 1.0
        hi0[j] = 0.0
        stack.append((lo.copy(), hi0))     # x_j = 0 (explored second)
        stack.append((lo1, hi.copy()))     # x_j = 1 (explored first)
    return best if best is not None else LPResult("infeasible")


def box_lp_max(mu, cost, b, alpha) -> Optional[np.ndarray]:
    """max mu.p  s.t.  cost.p <= b,  sum p = 1,  0 <= p <= alpha.  None if infeasible."""
    n = len(mu)
    res = linprog(-np.asarray(mu, float), A_ub=[np.asarray(cost, float)], b_ub=[b], A_eq=[np.ones(n)], b_eq=[1.0],
                  ub=np.asarray(alpha, float))
    if res.status != "optimal":
        return None
    p = np.clip(res.x, 0.0, None)
    return p / p.sum()


def deploy_mip(mu_u, cost_l, b, alpha, n_deploy: int):
    """StageRoute DeployOPT (Li & Li, Eq. 3):
        max_{d,z} sum mu^U_m d_m  s.t. sum c^L_m d_m <= b, sum d_m = 1, 0 <= d_m <= alpha_m z_m,
                                       sum z_m = n_deploy, z_m in {0,1}.
    Returns (d, z) as numpy arrays, or None if infeasible."""
    mu_u, cost_l, alpha = (np.asarray(v, float) for v in (mu_u, cost_l, alpha))
    n = mu_u.size
    c = np.concatenate([-mu_u, np.zeros(n)])
    A_ub = [np.concatenate([cost_l, np.zeros(n)])]
    b_ub = [b]
    for m in range(n):                         # d_m - alpha_m z_m <= 0
        row = np.zeros(2 * n)
        row[m], row[n + m] = 1.0, -alpha[m]
        A_ub.append(row)
        b_ub.append(0.0)
    A_eq = [np.concatenate([np.ones(n), np.zeros(n)]), np.concatenate([np.zeros(n), np.ones(n)])]
    b_eq = [1.0, float(n_deploy)]
    ub = np.concatenate([np.full(n, np.inf), np.ones(n)])
    res = milp_binary(c, A_ub, b_ub, A_eq, b_eq, ub, binary=range(n, 2 * n))
    if res.status != "optimal":
        return None
    return res.x[:n], np.round(res.x[n:]).astype(int)
