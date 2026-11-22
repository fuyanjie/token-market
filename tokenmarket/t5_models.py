"""Official T5 learners, online routing policies, and post-hoc oracle observer.

Follows docs/PROTOCOL_T5.md (frozen 2026-11-22) §1, §3, §4, §5, §6 strictly.
Reuses LogisticRegression and GBDT from tokenmarket.t4_models with identical frozen hyperparameters.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Sequence, Set, Tuple

import numpy as np

from .backends import task_max_new_tokens
from .t4_models import GBDT, LogisticRegression
from .t5_export import (
    BEHAVIOR_EPSILON,
    CATEGORICAL,
    FEATURE_COLUMNS,
    T5HistoryTracker,
    assert_public_features,
    build_candidate_feature_row,
    listed_quality,
    seller_key,
    task_prompt_sha256,
)


def _num(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


class T5Encoder:
    """Deterministic feature encoder matching T4 conventions (train-median impute, standardize, one-hot)."""

    def __init__(self, columns: Sequence[str] = FEATURE_COLUMNS):
        assert_public_features(columns, allow_keys=False)
        self.columns = list(columns)
        self.cat = [c for c in self.columns if c in CATEGORICAL]
        self.num = [c for c in self.columns if c not in CATEGORICAL]
        self.med: Dict[str, float] = {}
        self.mu: Dict[str, float] = {}
        self.sd: Dict[str, float] = {}
        self.vocab: Dict[str, List[str]] = {}

    def fit(self, rows: Sequence[Dict]) -> "T5Encoder":
        self.med, self.mu, self.sd = {}, {}, {}
        for c in self.num:
            vals = [x for x in (_num(r.get(c)) for r in rows) if x is not None]
            self.med[c] = float(np.median(vals)) if vals else 0.0
            filled = np.array([
                x if (x := _num(r.get(c))) is not None else self.med[c]
                for r in rows
            ], dtype=float)
            self.mu[c] = float(filled.mean()) if len(filled) else 0.0
            sd = float(filled.std()) if len(filled) else 0.0
            self.sd[c] = sd if sd > 1e-12 else 1.0
        self.vocab = {c: sorted({str(r.get(c)) for r in rows}) for c in self.cat}
        return self

    def names(self) -> List[str]:
        return list(self.num) + [f"{c}={v}" for c in self.cat for v in self.vocab[c]]

    def transform(self, rows: Sequence[Dict]) -> np.ndarray:
        n_cols = len(self.names())
        X = np.zeros((len(rows), n_cols), dtype=float)
        for i, r in enumerate(rows):
            for j, c in enumerate(self.num):
                x = _num(r.get(c))
                X[i, j] = ((x if x is not None else self.med[c]) - self.mu[c]) / self.sd[c]
            k = len(self.num)
            for c in self.cat:
                v = str(r.get(c))
                for vv in self.vocab[c]:
                    if v == vv:
                        X[i, k] = 1.0
                    k += 1
        return X


class TwoStageRecommender:
    """Protocol §3/§4 two-stage recommender: P(correct and not attacked | x) >= tau -> min expected billed cost."""

    def __init__(
        self,
        model_kind: str,
        tau: float,
        fallback_model_billed: Dict[str, float],
        fallback_global_billed: float,
        columns: Sequence[str] = FEATURE_COLUMNS,
    ):
        if model_kind not in ("logreg", "gbdt"):
            raise ValueError(f"unsupported model_kind {model_kind!r}")
        assert_public_features(columns, allow_keys=False)
        self.model_kind = model_kind
        self.tau = float(tau)
        self.fallback_model_billed = dict(fallback_model_billed)
        self.fallback_global_billed = float(fallback_global_billed)
        self.columns = list(columns)
        self.encoder = T5Encoder(self.columns)
        # Exact T4 default hyperparameters (Protocol §3)
        self.model = (
            LogisticRegression(l2=1.0, iters=50)
            if model_kind == "logreg"
            else GBDT(n_estimators=100, learning_rate=0.1, depth=3, min_leaf=5, lam=1.0, n_thresholds=16)
        )

    def fit(self, feature_rows: Sequence[Dict], y: Sequence[int]) -> "TwoStageRecommender":
        self.encoder.fit(feature_rows)
        X = self.encoder.transform(feature_rows)
        y_arr = np.asarray(y, dtype=float)
        self.model.fit(X, y_arr)
        return self

    def predict_proba(self, feature_rows: Sequence[Dict]) -> np.ndarray:
        if not feature_rows:
            return np.zeros(0, dtype=float)
        X = self.encoder.transform(feature_rows)
        return self.model.predict(X)

    def clone_with_tau(self, tau: float) -> "TwoStageRecommender":
        """Share the already-fitted encoder and model with a different decision threshold tau."""
        obj = TwoStageRecommender(
            self.model_kind, tau, self.fallback_model_billed, self.fallback_global_billed, self.columns
        )
        obj.encoder = self.encoder
        obj.model = self.model
        return obj


def _select_strongest(run_id: str, task, cands: Sequence, cfg: Dict):
    """Protocol §4 strongest eligible: highest listed_quality, then lowest list_price, then seller_key."""
    return min(
        cands,
        key=lambda s: (
            -listed_quality(cfg, s.claimed_model, int(task.difficulty)),
            float(s.price_per_1k),
            seller_key(run_id, s.id),
        ),
    )


def _select_cheapest(run_id: str, cands: Sequence, history: T5HistoryTracker):
    """Protocol §4 cheapest eligible: lowest expected billed cost, then lowest list_price, then seller_key."""
    return min(
        cands,
        key=lambda s: (
            history.expected_billed_cost(s),
            float(s.price_per_1k),
            seller_key(run_id, s.id),
        ),
    )


class _BaseT5Policy:
    def __init__(self, cfg: Dict, seed: int, history: T5HistoryTracker):
        self.cfg = cfg
        self.seed = int(seed)
        self.history = history

    def on_round(self, rnd: int) -> None:
        self.history.on_round(rnd)

    def after_task(self, rnd: int, lines: Sequence[Dict]) -> None:
        for rec in lines:
            if rec.get("status") == "allowed" and rec.get("seller_id") is not None:
                self.history.record_served(
                    rnd, rec["seller_id"], rec["claimed_model"], float(rec["billed_tokens"])
                )


class T5BehaviorPolicy(_BaseT5Policy):
    """Protocol §1 frozen training behavior policy: eps=0.20 uniform random eligible, else strongest eligible."""

    def __init__(self, cfg: Dict, seed: int, epsilon: float = BEHAVIOR_EPSILON):
        super().__init__(cfg, seed, T5HistoryTracker())
        self.epsilon = float(epsilon)

    def choose(self, run_id: str, rnd: int, task, buyer, cands: Sequence):
        if not cands:
            return None
        rng = random.Random(f"t5-behavior-{run_id}-{task.task_id}")
        if rng.random() < self.epsilon:
            ordered = sorted(cands, key=lambda s: seller_key(run_id, s.id))
            return rng.choice(ordered)
        return _select_strongest(run_id, task, cands, self.cfg)


class T5TwoStagePolicy(_BaseT5Policy):
    """Protocol §3/§4 online two-stage recommender policy."""

    def __init__(self, cfg: Dict, seed: int, recommender: TwoStageRecommender):
        history = T5HistoryTracker(
            fallback_model_billed=recommender.fallback_model_billed,
            fallback_global_billed=recommender.fallback_global_billed,
        )
        super().__init__(cfg, seed, history)
        self.recommender = recommender

    def choose(self, run_id: str, rnd: int, task, buyer, cands: Sequence):
        if not cands:
            return None
        rows = [
            build_candidate_feature_row(run_id, self.seed, task, buyer, s, self.cfg, self.history, is_eligible=1)
            for s in cands
        ]
        probs = self.recommender.predict_proba(rows)
        tau = self.recommender.tau
        passing = [(s, float(p)) for s, p in zip(cands, probs) if float(p) >= tau]
        if passing:
            # Lowest expected billed cost, then lowest list_price, then seller_key
            return min(
                passing,
                key=lambda sp: (
                    self.history.expected_billed_cost(sp[0]),
                    float(sp[0].price_per_1k),
                    seller_key(run_id, sp[0].id),
                ),
            )[0]
        # Fallback (§3): highest predicted p; ties broken by §4 tie-break (lowest ebc, lowest list_price, seller_key)
        return min(
            zip(cands, probs),
            key=lambda sp: (
                -float(sp[1]),
                self.history.expected_billed_cost(sp[0]),
                float(sp[0].price_per_1k),
                seller_key(run_id, sp[0].id),
            ),
        )[0]


class T5CheapestPolicy(_BaseT5Policy):
    """Protocol §4 cheapest eligible baseline."""

    def __init__(self, cfg: Dict, seed: int, fallback_model_billed: Dict[str, float], fallback_global_billed: float):
        super().__init__(cfg, seed, T5HistoryTracker(fallback_model_billed, fallback_global_billed))

    def choose(self, run_id: str, rnd: int, task, buyer, cands: Sequence):
        if not cands:
            return None
        return _select_cheapest(run_id, cands, self.history)


class T5StrongestPolicy(_BaseT5Policy):
    """Protocol §4 strongest eligible baseline."""

    def __init__(self, cfg: Dict, seed: int):
        super().__init__(cfg, seed, T5HistoryTracker())

    def choose(self, run_id: str, rnd: int, task, buyer, cands: Sequence):
        if not cands:
            return None
        return _select_strongest(run_id, task, cands, self.cfg)


class T5RandomPolicy(_BaseT5Policy):
    """Protocol §4 random eligible baseline using random.Random(f't5-random-{run_id}-{task_id}')."""

    def __init__(self, cfg: Dict, seed: int):
        super().__init__(cfg, seed, T5HistoryTracker())

    def choose(self, run_id: str, rnd: int, task, buyer, cands: Sequence):
        if not cands:
            return None
        ordered = sorted(cands, key=lambda s: seller_key(run_id, s.id))
        rng = random.Random(f"t5-random-{run_id}-{task.task_id}")
        return rng.choice(ordered)


class T5RunObserver:
    """Side-effect-free observer attached to sim.run_single for:
    1) capturing strictly pre-decision feature rows during training-log collection,
    2) evaluating the frozen §6 post-hoc incomplete oracle on the exact decision-time cands,
    3) computing full-task and 15-prompt hold-out subset metrics identically for all 7 methods.
    """

    def __init__(
        self,
        cfg: Dict,
        seed: int,
        cache,
        holdout_hashes: Set[str],
        fallback_model_billed: Optional[Dict[str, float]] = None,
        fallback_global_billed: Optional[float] = None,
        collect_training: bool = False,
    ):
        self.cfg = cfg
        self.seed = int(seed)
        self.cache = cache
        self.holdout_hashes = set(holdout_hashes)
        self.collect_training = bool(collect_training)
        self.history = T5HistoryTracker(fallback_model_billed, fallback_global_billed)
        lc = cfg.get("backends", {}).get("local_hf", {})
        self.max_new_tokens = int(lc.get("max_new_tokens", 256))
        self.long_max_new_tokens = int(lc.get("long_max_new_tokens", self.max_new_tokens))

        self._cur_run_id: str = ""
        self._cur_rnd: int = 0
        self._cur_cand_feats: Dict[str, Dict] = {}
        self._cur_cand_ebc: Dict[str, float] = {}
        self._cur_oracle: Optional[Tuple[bool, float]] = None
        self._cur_is_holdout: bool = False
        self._cur_prompt_hash: str = ""

        self.train_features: List[Dict] = []
        self.train_labels: List[Dict] = []
        self.task_records: List[Dict] = []

    def on_round(self, rnd: int) -> None:
        self.history.on_round(rnd)

    def _compute_oracle(self, run_id: str, task, cands: Sequence) -> Optional[Tuple[bool, float]]:
        """Protocol §6 frozen incomplete post-hoc oracle:
        - Restrict to compliant eligible NON-STRATEGIC sellers with deterministic cache hit
          (exclude strategic sellers and mock / missing cache).
        - Among cache-correct sellers, pick lowest decision-time expected billed cost
          (tie: lower list_price, then seller_key).
        - If none is cache-correct, pick strongest eligible among those honest cached sellers.
        """
        if self.cache is None or not cands:
            return None
        mnt = task_max_new_tokens(task, self.max_new_tokens, self.long_max_new_tokens)
        prompt_text = None
        honest_cached = []
        for s in cands:
            if s.strategy is not None or s.is_model_swap:
                continue
            if s.backend != "local_hf":
                continue
            if prompt_text is None:
                from .backends import render_task_prompt
                prompt_text = render_task_prompt(task)
            rec = self.cache.get(s.claimed_model, prompt_text, mnt)
            if rec is None:
                continue
            ans = rec.get("parsed_answer")
            ok = (ans is not None and int(ans) == task.gold)
            honest_cached.append((s, ok, self.history.expected_billed_cost(s)))
        if not honest_cached:
            return None
        correct_ones = [x for x in honest_cached if x[1]]
        if correct_ones:
            best = min(correct_ones, key=lambda x: (x[2], float(x[0].price_per_1k), seller_key(run_id, x[0].id)))
        else:
            best = min(
                honest_cached,
                key=lambda x: (
                    -listed_quality(self.cfg, x[0].claimed_model, int(task.difficulty)),
                    float(x[0].price_per_1k),
                    seller_key(run_id, x[0].id),
                ),
            )
        return bool(best[1]), float(best[2])

    def before_task(self, run_id: str, rnd: int, task, buyer, cands: Sequence, reason: Optional[str]) -> None:
        self._cur_run_id = run_id
        self._cur_rnd = int(rnd)
        self._cur_prompt_hash = task_prompt_sha256(task)
        self._cur_is_holdout = self._cur_prompt_hash in self.holdout_hashes
        self._cur_cand_feats = {}
        self._cur_cand_ebc = {}
        if not reason and cands:
            for s in cands:
                self._cur_cand_ebc[s.id] = self.history.expected_billed_cost(s)
                if self.collect_training:
                    self._cur_cand_feats[s.id] = build_candidate_feature_row(
                        run_id, self.seed, task, buyer, s, self.cfg, self.history, is_eligible=1
                    )
            self._cur_oracle = self._compute_oracle(run_id, task, cands)
        else:
            self._cur_oracle = None

    def after_task(self, rnd: int, task, lines: Sequence[Dict]) -> None:
        served = [r for r in lines if r.get("status") == "allowed"]
        last = lines[-1]
        final_correct = bool(last.get("final_correct"))
        cost_incl_audit = sum(float(r.get("actual_cost", 0.0)) + float(r.get("audit_cost", 0.0)) for r in lines)
        n_viol = sum(1 for r in served if r.get("violation"))
        n_attacked = sum(1 for r in served if (r.get("attack_mode") or "none") != "none")
        policy_ebc = (
            self._cur_cand_ebc.get(served[0]["seller_id"])
            if len(served) == 1 and served[0].get("seller_id") in self._cur_cand_ebc
            else None
        )
        self.task_records.append({
            "task_id": task.task_id,
            "round": int(rnd),
            "is_holdout": self._cur_is_holdout,
            "final_correct": final_correct,
            "cost_incl_audit": cost_incl_audit,
            "n_served": len(served),
            "n_viol": n_viol,
            "n_attacked": n_attacked,
            "filled": len(served) > 0,
            "policy_ebc": policy_ebc,
            "oracle_defined": self._cur_oracle is not None,
            "oracle_correct": self._cur_oracle[0] if self._cur_oracle is not None else None,
            "oracle_ebc": self._cur_oracle[1] if self._cur_oracle is not None else None,
        })
        if self.collect_training and len(served) == 1 and not self._cur_is_holdout:
            rec = served[0]
            sid = rec["seller_id"]
            if sid in self._cur_cand_feats:
                attack_mode_str = rec.get("attack_mode") or "none"
                y = 1 if (final_correct and attack_mode_str == "none") else 0
                bt = float(rec.get("billed_tokens", 0))
                at = float(rec.get("actual_tokens", 0))
                self.train_features.append(self._cur_cand_feats[sid])
                self.train_labels.append({
                    "run_id": self._cur_run_id,
                    "seed": self.seed,
                    "round": int(rnd),
                    "task_id": task.task_id,
                    "seller_key": seller_key(self._cur_run_id, sid),
                    "seller_id": sid,
                    "prompt_sha256": self._cur_prompt_hash,
                    "y_correct_clean": y,
                    "correct": 1 if final_correct else 0,
                    "attack_mode": attack_mode_str,
                    "billed_tokens": bt,
                    "leakref_tokens_actual": at,
                    "leakref_billed_minus_actual": bt - at,
                    "leakref_latency_ms": float(rec.get("latency_ms", 0.0)),
                })
        for rec in served:
            if rec.get("seller_id") is not None:
                self.history.record_served(
                    rnd, rec["seller_id"], rec["claimed_model"], float(rec["billed_tokens"])
                )

    def summarize(self, holdout_only: Optional[bool] = None) -> Dict[str, Optional[float]]:
        """Summarize task-level metrics over all tasks (None), holdout-only (True), or non-holdout (False)."""
        if holdout_only is None:
            rows = self.task_records
        else:
            rows = [r for r in self.task_records if r["is_holdout"] is holdout_only]
        n = len(rows)
        if n == 0:
            return {
                "n_tasks": 0, "accuracy": None, "cost_per_task": None, "violation_rate": None,
                "E": None, "fill_rate": None, "oracle_defined_rate": None,
                "oracle_accuracy": None, "oracle_ebc": None,
                "oracle_accuracy_regret": None, "oracle_cost_regret": None, "oracle_ebc_regret": None,
            }
        n_served = sum(r["n_served"] for r in rows)
        n_att = sum(r["n_attacked"] for r in rows)
        n_viol = sum(r["n_viol"] for r in rows)
        accuracy = sum(1.0 for r in rows if r["final_correct"]) / n
        cost_per_task = sum(r["cost_incl_audit"] for r in rows) / n
        violation_rate = n_viol / n
        E = (n_att / n_served) if n_served > 0 else 0.0
        fill_rate = sum(1.0 for r in rows if r["filled"]) / n

        odef = [r for r in rows if r["oracle_defined"]]
        od_rate = len(odef) / n
        if odef:
            o_acc = sum(1.0 for r in odef if r["oracle_correct"]) / len(odef)
            o_ebc = sum(r["oracle_ebc"] for r in odef) / len(odef)
            p_acc_od = sum(1.0 for r in odef if r["final_correct"]) / len(odef)
            p_cost_od = sum(r["cost_incl_audit"] for r in odef) / len(odef)
            o_acc_reg = o_acc - p_acc_od
            o_cost_reg = p_cost_od - o_ebc
            ebcs = [r for r in odef if r["policy_ebc"] is not None]
            o_ebc_reg = (
                (sum(r["policy_ebc"] - r["oracle_ebc"] for r in ebcs) / len(ebcs))
                if ebcs else None
            )
        else:
            o_acc = o_ebc = o_acc_reg = o_cost_reg = o_ebc_reg = None
        return {
            "n_tasks": n,
            "n_served": n_served,
            "accuracy": accuracy,
            "cost_per_task": cost_per_task,
            "violation_rate": violation_rate,
            "E": E,
            "fill_rate": fill_rate,
            "oracle_defined_rate": od_rate,
            "oracle_accuracy": o_acc,
            "oracle_ebc": o_ebc,
            "oracle_accuracy_regret": o_acc_reg,
            "oracle_cost_regret": o_cost_reg,
            "oracle_ebc_regret": o_ebc_reg,
        }
