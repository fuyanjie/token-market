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


def test_t5_audit_wiring_isolation_and_audited_policies_unchanged():
    """T5 policies/PILOT/StageRoute must stay out of AUDITED_POLICIES and audit_v11 must stay off,
    while T5 config gets v1.0 fixed audit a=0.10 (identity+length) without altering ordinary T1/T2/T4."""
    from tokenmarket.audit_v1 import audit_rule, audit_v11, trust_feedback_on
    from tokenmarket.portfolio import AUDITED_POLICIES
    from tokenmarket.sim import policy_audit_checks, policy_audit_rate

    _runner_spec = importlib.util.spec_from_file_location("run_t5_eval", ROOT / "scripts/run_t5_eval.py")
    _runner_mod = importlib.util.module_from_spec(_runner_spec)
    _runner_spec.loader.exec_module(_runner_mod)

    # AUDITED_POLICIES must remain strictly D3 policies only (no cascade/trust leak to T5/PILOT/StageRoute)
    assert AUDITED_POLICIES == ("audited_compliance_cascade", "audited_cascade_unfiltered")
    for p in ("t5_recommender_compliant", "pilot_v1_compliant", "stageroute_v1_compliant",
              "single_cheapest_compliant", "single_best_compliant"):
        assert p not in AUDITED_POLICIES

    base = load_config(str(ROOT / "configs/v1.0/scale.yaml"))
    assert audit_v11(base) is None

    # Ordinary non-T5 runs on scale.yaml MUST keep legacy rates/checks untouched (T1/T2/T4 safety)
    for p in ("pilot_v1_compliant", "stageroute_v1_compliant", "single_cheapest_compliant", "single_best_compliant"):
        assert policy_audit_rate(base, p) == 0.0
        assert policy_audit_checks(base, p) == ["identity"]
        assert audit_rule(base, p, AUDITED_POLICIES) == "fixed"
        assert trust_feedback_on(base, p, AUDITED_POLICIES) is False

    # T5 runner config (_t5_cfg) must give fixed a=0.10 and both checks to all T5 eval/train policies
    t5_cfg = _runner_mod._t5_cfg(base, 1.0, 14)
    assert audit_v11(t5_cfg) is None
    for p in ("t5_recommender_compliant", "pilot_v1_compliant", "stageroute_v1_compliant"):
        assert policy_audit_rate(t5_cfg, p) == pytest.approx(0.10)
        assert policy_audit_checks(t5_cfg, p) == ["identity", "length"]
        assert audit_rule(t5_cfg, p, AUDITED_POLICIES) == "fixed"
        assert trust_feedback_on(t5_cfg, p, AUDITED_POLICIES) is False


def test_t5_train_and_eval_realized_audit_rate_at_official_scale():
    """Official-scale T5 train and eval run_single paths must realize ~a=0.10 fixed audits (not 0),
    with both identity+length checks and no D3 trust/cascade dispatch."""
    _runner_spec = importlib.util.spec_from_file_location("run_t5_eval", ROOT / "scripts/run_t5_eval.py")
    _runner_mod = importlib.util.module_from_spec(_runner_spec)
    _runner_spec.loader.exec_module(_runner_mod)

    base = load_config(str(ROOT / "configs/v1.0/scale.yaml"))

    class _L:
        def __init__(self):
            self.records = []

        def write(self, r):
            self.records.append(r)

    # 1) Training path (seed 0, pi=1.0, T5BehaviorPolicy)
    cfg_tr = _runner_mod._t5_cfg(base, 1.0, 0)
    pool, cache, stats, _ = prepare(cfg_tr, None, str(ROOT / "cache/llm_outputs.jsonl"), None, lambda *a: None)
    backends = build_backends(cfg_tr, {s.get("backend", "mock") for s in cfg_tr["sellers"]}, cache)
    rep = Reputation(cfg_tr["models"], stats)
    lg_tr = _L()
    m_tr = run_single(
        cfg_tr, "posted_price", "t5_recommender_compliant", 0, backends, rep, lg_tr, pool,
        t5_policy=T5BehaviorPolicy(cfg_tr, 0), run_id_override="t5__test_beh__seed0",
    )
    rate_tr = m_tr["n_audits"] / max(1, m_tr["n_purchases"])
    assert m_tr["audit_rate"] == pytest.approx(0.10)
    assert m_tr["audit_rule"] == "fixed"
    assert m_tr["audit_checks"] == ["identity", "length"]
    assert m_tr["trust_feedback"] is False
    assert "trust_q_hat" not in m_tr
    assert m_tr["purchases_per_task"] <= 1.0 + 1e-12
    assert m_tr["n_audits"] > 0 and 0.04 <= rate_tr <= 0.18
    assert all(r["audit_type"] == "both" for r in lg_tr.records if r["audited"])

    # 2) Official eval paths (seed 14, pi=1.0): t5_recommender_compliant, pilot_v1_compliant, stageroute_v1_compliant
    cfg_ev = _runner_mod._t5_cfg(base, 1.0, 14)
    backends_ev = build_backends(cfg_ev, {s.get("backend", "mock") for s in cfg_ev["sellers"]}, cache)
    rep_ev = Reputation(cfg_ev["models"], stats)
    for sim_policy, t5_pol in (
        ("t5_recommender_compliant", T5StrongestPolicy(cfg_ev, 14)),
        ("pilot_v1_compliant", None),
        ("stageroute_v1_compliant", None),
    ):
        lg = _L()
        m = run_single(
            cfg_ev, "posted_price", sim_policy, 14, backends_ev, rep_ev, lg, pool,
            t5_policy=t5_pol, run_id_override=f"t5__test_{sim_policy}__seed14",
        )
        realized = m["n_audits"] / max(1, m["n_purchases"])
        assert m["audit_rate"] == pytest.approx(0.10)
        assert m["audit_rule"] == "fixed"
        assert m["audit_checks"] == ["identity", "length"]
        assert m["trust_feedback"] is False
        assert "trust_q_hat" not in m
        assert m["purchases_per_task"] <= 1.0 + 1e-12
        assert m["n_audits"] > 0 and 0.04 <= realized <= 0.18, f"{sim_policy}: n_audits={m['n_audits']}, realized={realized}"
        assert all(r["audit_type"] == "both" for r in lg.records if r["audited"])
