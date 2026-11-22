"""Unit tests for frozen T5 protocol implementation (docs/PROTOCOL_T5.md)."""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import random
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("check_t5_leakage", ROOT / "scripts/check_t5_leakage.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
check_t5_leakage = _mod.check

from tokenmarket.config import load_config
from tokenmarket.roster import materialize
from tokenmarket.sellers import Reputation
from tokenmarket.sim import build_backends, prepare, run_single
from tokenmarket.t5_export import (
    FEATURE_COLUMNS,
    HOLDOUT_COUNT,
    KEY_COLUMNS,
    LABEL,
    PROTOCOL_T5_SHA256,
    SCALE_YAML_SHA256,
    T5HistoryTracker,
    blacklist_hits,
    check_feature_columns,
    holdout_prompt_hashes,
    seller_key,
    write_t5_export,
)
from tokenmarket.t5_models import (
    T5BehaviorPolicy,
    T5CheapestPolicy,
    T5RandomPolicy,
    T5RunObserver,
    T5StrongestPolicy,
    T5TwoStagePolicy,
    TwoStageRecommender,
)
from tokenmarket.tasks import build_task_pool


def test_t5_whitelist_and_blacklist():
    assert len(FEATURE_COLUMNS) == 14
    assert check_feature_columns(list(KEY_COLUMNS) + list(FEATURE_COLUMNS), allow_keys=True) == []
    # Forbidden columns must fail
    for bad in (
        "actual_model", "tokens_actual", "billed_minus_actual", "attack_mode",
        "learned_q_swap", "hit", "miss", "label_correct", "fraud_realized",
        "slash_amount", "delist_rounds", "confidence", "latency_ms", "gold",
        "correct", "prompt", "prompt_sha256", "pool_task_id", "seller_id",
    ):
        assert blacklist_hits(bad), f"expected blacklist hit for {bad}"
        assert check_feature_columns([bad], allow_keys=True), f"expected column rejection for {bad}"
    # seller_key is allowed as join key, NEVER as learner feature
    assert check_feature_columns(["seller_key"], allow_keys=False)


def test_t5_holdout_prompt_draw_matches_protocol():
    cfg = load_config(str(ROOT / "configs/v1.0/scale.yaml"))
    pool = build_task_pool(cfg)
    assert len(pool) == 80
    h1 = holdout_prompt_hashes(pool)
    h2 = holdout_prompt_hashes(pool)
    assert len(h1) == HOLDOUT_COUNT == 15
    assert h1 == h2


def test_t5_history_strictly_earlier_rounds():
    h = T5HistoryTracker(fallback_model_billed={"mA": 120.0}, fallback_global_billed=100.0)
    h.on_round(0)
    assert h.seller_hist("s01") == (0, None, 0.0)
    assert h.expected_billed_tokens("mA") == 120.0
    assert h.expected_billed_tokens("mB") == 100.0

    # Record in round 0 — must NOT be visible in round 0!
    h.record_served(0, "s01", "mA", 200.0)
    assert h.seller_hist("s01") == (0, None, 0.0)
    assert h.expected_billed_tokens("mA") == 120.0

    # Advance to round 1 — round 0 observations now visible
    h.on_round(1)
    assert h.seller_hist("s01") == (1, 200.0, 1.0)
    assert h.expected_billed_tokens("mA") == 200.0

    # Record in round 1 — must NOT be visible in round 1
    h.record_served(1, "s02", "mA", 100.0)
    assert h.seller_hist("s01") == (1, 200.0, 1.0)
    assert h.seller_hist("s02") == (0, None, 0.0)
    h.on_round(2)
    assert h.seller_hist("s01") == (1, 200.0, 0.5)
    assert h.seller_hist("s02") == (1, 100.0, 0.5)
    assert h.expected_billed_tokens("mA") == 150.0


def test_t5_leakage_checker_catches_bad_columns_and_leaks(tmp_path):
    cfg = materialize(load_config(str(ROOT / "configs/v1.0/scale.yaml")), 0)
    cfg["run"]["n_tasks"] = 40
    cfg["run"]["n_rounds"] = 4
    pool, cache, stats, _ = prepare(cfg, "mock", str(ROOT / "cache/llm_outputs.jsonl"), None, lambda *a: None)
    backends = build_backends(cfg, {"mock"}, cache)
    rep = Reputation(cfg["models"], stats)
    holdout = holdout_prompt_hashes(pool)

    class _L:
        def write(self, r):
            pass

    pol = T5BehaviorPolicy(cfg, 0)
    obs = T5RunObserver(cfg, 0, cache, set(holdout), collect_training=True)
    run_single(
        cfg, "posted_price", "t5_recommender_compliant", 0, backends, rep, _L(), pool,
        backend_override="mock", t5_policy=pol, run_id_override="t5__beh__seed0", t5_observer=obs,
    )
    assert len(obs.train_features) > 0
    exp = write_t5_export(obs.train_features, obs.train_labels, str(tmp_path / "ok"), holdout)
    offenders, _, _ = check_t5_leakage([exp["features_train"]], [exp["labels_train"]], exp["manifest"])
    assert offenders == [], f"clean export failed leakage check: {offenders}"

    # Inject a blacklisted column into features_train.csv -> must fail
    bad_f = tmp_path / "bad_features.csv"
    with open(exp["features_train"], encoding="utf-8") as src, open(bad_f, "w", encoding="utf-8", newline="") as dst:
        rd = csv.DictReader(src)
        cols = list(rd.fieldnames) + ["latency_ms"]
        wr = csv.DictWriter(dst, cols)
        wr.writeheader()
        for r in rd:
            r["latency_ms"] = "123.0"
            wr.writerow(r)
    off2, _, _ = check_t5_leakage([str(bad_f)], [exp["labels_train"]], exp["manifest"])
    assert any("latency_ms" in o for o in off2)

    # Inject a test seed (14) into features_train.csv -> must fail
    bad_s = tmp_path / "bad_seed.csv"
    with open(exp["features_train"], encoding="utf-8") as src, open(bad_s, "w", encoding="utf-8", newline="") as dst:
        rd = csv.DictReader(src)
        wr = csv.DictWriter(dst, rd.fieldnames)
        wr.writeheader()
        for i, r in enumerate(rd):
            if i == 0:
                r["seed"] = "14"
            wr.writerow(r)
    off3, _, _ = check_t5_leakage([str(bad_s)], [exp["labels_train"]], exp["manifest"])
    assert any("test seeds" in o for o in off3)


def test_t5_online_policies_and_oracle_with_cache():
    cfg = materialize(load_config(str(ROOT / "configs/v1.0/scale.yaml")), 14)
    cfg["run"]["n_tasks"] = 40
    cfg["run"]["n_rounds"] = 4
    pool, cache, stats, _ = prepare(cfg, None, str(ROOT / "cache/llm_outputs.jsonl"), None, lambda *a: None)
    backends = build_backends(cfg, {s.get("backend", "mock") for s in cfg["sellers"]}, cache)
    rep = Reputation(cfg["models"], stats)
    holdout = set(holdout_prompt_hashes(pool))

    class _L:
        def write(self, r):
            pass

    for pol_cls in (
        lambda: T5StrongestPolicy(cfg, 14),
        lambda: T5CheapestPolicy(cfg, 14, {}, 140.0),
        lambda: T5RandomPolicy(cfg, 14),
    ):
        obs = T5RunObserver(cfg, 14, cache, holdout, fallback_global_billed=140.0)
        m = run_single(
            cfg, "posted_price", "t5_recommender_compliant", 14, backends, rep, _L(), pool,
            t5_policy=pol_cls(), run_id_override="t5__test__seed14", t5_observer=obs,
        )
        s_all = obs.summarize(holdout_only=None)
        assert s_all["n_tasks"] == 40
        assert abs(s_all["accuracy"] - m["task_accuracy"]) < 1e-12
        assert s_all["oracle_defined_rate"] is not None and s_all["oracle_defined_rate"] > 0.5
        assert s_all["violation_rate"] == 0.0
