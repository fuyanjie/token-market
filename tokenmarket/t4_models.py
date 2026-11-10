"""v1.0 T4 baselines and metrics in numpy (no sklearn in the pinned environment). Protocol §5:
logistic regression, GBDT and a rule baseline (low quoted price + billed-tokens anomaly; NOT answer length), scored
with AUROC, AP and precision@10.

Feature encoding: numeric whitelisted columns (train-median imputation, train mean/std standardisation) + one-hot
of the categorical columns (train vocabulary). All fits are deterministic (no RNG).
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .t4_export import CATEGORICAL


# --------------------------------------------------------------------------- metrics
def auroc(y: Sequence[int], s: Sequence[float]) -> Optional[float]:
    """Mann-Whitney AUROC with average ranks for ties; None if only one class."""
    y, s = np.asarray(y, int), np.asarray(s, float)
    n1, n0 = int(y.sum()), int((1 - y).sum())
    if n1 == 0 or n0 == 0:
        return None
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s))
    ss = s[order]
    i = 0
    while i < len(ss):
        j = i
        while j + 1 < len(ss) and ss[j + 1] == ss[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def average_precision(y: Sequence[int], s: Sequence[float]) -> Optional[float]:
    """AP = mean of precision at each positive, ranking by score descending (ties broken by original order,
    stable); None if there are no positives."""
    y, s = np.asarray(y, int), np.asarray(s, float)
    if y.sum() == 0:
        return None
    order = np.argsort(-s, kind="mergesort")
    yy = y[order]
    hits = np.cumsum(yy)
    prec = hits / np.arange(1, len(yy) + 1)
    return float((prec * yy).sum() / yy.sum())


def precision_at_k(y: Sequence[int], s: Sequence[float], k: int = 10) -> Optional[float]:
    y, s = np.asarray(y, int), np.asarray(s, float)
    if len(y) == 0:
        return None
    order = np.argsort(-s, kind="mergesort")[:k]
    return float(y[order].mean())


METRICS = {"auroc": auroc, "ap": average_precision, "p_at_10": precision_at_k}


# --------------------------------------------------------------------------- encoding
def _num(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


class Encoder:
    def __init__(self, columns: Sequence[str]):
        self.cat = [c for c in columns if c in CATEGORICAL]
        self.num = [c for c in columns if c not in CATEGORICAL]

    def fit(self, rows: List[Dict]) -> "Encoder":
        self.med, self.mu, self.sd = {}, {}, {}
        for c in self.num:
            v = [x for x in (_num(r.get(c)) for r in rows) if x is not None]
            self.med[c] = float(np.median(v)) if v else 0.0
            filled = np.array([_num(r.get(c)) if _num(r.get(c)) is not None else self.med[c] for r in rows])
            self.mu[c] = float(filled.mean()) if len(filled) else 0.0
            sd = float(filled.std()) if len(filled) else 0.0
            self.sd[c] = sd if sd > 1e-12 else 1.0
        self.vocab = {c: sorted({str(r.get(c)) for r in rows}) for c in self.cat}
        return self

    def names(self) -> List[str]:
        return list(self.num) + [f"{c}={v}" for c in self.cat for v in self.vocab[c]]

    def transform(self, rows: List[Dict]) -> np.ndarray:
        X = np.zeros((len(rows), len(self.names())))
        for i, r in enumerate(rows):
            for j, c in enumerate(self.num):
                x = _num(r.get(c))
                X[i, j] = ((x if x is not None else self.med[c]) - self.mu[c]) / self.sd[c]
            k = len(self.num)
            for c in self.cat:
                v = str(r.get(c))
                for vv in self.vocab[c]:
                    X[i, k] = 1.0 if v == vv else 0.0
                    k += 1
        return X


# --------------------------------------------------------------------------- models
class LogisticRegression:
    """L2-regularised logistic regression fitted by Newton / IRLS (intercept unpenalised)."""

    def __init__(self, l2: float = 1.0, iters: int = 50):
        self.l2, self.iters = float(l2), int(iters)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LogisticRegression":
        Xb = np.hstack([np.ones((len(X), 1)), X])
        w = np.zeros(Xb.shape[1])
        R = self.l2 * np.eye(Xb.shape[1])
        R[0, 0] = 0.0
        for _ in range(self.iters):
            p = 1.0 / (1.0 + np.exp(-np.clip(Xb @ w, -30, 30)))
            g = Xb.T @ (p - y) + R @ w
            H = (Xb * (p * (1 - p))[:, None]).T @ Xb + R + 1e-9 * np.eye(len(w))
            step = np.linalg.solve(H, g)
            w -= step
            if np.abs(step).max() < 1e-8:
                break
        self.w = w
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-np.clip(np.hstack([np.ones((len(X), 1)), X]) @ self.w, -30, 30)))


class _Tree:
    """Regression tree on gradients with Newton leaf values (XGBoost-style gain, lambda L2 on leaves)."""

    def __init__(self, depth: int, min_leaf: int, lam: float, n_thresholds: int):
        self.depth, self.min_leaf, self.lam, self.n_thr = depth, min_leaf, lam, n_thresholds

    def fit(self, X, g, h):
        self.node = self._grow(X, g, h, np.arange(len(g)), 0)
        return self

    def _leaf(self, g, h, idx):
        return ("leaf", -g[idx].sum() / (h[idx].sum() + self.lam))

    def _grow(self, X, g, h, idx, d):
        if d >= self.depth or len(idx) < 2 * self.min_leaf:
            return self._leaf(g, h, idx)
        G, H = g[idx].sum(), h[idx].sum()
        base = G * G / (H + self.lam)
        best = (1e-12, None, None)
        for j in range(X.shape[1]):
            xs = X[idx, j]
            qs = np.unique(np.quantile(xs, np.linspace(0, 1, self.n_thr + 2)[1:-1]))
            for t in qs:
                left = xs <= t
                nl = int(left.sum())
                if nl < self.min_leaf or len(idx) - nl < self.min_leaf:
                    continue
                gl, hl = g[idx][left].sum(), h[idx][left].sum()
                gain = gl * gl / (hl + self.lam) + (G - gl) ** 2 / (H - hl + self.lam) - base
                if gain > best[0]:
                    best = (gain, j, float(t))
        if best[1] is None:
            return self._leaf(g, h, idx)
        _, j, t = best
        m = X[idx, j] <= t
        return ("split", j, t, self._grow(X, g, h, idx[m], d + 1), self._grow(X, g, h, idx[~m], d + 1))

    def predict(self, X):
        out = np.empty(len(X))
        for i, x in enumerate(X):
            n = self.node
            while n[0] == "split":
                n = n[3] if x[n[1]] <= n[2] else n[4]
            out[i] = n[1]
        return out


class GBDT:
    """Gradient-boosted trees with logistic loss (deterministic: no row/column subsampling)."""

    def __init__(self, n_estimators: int = 100, learning_rate: float = 0.1, depth: int = 3, min_leaf: int = 5,
                 lam: float = 1.0, n_thresholds: int = 16):
        self.n, self.lr, self.depth, self.min_leaf, self.lam, self.n_thr = (n_estimators, learning_rate, depth,
                                                                            min_leaf, lam, n_thresholds)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GBDT":
        p0 = min(1 - 1e-6, max(1e-6, float(y.mean())))
        self.f0 = math.log(p0 / (1 - p0))
        f = np.full(len(y), self.f0)
        self.trees = []
        for _ in range(self.n):
            p = 1.0 / (1.0 + np.exp(-f))
            t = _Tree(self.depth, self.min_leaf, self.lam, self.n_thr).fit(X, p - y, np.maximum(p * (1 - p), 1e-9))
            f += self.lr * t.predict(X)
            self.trees.append(t)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        f = np.full(len(X), self.f0)
        for t in self.trees:
            f += self.lr * t.predict(X)
        return 1.0 / (1.0 + np.exp(-f))


def rule_scores(rows: List[Dict]) -> np.ndarray:
    """Rule baseline (no training, protocol §5): low quoted price + billed-tokens anomaly, both relative to the
    sellers in the SAME run that declare the SAME model (peer group):
        score = z(-quoted_price_mean) + z(billed_tokens_mean)       (z within the peer group; 0 if group size 1)
    A seller that undercuts its peers and bills more tokens than them per purchase ranks high. Uses only whitelisted
    columns (no latency, no answer length), so it is identical in the 7- and 6-feature settings."""
    groups: Dict[Tuple, List[int]] = {}
    for i, r in enumerate(rows):
        groups.setdefault((r.get("run_id"), r.get("declared_model")), []).append(i)
    out = np.zeros(len(rows))
    for idx in groups.values():
        for col, sign in (("quoted_price_mean", -1.0), ("billed_tokens_mean", 1.0)):
            v = np.array([_num(rows[i].get(col)) for i in idx], dtype=float)
            if np.isnan(v).all():
                continue
            v = np.where(np.isnan(v), np.nanmedian(v), v)
            sd = v.std()
            if len(idx) > 1 and sd > 1e-12:
                out[idx] += sign * (v - v.mean()) / sd
    return out
