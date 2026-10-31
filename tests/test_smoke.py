import copy
import os
import random
import sys

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tokenmarket.backends import MockLLM, parse_final_number  # noqa: E402
from tokenmarket.buyers import load_buyers  # noqa: E402
from tokenmarket.compliance import ComplianceEngine  # noqa: E402
from tokenmarket.gateway import CrossBorderGateway  # noqa: E402
from tokenmarket.logging_schema import FIELDS, read_log, validate_record  # noqa: E402
from tokenmarket.matching import run_auction  # noqa: E402
from tokenmarket.sellers import load_sellers  # noqa: E402
from tokenmarket.sim import run_all  # noqa: E402
from tokenmarket.tasks import Task, generate_stream  # noqa: E402
from tokenmarket.verification import TEEAttestationVerifier, TrustingVerifier, VerificationModule  # noqa: E402

REQUIRED = ["ts", "round", "run_id", "mechanism", "policy", "seed", "buyer_id", "buyer_jurisdiction",
            "task_id", "sensitivity", "seller_id", "seller_jurisdiction", "claimed_model", "actual_model",
            "cross_border", "price_per_1k", "reasoning_tokens", "cost", "fee", "latency_ms", "answer",
            "gold", "correct", "status", "rule_id", "buyer_surplus", "seller_profit"]


@pytest.fixture(scope="module")
def cfg():
    with open(os.path.join(ROOT, "configs", "default.yaml"), encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="module")
def small_run(cfg, tmp_path_factory):
    out = tmp_path_factory.mktemp("results")
    c = copy.deepcopy(cfg)
    c["run"]["n_rounds"] = 3
    summary = run_all(c, seeds=[0, 1], backend_name="mock", n_tasks=40, results_dir=str(out))
    return summary, read_log(os.path.join(str(out), "transactions.jsonl")), str(out)


def _flow(cfg, buyer_id, seller_id, sensitivity, flags=()):
    buyers = {b.id: b for b in load_buyers(cfg)}
    sellers = {s.id: s for s in load_sellers(cfg)}
    task = Task("tx", "arithmetic", 1, "1+1", 2, buyer_id, sensitivity, list(flags))
    return ComplianceEngine.from_config(cfg).evaluate_flow(buyers[buyer_id], sellers[seller_id], task)


def test_default_config_three_sellers_one_fraud(cfg):
    sellers = cfg["sellers"]
    assert len(sellers) == 3
    assert sorted(s["jurisdiction"] for s in sellers) == ["BR", "CN", "SG"]
    for s in sellers:
        for k in ("id", "jurisdiction", "claimed_model", "actual_model", "price_per_1k", "latency",
                  "capacity_per_round", "quality_profile"):
            assert k in s
    fraud = [s for s in sellers if s["claimed_model"] != s["actual_model"]]
    assert len(fraud) == 1 and fraud[0]["jurisdiction"] == "SG"
    m = cfg["models"]
    assert m[fraud[0]["actual_model"]]["accuracy"][3] < m[fraud[0]["claimed_model"]]["accuracy"][3]
    assert m[fraud[0]["actual_model"]]["tokens_mean"] < m[fraud[0]["claimed_model"]]["tokens_mean"]


def test_sim_runs_full_matrix(small_run):
    summary, _, out = small_run
    assert set(summary["combos"]) == {f"{m}/{p}" for m in ("posted_price", "sealed_bid")
                                      for p in ("cheapest", "quality_per_cost", "compliance_aware")}
    assert os.path.exists(os.path.join(out, "summary.json"))
    assert os.path.exists(os.path.join(out, "summary.md"))


def test_one_log_line_per_transaction(small_run):
    summary, recs, _ = small_run
    assert len(recs) == 6 * 2 * 40 == summary["log_lines"]
    keys = [(r["run_id"], r["task_id"]) for r in recs]
    assert len(set(keys)) == len(keys)


def test_schema_valid(small_run):
    _, recs, _ = small_run
    assert set(REQUIRED) <= set(FIELDS)
    for r in recs:
        assert validate_record(r) == [], r
    assert validate_record({"status": "allowed"})  # missing fields detected
    statuses = {r["status"] for r in recs}
    assert "allowed" in statuses and "blocked" in statuses


def test_gateway_lets_no_violation_through(small_run):
    summary, recs, _ = small_run
    for c in summary["combos"].values():
        for m in c["per_seed"]:
            assert m["violating_flows_through"] == 0
        if c["policy"] == "compliance_aware":
            assert c["aggregate"]["blocked_attempts"]["mean"] == 0
    for r in recs:
        if r["status"] == "blocked":
            assert r["rule_id"] and r["cost"] == 0 and r["correct"] is None


def test_cn_important_data_export_blocked(cfg):
    for seller in ("seller_sg", "seller_br"):
        d = _flow(cfg, "buyer_cn_2", seller, "important_data")
        assert not d.allowed and d.rule_id == "CN-DSL-31"
    assert _flow(cfg, "buyer_cn_2", "seller_cn", "important_data").allowed  # domestic
    gw = CrossBorderGateway(ComplianceEngine.from_config(cfg), cfg)
    b = {x.id: x for x in load_buyers(cfg)}["buyer_cn_1"]
    s = {x.id: x for x in load_sellers(cfg)}["seller_sg"]
    res = gw.route(b, s, Task("t", "logic", 1, "q", 1, b.id, "important_data"))
    assert not res.allowed and res.rule_id == "CN-DSL-31" and gw.stats()["blocked_total"] == 1


def test_other_rules(cfg):
    assert _flow(cfg, "buyer_cn_1", "seller_sg", "personal").allowed            # cn_standard_contract
    assert _flow(cfg, "buyer_cn_1", "seller_br", "personal").rule_id == "CN-PIPL-38"
    assert _flow(cfg, "buyer_cn_1", "seller_sg", "sensitive_personal").rule_id == "CN-PIPL-40"
    assert _flow(cfg, "buyer_sg_1", "seller_cn", "personal").rule_id == "SG-PDPA-26"
    assert _flow(cfg, "buyer_sg_1", "seller_br", "personal").allowed            # adequacy list
    assert _flow(cfg, "buyer_br_1", "seller_sg", "sensitive_personal").rule_id == "BR-LGPD-33-VIII"
    assert _flow(cfg, "buyer_br_1", "seller_sg", "sensitive_personal", ["specific_consent"]).allowed
    for b in ("buyer_cn_1", "buyer_sg_1", "buyer_br_1"):
        for s in ("seller_cn", "seller_sg", "seller_br"):
            assert _flow(cfg, b, s, "public").allowed


def test_fraud_seller_logs_claimed_ne_actual(small_run):
    _, recs, _ = small_run
    sg = [r for r in recs if r["seller_id"] == "seller_sg" and r["status"] == "allowed"]
    assert sg
    assert all(r["claimed_model"] == "sim-strong-r1" and r["actual_model"] == "sim-weak-r1" for r in sg)
    honest = [r for r in recs if r["seller_id"] in ("seller_cn", "seller_br")]
    assert all(r["claimed_model"] == r["actual_model"] for r in honest)


def test_second_price_auction():
    bids = [("a", 0.010, 1.0), ("b", 0.014, 1.0), ("c", 0.020, 1.0)]
    assert run_auction(bids, "second_price") == ("a", 0.014)
    assert run_auction(bids, "first_price") == ("a", 0.010)
    assert run_auction(bids, "second_price", reserve=0.012) == ("a", 0.012)   # capped at reserve
    assert run_auction([("a", 0.010, 1.0)], "second_price", reserve=0.03) == ("a", 0.03)
    assert run_auction([("a", 0.05, 1.0)], "second_price", reserve=0.03) is None
    # scoring auction: score = bid / quality; winner paid price that ties runner-up's score
    w, p = run_auction([("hi_q", 0.018, 0.9), ("lo_q", 0.010, 0.4)], "second_price")
    assert w == "hi_q" and p == pytest.approx(0.010 / 0.4 * 0.9)


def test_mock_backend_and_tasks(cfg):
    buyers = load_buyers(cfg)
    tasks = generate_stream(cfg, buyers, 50, seed=0)
    assert tasks == generate_stream(cfg, buyers, 50, seed=0)  # deterministic
    rng = random.Random(0)
    strong, weak = cfg["models"]["sim-strong-r1"], cfg["models"]["sim-weak-r1"]
    acc = lambda prof: sum(MockLLM().solve(t, "m", prof, 1.0, rng).answer == t.gold for t in tasks * 20)
    assert acc(strong) > acc(weak)
    r = MockLLM().solve(tasks[0], "m", weak, 1.0, rng)
    assert r.reasoning_tokens >= 50
    assert parse_final_number("so 3+4=7.\nAnswer: 1,234") == 1234


def test_verification_stubs():
    v = TrustingVerifier()
    assert isinstance(v, VerificationModule)
    tx = {"price_per_1k": 0.01, "reasoning_tokens": 2000, "fee_rate": 0.05}
    assert v.verify_model_identity(tx) == "unverified" and v.verify_token_count(tx) == "unverified"
    st = v.settle(tx)
    assert st.buyer_pays == pytest.approx(0.02) and st.fee == pytest.approx(0.001)
    with pytest.raises(NotImplementedError):
        TEEAttestationVerifier().verify_model_identity(tx)
