"""Official T5 (task-conditioned model/seller recommendation) feature contract, history tracker, and export.

Follows docs/PROTOCOL_T5.md (frozen 2026-11-22) §2, §3, §5 strictly.
Unit of decision: candidate seller for (run_id, task_id).
History features strictly use earlier rounds (round < current_round) within the SAME run.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import re
import statistics
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .backends import prompt_sha256, render_task_prompt

PROTOCOL_T5_SHA256 = "4301f4b281e90b1b835d1e7868e3b00c98bc8eaee382cf29f8646c6fa7272542"
SCALE_YAML_SHA256 = "780e9b961d89bad6fd520c9cbfd5710055ff2d5d3e0ff3bcfbd745709eb0da6c"

HOLDOUT_RNG_SEED = "t5-prompt-holdout-20261122"
HOLDOUT_COUNT = 15

TRAIN_SEEDS = tuple(range(0, 14))
INNER_FIT_SEEDS = tuple(range(0, 10))
INNER_VAL_SEEDS = tuple(range(10, 14))
TEST_SEEDS = tuple(range(14, 20))
EVAL_PIS = (1.0, 0.1, 0.0)
BEHAVIOR_EPSILON = 0.20
TAU_GRID = (0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90)

# Join keys only — NEVER passed into learners.
KEY_COLUMNS = ("run_id", "seed", "task_id", "seller_key")

# Locked §2 whitelist (6 task-side + 8 seller-side = 14 features).
WHITELIST: Dict[str, Tuple[str, str]] = {
    # Task-side (6)
    "task_type": ("task_side", "categorical task type"),
    "difficulty": ("task_side", "numeric task difficulty"),
    "sensitivity": ("task_side", "categorical data sensitivity"),
    "buyer_jurisdiction": ("task_side", "categorical buyer jurisdiction"),
    "budget_remaining": ("task_side", "numeric pre-decision buyer remaining budget"),
    "consent": ("task_side", "binary 0/1 specific_consent task flag"),
    # Seller-side (8)
    "claimed_model": ("seller_side", "categorical declared model"),
    "list_price": ("seller_side", "numeric posted price_per_1k"),
    "listed_quality": ("seller_side", "numeric public model accuracy at task difficulty (else mean)"),
    "seller_jurisdiction": ("seller_side", "categorical seller jurisdiction"),
    "is_eligible": ("seller_side", "binary 0/1 eligible after hard compliance filter"),
    "hist_n_served": ("seller_side", "count of served purchases by seller in rounds < current_round"),
    "hist_billed_tokens_mean": ("seller_side", "mean billed_tokens of seller in rounds < current_round (nullable)"),
    "hist_served_share": ("seller_side", "seller share of run served purchases in rounds < current_round"),
}

FEATURE_COLUMNS = tuple(WHITELIST.keys())
CATEGORICAL = ("task_type", "sensitivity", "buyer_jurisdiction", "claimed_model", "seller_jurisdiction")
NUMERIC = tuple(c for c in FEATURE_COLUMNS if c not in CATEGORICAL)

# §2 locked blacklist: exact names and regex patterns.
BLACKLIST_EXACT: Set[str] = {
    "actual_model", "tokens_actual", "actual_tokens", "reasoning_tokens", "token_inflation",
    "tokens_actual_minus_billed", "billed_minus_actual", "tokens_billed_minus_actual",
    "attack", "attack_mode", "swap_prob", "theft_prob", "downgrade_prob",
    "hit", "miss", "label_correct", "fraud_realized", "slash_amount", "delist_rounds",
    "confidence", "latency", "latency_ms", "gen_time_s",
    "gold", "correct", "final_correct", "answer", "final_answer",
    "prompt", "question", "prompt_hash", "prompt_sha256", "pool_task_id",
    "seller_id", "seller_key",
    "audited", "audit_cost", "audit_type", "swap_detected", "theft_detected",
    "escrow_held", "escrow_released", "escrow_slashed", "ban_until", "banned_until_round",
    "stake_remaining", "seller_profit", "buyer_surplus", "actual_cost", "cost_overrun",
    "y_correct_clean", "round",
}

BLACKLIST_PATTERNS: Tuple[str, ...] = (
    r"actual_model", r"tokens?_actual", r"actual_tokens?", r"reasoning_tokens?",
    r"token_inflation", r"billed_minus_actual", r"actual_minus_billed", r"token_gap",
    r"attack", r"learned_q", r"latent_q", r"fraud", r"slash", r"delist",
    r"(^|_)ban", r"escrow", r"audit", r"detected", r"(^|_)(hit|miss)(_|$)", r"label",
    r"confidence", r"latency", r"gen_time",
    r"correct", r"answer", r"gold", r"prompt", r"question", r"pool_task",
    r"seller_id", r"swap_prob", r"theft_prob", r"downgrade", r"profit", r"surplus",
    r"trust", r"q_hat", r"leakref",
)
_BL_RE = [re.compile(p, re.IGNORECASE) for p in BLACKLIST_PATTERNS]

LABEL = "y_correct_clean"
LEAKREF_COLUMNS = ("leakref_tokens_actual", "leakref_billed_minus_actual", "leakref_latency_ms")
LABEL_COLUMNS = (
    "run_id", "seed", "round", "task_id", "seller_key", "seller_id", "prompt_sha256",
    LABEL, "correct", "attack_mode", "billed_tokens",
) + LEAKREF_COLUMNS


def seller_key(run_id: str, seller_id: str) -> str:
    """Per-run seller pseudonym matching T4 (sha256(run_id|seller_id)[:12]); key & tie-break only."""
    return hashlib.sha256(f"{run_id}|{seller_id}".encode("utf-8")).hexdigest()[:12]


def task_prompt_sha256(task) -> str:
    return prompt_sha256(render_task_prompt(task))


def holdout_prompt_hashes(pool: Sequence) -> List[str]:
    """Protocol §5: sort unique prompt SHA256 hashes, draw 15 without replacement using frozen RNG seed."""
    unique_hashes = sorted({task_prompt_sha256(t) for t in pool})
    if len(unique_hashes) < HOLDOUT_COUNT:
        raise ValueError(f"pool has only {len(unique_hashes)} unique prompts, need >= {HOLDOUT_COUNT}")
    rng = random.Random(HOLDOUT_RNG_SEED)
    return sorted(rng.sample(unique_hashes, HOLDOUT_COUNT))


def listed_quality(cfg: Dict, claimed_model: str, difficulty: int) -> float:
    """Protocol §2: public listing accuracy at task difficulty if available, else mean over difficulties."""
    acc = cfg.get("models", {}).get(claimed_model, {}).get("accuracy", {})
    if not acc:
        return 0.0
    if difficulty in acc:
        return float(acc[difficulty])
    if str(difficulty) in acc:
        return float(acc[str(difficulty)])
    return float(statistics.fmean(float(v) for v in acc.values()))


def blacklist_hits(col: str) -> List[str]:
    hits = [f"exact:{col}"] if col in BLACKLIST_EXACT else []
    return hits + [f"pattern:{r.pattern}" for r in _BL_RE if r.search(col)]


def check_feature_columns(cols: Iterable[str], allow_keys: bool = True) -> List[str]:
    """Verify columns obey the locked §2 T5 whitelist and blacklist."""
    errs: List[str] = []
    for c in cols:
        if allow_keys and c in KEY_COLUMNS:
            continue
        if c not in WHITELIST:
            errs.append(f"{c}: not on T5 WHITELIST")
        bl = blacklist_hits(c)
        if bl:
            errs.append(f"{c}: T5 BLACKLIST {bl}")
    return errs


def assert_public_features(cols: Iterable[str], allow_keys: bool = True) -> None:
    errs = check_feature_columns(cols, allow_keys=allow_keys)
    if errs:
        raise ValueError("T5 feature columns violate whitelist/blacklist: " + "; ".join(errs))


class T5HistoryTracker:
    """Tracks strictly pre-decision (round < current_round) history within a single run.

    Observations from round `r` are buffered in `_pending` and committed only when `on_round(rnd)`
    advances past `r`, guaranteeing zero within-round or future leakage.
    """

    def __init__(self, fallback_model_billed: Optional[Dict[str, float]] = None,
                 fallback_global_billed: Optional[float] = None):
        self.fallback_model_billed: Dict[str, float] = dict(fallback_model_billed or {})
        self.fallback_global_billed: float = float(fallback_global_billed) if fallback_global_billed is not None else 150.0
        self.current_round: int = 0
        self.seller_count: Dict[str, int] = {}
        self.seller_billed_sum: Dict[str, float] = {}
        self.model_count: Dict[str, int] = {}
        self.model_billed_sum: Dict[str, float] = {}
        self.total_served: int = 0
        self._pending: List[Tuple[int, str, str, float]] = []

    def on_round(self, rnd: int) -> None:
        """Commit all buffered observations from rounds strictly < rnd."""
        rnd = int(rnd)
        self.current_round = rnd
        if not self._pending:
            return
        keep: List[Tuple[int, str, str, float]] = []
        for r, sid, model, btok in self._pending:
            if r < rnd:
                self.seller_count[sid] = self.seller_count.get(sid, 0) + 1
                self.seller_billed_sum[sid] = self.seller_billed_sum.get(sid, 0.0) + btok
                self.model_count[model] = self.model_count.get(model, 0) + 1
                self.model_billed_sum[model] = self.model_billed_sum.get(model, 0.0) + btok
                self.total_served += 1
            else:
                keep.append((r, sid, model, btok))
        self._pending = keep

    def record_served(self, rnd: int, seller_id: str, claimed_model: str, billed_tokens: float) -> None:
        self._pending.append((int(rnd), str(seller_id), str(claimed_model), float(billed_tokens)))

    def seller_hist(self, seller_id: str) -> Tuple[int, Optional[float], float]:
        n = self.seller_count.get(seller_id, 0)
        mean_bt = (self.seller_billed_sum[seller_id] / n) if n > 0 else None
        share = (n / self.total_served) if self.total_served > 0 else 0.0
        return n, mean_bt, share

    def expected_billed_tokens(self, claimed_model: str) -> float:
        """Protocol §3 expected_billed_tokens:
        1) run pre-decision window mean for claimed_model;
        2) else fitting-fold train mean for claimed_model;
        3) else fitting-fold global mean.
        """
        n = self.model_count.get(claimed_model, 0)
        if n > 0:
            return self.model_billed_sum[claimed_model] / n
        if claimed_model in self.fallback_model_billed:
            return self.fallback_model_billed[claimed_model]
        return self.fallback_global_billed

    def expected_billed_cost(self, seller) -> float:
        """Protocol §3 decision-time expected billed cost: list_price * expected_billed_tokens / 1000."""
        return float(seller.price_per_1k) * self.expected_billed_tokens(seller.claimed_model) / 1000.0


def build_candidate_feature_row(
    run_id: str,
    seed: int,
    task,
    buyer,
    seller,
    cfg: Dict,
    history: T5HistoryTracker,
    is_eligible: int = 1,
) -> Dict:
    """Build one strictly pre-decision feature row for (run_id, task_id, seller_key)."""
    n_served, mean_bt, share = history.seller_hist(seller.id)
    return {
        "run_id": run_id,
        "seed": int(seed),
        "task_id": task.task_id,
        "seller_key": seller_key(run_id, seller.id),
        "task_type": task.task_type,
        "difficulty": int(task.difficulty),
        "sensitivity": task.sensitivity,
        "buyer_jurisdiction": buyer.jurisdiction,
        "budget_remaining": float(buyer.remaining),
        "consent": 1 if "specific_consent" in getattr(task, "flags", ()) else 0,
        "claimed_model": seller.claimed_model,
        "list_price": float(seller.price_per_1k),
        "listed_quality": listed_quality(cfg, seller.claimed_model, int(task.difficulty)),
        "seller_jurisdiction": seller.jurisdiction,
        "is_eligible": int(is_eligible),
        "hist_n_served": int(n_served),
        "hist_billed_tokens_mean": mean_bt,
        "hist_served_share": float(share),
    }


def compute_billed_token_fallbacks(feature_rows: Sequence[Dict], label_rows: Sequence[Dict]) -> Tuple[Dict[str, float], float]:
    """Compute fitting-fold per-claimed_model and global billed_tokens means strictly from training rows."""
    by_model: Dict[str, List[float]] = {}
    all_bt: List[float] = []
    for f, lab in zip(feature_rows, label_rows):
        bt = float(lab["billed_tokens"])
        m = str(f["claimed_model"])
        by_model.setdefault(m, []).append(bt)
        all_bt.append(bt)
    model_means = {m: float(statistics.fmean(vs)) for m, vs in sorted(by_model.items()) if vs}
    global_mean = float(statistics.fmean(all_bt)) if all_bt else 150.0
    return model_means, global_mean


def _write_csv(path: str, rows: Sequence[Dict], cols: Sequence[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            w.writerow(["" if r.get(c) is None else r[c] for c in cols])


def write_t5_export(
    feature_rows: Sequence[Dict],
    label_rows: Sequence[Dict],
    out_dir: str,
    holdout_hashes: Sequence[str],
    extra_meta: Optional[Dict] = None,
) -> Dict:
    """Write label-stripped training features + separate labels + manifest."""
    cols = list(KEY_COLUMNS) + list(FEATURE_COLUMNS)
    assert_public_features(cols, allow_keys=True)
    os.makedirs(out_dir, exist_ok=True)
    feat_path = os.path.join(out_dir, "features_train.csv")
    lab_path = os.path.join(out_dir, "labels_train.csv")
    _write_csv(feat_path, feature_rows, cols)
    _write_csv(lab_path, label_rows, LABEL_COLUMNS)
    manifest = {
        "task": "T5 task-conditioned model/seller recommendation (docs/PROTOCOL_T5.md)",
        "protocol_sha256": PROTOCOL_T5_SHA256,
        "scale_yaml_sha256": SCALE_YAML_SHA256,
        "unit": "(run_id, task_id, seller_key)",
        "label": LABEL,
        "label_definition": "1 iff final_correct and attack_mode == 'none' on served purchase; else 0",
        "key_columns": list(KEY_COLUMNS),
        "feature_columns": list(FEATURE_COLUMNS),
        "categorical_columns": list(CATEGORICAL),
        "numeric_columns": list(NUMERIC),
        "whitelist": {k: list(v) for k, v in WHITELIST.items()},
        "blacklist_exact": sorted(BLACKLIST_EXACT),
        "blacklist_patterns": list(BLACKLIST_PATTERNS),
        "holdout_rng_seed": HOLDOUT_RNG_SEED,
        "holdout_prompt_hashes": list(holdout_hashes),
        "n_train_rows": len(feature_rows),
        "n_train_pos": sum(int(r[LABEL]) for r in label_rows),
        "train_seeds": sorted({int(r["seed"]) for r in feature_rows}),
        **(extra_meta or {}),
    }
    manifest_path = os.path.join(out_dir, "t5_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    return {
        "features_train": feat_path,
        "labels_train": lab_path,
        "manifest": manifest_path,
    }
