"""v4 tests: imperfect detection, token-theft seller, length auditor, joint objective (mock only, fast)."""
import math
import os
import random
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tokenmarket.backends import Backend, BackendResult, MockLLM  # noqa: E402
from tokenmarket.config import load_config  # noqa: E402
from tokenmarket.experiments import interp_curve  # noqa: E402
from tokenmarket.logging_schema import FIELDS, validate_record  # noqa: E402
from tokenmarket.sim import joint_objective  # noqa: E402
from tokenmarket.strategic import (AttackStrategy, IdentityCheckDetector, SwapStrategy, TokenLengthAuditor,  # noqa: E402
                                   analytic_threshold, billed_tokens)
from tokenmarket.tasks import Task  # noqa: E402

from test_v3 import _run  # noqa: E402

SG = "seller_sg"


@pytest.fixture(scope="module")
def cfg():
    return load_config(os.path.join(ROOT, "configs", "default.yaml"))


def _sg(recs):
    return [r for r in recs if r["seller_id"] == SG and r["status"] == "allowed"]


# ---------------------------------------------------------------- imperfect detection
def test_analytic_threshold_decreases_in_detect_prob():
    ds = [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
    a = [analytic_threshold(0.01, d, 0.5) for d in ds]
    assert all(x > y for x, y in zip(a, a[1:]))                    # strictly decreasing in d
    assert a[2] == pytest.approx(2 * a[-1])                         # a*(d) = a*(1) / d
    assert analytic_threshold(0.01, 0.0, 0.5) == math.inf           # miss rate 1 -> no deterrence
    det = IdentityCheckDetector(0.7)
    assert det.miss_rate == pytest.approx(0.3) and det.false_positive_rate == 0.0
    rng = random.Random(0)
    assert not any(det.detect(False, rng) for _ in range(1000))     # no false positives
    hits = sum(det.detect(True, rng) for _ in range(4000)) / 4000
    assert abs(hits - 0.7) < 0.03                                   # false-negative rate ~ 1 - d


def test_learning_seller_stays_high_q_when_detection_fails(cfg):
    # a = 0.3, P = 0.5 deters at d = 0.9 (a*d*P = 0.135 >> saving ~0.01) but NOT at d = 0.01 (0.0015 < saving)
    over = {"fraud": {"strategy": "learning", "penalty": 0.5, "detect_prob": 0.01},
            "market": {"audit": {"rate": 0.3}, "budget_multiplier": 10.0}}
    m, _, _ = _run(cfg, "single_best_compliant", over, n_tasks=720, n_rounds=72)
    assert m["learned_swap_q"][SG] > 0.85
    over["fraud"]["detect_prob"] = 0.9
    m, _, _ = _run(cfg, "single_best_compliant", over, n_tasks=720, n_rounds=72)
    assert m["learned_swap_q"][SG] < 0.1


# ---------------------------------------------------------------- token theft
def test_length_auditor_rule():
    la = TokenLengthAuditor(1.0, tol=0.1)
    rng = random.Random(0)
    assert not la.overbilled(100, 100) and not la.overbilled(110, 100)
    assert la.overbilled(111, 100) and la.detect(150, 48, rng)
    assert not la.detect(48, 48, rng)                               # honest bill never flagged
    assert TokenLengthAuditor(1.0, tol=1.0, abs_gap=20).overbilled(130, 100)   # absolute-gap rule
    assert la.overbilled(150, 150, reference=100) and not la.overbilled(100, 48, reference=100)
    half = TokenLengthAuditor(0.5, tol=0.1)
    assert half.miss_rate == 0.5
    hits = sum(half.detect(150, 48, rng) for _ in range(4000)) / 4000
    assert abs(hits - 0.5) < 0.03
    assert billed_tokens("claimed_mean", 48, 140, 142.3, 2.0) == 142
    assert billed_tokens("inflated_factor", 48, 140, 142.3, 2.0) == 280
    assert billed_tokens("claimed_mean", 300, 300, 142.3, 2.0) == 300  # never bills below actual


@pytest.mark.parametrize("d_len", [1.0, 0.5])
def test_theft_seller_bills_more_than_actual_and_is_flagged(cfg, d_len):
    over = {"fraud": {"strategy": "static", "attack_modes_enabled": ["theft"], "q_theft_static": 1.0,
                      "detect_prob_length": d_len, "penalty": 0.1, "theft_max_new_tokens": 40},
            "market": {"audit": {"rate": 1.0, "types": ["length"]}, "budget_multiplier": 10.0}}
    m, recs, c = _run(cfg, "single_best_compliant", over)
    sg = _sg(recs)
    assert sg and all(r["attack_mode"] == "theft" for r in sg)
    assert all(r["actual_model"] == r["claimed_model"] for r in sg)            # theft only: no swap
    assert all(r["actual_tokens"] == r["reasoning_tokens"] <= 40 for r in sg)
    assert all(r["billed_tokens"] > r["actual_tokens"] for r in sg)
    assert all(r["token_inflation"] == pytest.approx(r["billed_tokens"] / r["actual_tokens"]) for r in sg)
    assert all(r["cost"] == pytest.approx(r["price_per_1k"] * r["billed_tokens"] / 1000) for r in sg)
    aud = [r for r in sg if r["audited"]]
    assert aud and all(r["audit_type"] == "length" and r["swap_detected"] is None for r in aud)
    assert all(r["detect_prob_length"] == d_len and r["detect_prob_identity"] is None for r in sg)
    rate = sum(r["theft_detected"] for r in aud) / len(aud)
    assert rate == 1.0 if d_len == 1.0 else 0.35 < rate < 0.65
    # honest sellers: billed == actual, never flagged
    other = [r for r in recs if r["status"] == "allowed" and r["seller_id"] != SG]
    assert other and all(r["billed_tokens"] == r["actual_tokens"] and r["attack_mode"] == "none" for r in other)
    assert not any(r["theft_detected"] for r in other)
    assert m["thefts_served"] == len(sg) and m["buyer_overpayment"] > 0


def test_attack_mode_both_logs_both_signals(cfg):
    over = {"fraud": {"strategy": "static", "attack_modes_enabled": ["swap", "theft"], "detect_prob": 1.0,
                      "detect_prob_length": 1.0, "penalty": 0.2},
            "market": {"audit": {"rate": 1.0, "types": ["identity", "length"]}, "budget_multiplier": 10.0}}
    m, recs, c = _run(cfg, "single_best_compliant", over)
    sg = _sg(recs)
    assert sg and all(r["attack_mode"] == "both" for r in sg)
    assert all(r["actual_model"] == "Qwen/Qwen2.5-0.5B-Instruct" and r["billed_tokens"] > r["actual_tokens"]
               for r in sg)
    both = [r for r in sg if r["audited"]]
    assert both and all(r["audit_type"] == "both" and r["swap_detected"] and r["theft_detected"] for r in both)
    cost_swap = next(s for s in c["sellers"] if s["id"] == SG)["cost_per_1k"]
    for r in both:   # penalty slashed ONCE although both checks fired; revenue on billed, cost on actual
        assert r["seller_profit"] == pytest.approx(r["cost"] - cost_swap * r["actual_tokens"] / 1000 - 0.2)
    assert m["total_stake_slashed"] == pytest.approx(0.2 * len(both))
    assert m["fraud_share"] == pytest.approx(len(sg) / m["n_purchases"])


def test_swap_only_default_keeps_v3_semantics(cfg):
    assert issubclass(SwapStrategy, AttackStrategy)
    s = SwapStrategy(kind="learning", theft_enabled=True)
    assert not s.theft_enabled and len(s._pairs) == 11
    m, recs, _ = _run(cfg, "single_best_compliant")
    for r in recs:
        assert r["billed_tokens"] == r["actual_tokens"] == r["reasoning_tokens"]
        if r["status"] == "allowed":
            assert r["attack_mode"] in ("none", "swap") and r["theft_prob"] == 0.0
            assert r["audit_type"] == "none" and r["theft_detected"] is None
    assert m["thefts_served"] == 0 and m["fraud_share"] == pytest.approx(m["fraud_seller_share"])


def test_learning_attacker_against_length_audit(cfg):
    over = {"fraud": {"strategy": "learning", "attack_modes_enabled": ["swap", "theft"], "penalty": 0.5},
            "market": {"audit": {"rate": 0.3, "types": ["identity"]}, "budget_multiplier": 10.0}}
    m, _, _ = _run(cfg, "single_best_compliant", over, n_tasks=960, n_rounds=96)
    assert m["learned_swap_q"][SG] < 0.15 and m["learned_theft_q"][SG] > 0.8   # identity audit misses theft
    over["market"]["audit"]["types"] = ["identity", "length"]
    m, _, _ = _run(cfg, "single_best_compliant", over, n_tasks=960, n_rounds=96)
    assert m["learned_swap_q"][SG] < 0.15 and m["learned_theft_q"][SG] < 0.15


def test_truncation_reparses_answer():
    res = BackendResult(42, 100, raw="We compute 3 * 7 = 21, then 21 * 2 = 42.\nAnswer: 42", confidence=0.9)

    class B(Backend):
        def solve(self, *a):
            return res
    t = B().truncate(res, None, 20, random.Random(0))
    assert t.reasoning_tokens == 20 and "Answer" not in t.raw and t.confidence <= 0.2
    assert B().truncate(res, None, 200, random.Random(0)) is res
    task = Task("t", "arithmetic", 1, "q", 10, "b", "public", [])
    mres = BackendResult(10, 100, raw="", confidence=0.8)
    outs = [MockLLM().truncate(mres, task, 25, random.Random(i)).answer == 10 for i in range(400)]
    assert 0.15 < sum(outs) / 400 < 0.35            # correct answer survives with prob max_tokens / tokens


# ---------------------------------------------------------------- joint objective + schema
def test_joint_objective_formula(cfg):
    assert joint_objective(0.8, 0.1, 0.2, 1.0, 0.5) == pytest.approx(0.6)
    assert joint_objective(0.8, 0.1, 0.2, 0.0, 0.0) == pytest.approx(0.8)
    over = {"fraud": {"strategy": "static", "attack_modes_enabled": ["swap", "theft"], "q_static": 0.5,
                      "q_theft_static": 0.5}, "market": {"joint": {"lambda": 2.0, "mu": 0.7}}}
    m, recs, _ = _run(cfg, "compliance_unaware_cheapest", over)
    served = [r for r in recs if r["status"] == "allowed"]
    finals = [r for r in recs if r["final"]]
    acc = sum(r["final_correct"] for r in finals) / len(finals)
    viol = sum(r["violation"] for r in served) / len(finals)
    fraud = sum(r["claimed_model"] != r["actual_model"] or r["billed_tokens"] > r["actual_tokens"]
                for r in served) / len(served)
    assert viol > 0
    assert m["joint_objective"] == pytest.approx(acc - 2.0 * viol - 0.7 * fraud)
    assert (m["joint_lambda"], m["joint_mu"]) == (2.0, 0.7)


def test_v4_schema_fields(cfg):
    for k in ("billed_tokens", "actual_tokens", "token_inflation", "attack_mode", "audit_type", "swap_detected",
              "theft_detected", "detect_prob_identity", "detect_prob_length"):
        assert k in FIELDS
    _, recs, _ = _run(cfg, "single_best_compliant", n_tasks=30, n_rounds=3)
    r = next(x for x in recs if x["status"] == "allowed")
    assert validate_record(r) == []
    assert validate_record(dict(r, attack_mode="steal"))
    assert validate_record(dict(r, audit_type="xray"))
    assert validate_record(dict(r, billed_tokens=r["actual_tokens"] - 1))


def test_interp_curve():
    pts = [(0.01, {"j": 0.2}), (0.03, {"j": 0.6}), (0.03, {"j": 0.8})]
    assert interp_curve(pts, 0.005) == (None, False)
    m, sat = interp_curve(pts, 0.02)
    assert m["j"] == pytest.approx(0.45) and not sat          # equal-cost points averaged (0.7)
    m, sat = interp_curve(pts, 0.05)
    assert m["j"] == pytest.approx(0.7) and sat
