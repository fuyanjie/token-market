"""v3 tests (mock override / fake runners only: fast, no model loading)."""
import copy
import json
import os
import random
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tokenmarket.backends import MockLLM, render_task_prompt  # noqa: E402
from tokenmarket.baselines import BudgetBins, solve_routing_lp, zcl_eligible, zcl_psi  # noqa: E402
from tokenmarket.buyers import load_buyers  # noqa: E402
from tokenmarket.cache import OutputCache  # noqa: E402
from tokenmarket.config import load_config  # noqa: E402
from tokenmarket.experiments import interp_at, pareto  # noqa: E402
from tokenmarket.logging_schema import FIELDS, validate_record  # noqa: E402
from tokenmarket.precompute import precompute  # noqa: E402
from tokenmarket.sellers import Reputation  # noqa: E402
from tokenmarket.sim import run_single  # noqa: E402
from tokenmarket.strategic import (SwapStrategy, TrustModel, analytic_threshold, best_response,  # noqa: E402
                                   swap_gain)
from tokenmarket.tasks import build_long_subset, build_task_pool, gsm8k_gold, load_long_tasks  # noqa: E402

QUIET = lambda *a, **k: None  # noqa: E731


@pytest.fixture(scope="module")
def cfg():
    return load_config(os.path.join(ROOT, "configs", "default.yaml"))


class _Log:
    def __init__(self):
        self.records = []

    def write(self, rec):
        assert validate_record(rec) == [], rec
        self.records.append(rec)


def _run(cfg, policy, over=None, seed=0, n_tasks=240, n_rounds=24):
    from tokenmarket.config import deep_merge
    c = deep_merge(cfg, over or {})
    c["run"]["n_rounds"] = n_rounds
    rep = Reputation(c["models"], {})
    lg = _Log()
    pool = build_task_pool(c)
    m = run_single(c, "posted_price", policy, seed, {"mock": MockLLM(c["market"]["mock_confidence"])}, rep, lg,
                   pool, n_tasks, "mock")
    return m, lg.records, c


# ---------------------------------------------------------------- C: strategic seller
def test_analytic_threshold():
    assert analytic_threshold(0.01, 0.9, 0.5) == pytest.approx(0.01 / 0.45)
    assert analytic_threshold(0.01, 0.0, 0.5) == float("inf")
    assert analytic_threshold(0.01, 0.5, 0.0) == float("inf")
    a = analytic_threshold(0.01, 0.9, 0.1, reputation_loss=0.1)
    assert a == pytest.approx(0.01 / 0.18)
    assert swap_gain(0.01, a, 0.9, 0.1, 0.1) == pytest.approx(0.0, abs=1e-12)
    assert best_response(0.01, 0.0, 0.9, 1.0) == 1.0
    assert best_response(0.01, 0.5, 0.9, 1.0) == 0.0
    s = SwapStrategy(kind="analytic", cost_saving=0.01, audit_rate=0.3, detect_prob=0.9, penalty=0.5)
    assert s.start_epoch(random.Random(0)) == 0.0
    s = SwapStrategy(kind="logit", cost_saving=0.01, audit_rate=0.0, detect_prob=0.9, penalty=0.5)
    assert s.start_epoch(random.Random(0)) > 0.99


@pytest.mark.parametrize("audit_rate,penalty,expect_low", [(0.0, 0.5, False), (0.5, 1.0, True)])
def test_learning_seller_converges(cfg, audit_rate, penalty, expect_low):
    over = {"fraud": {"strategy": "learning", "penalty": penalty},
            "market": {"audit": {"rate": audit_rate}, "budget_multiplier": 10.0}}
    m, recs, _ = _run(cfg, "single_best_compliant", over, n_tasks=720, n_rounds=72)
    q = m["learned_swap_q"]["seller_sg"]
    if expect_low:     # a*d*P = 0.45 >> saving ~0.01  ->  q ~ 0 (only epsilon exploration left)
        assert q < 0.1
    else:              # no audits -> swapping is free money -> q ~ 1
        assert q > 0.85
    sg = [r for r in recs if r["seller_id"] == "seller_sg" and r["status"] == "allowed"]
    assert sg and all(r["actual_model"] in ("Qwen/Qwen2.5-0.5B-Instruct", "Qwen/Qwen2.5-1.5B-Instruct") for r in sg)
    assert all(0.0 <= r["swap_prob"] <= 1.0 for r in sg)


def test_static_seller_keeps_v2_behaviour(cfg):
    m, recs, _ = _run(cfg, "single_best_compliant")
    sg = [r for r in recs if r["seller_id"] == "seller_sg" and r["status"] == "allowed"]
    assert sg and all(r["actual_model"] == "Qwen/Qwen2.5-0.5B-Instruct" and r["swap_prob"] == 1.0 for r in sg)
    assert all(not r["audited"] and r["audit_cost"] == 0 and r["swap_detected"] is None for r in recs)
    for k in ("audited", "audit_cost", "swap_detected", "swap_prob"):
        assert k in FIELDS


def test_detection_slashes_and_delists(cfg):
    over = {"fraud": {"strategy": "static", "penalty": 0.3, "detect_prob": 1.0, "reputation_rounds": 2},
            "market": {"audit": {"rate": 1.0}, "budget_multiplier": 10.0}}
    m, recs, _ = _run(cfg, "single_best_compliant", over)
    det = [r for r in recs if r["swap_detected"]]
    assert det and m["total_stake_slashed"] == pytest.approx(0.3 * len(det))
    assert all(r["seller_profit"] < 0 for r in det)
    rounds = {r["round"] for r in det}
    for r in recs:   # delisted for 2 rounds after a catch
        if r["seller_id"] == "seller_sg" and r["status"] == "allowed":
            assert not any(c < r["round"] <= c + 2 for c in rounds)


# ---------------------------------------------------------------- D1 PILOT
def test_zcl_threshold_and_eligibility():
    lb, ub = 5.0, 200.0
    assert zcl_psi(0.0, lb, ub) == pytest.approx(lb / np.e)
    assert zcl_psi(1.0, lb, ub) == pytest.approx(ub)
    assert zcl_psi(0.3, lb, ub) < zcl_psi(0.7, lb, ub)
    # efficiency 0.9/0.03 = 30: eligible at low utilisation, not near full utilisation
    assert zcl_eligible(0.03, 0.9, 0.0, lb, ub)
    assert not zcl_eligible(0.03, 0.9, 0.95, lb, ub)
    assert zcl_eligible(0.004, 0.8, 0.95, lb, ub)   # very efficient arm stays eligible


def test_budget_bins_spillover():
    b = BudgetBins(1.0, 8, 4)
    assert b.bin_budget == pytest.approx(0.25)
    b.spend(0.05)
    for _ in range(2):
        b.next_query()
    b.utilisation()
    assert b.bin_idx == 1 and b.bin_budget == pytest.approx(0.25 + 0.20)   # unspent 0.20 spills over
    assert b.per_query_left() == pytest.approx(0.95 / 6)


@pytest.mark.parametrize("policy", ["pilot", "pilot_compliant", "stageroute", "stageroute_compliant"])
def test_router_budget_never_exceeded(cfg, policy):
    for bm in (0.2, 1.0):
        m, recs, c = _run(cfg, policy, {"market": {"budget_multiplier": bm}})
        buyers = {b.id: b.budget * bm for b in load_buyers(c)}
        spend = {}
        for r in recs:
            spend[r["buyer_id"]] = spend.get(r["buyer_id"], 0.0) + r["actual_cost"] + r["audit_cost"]
        tol = max(r["actual_cost"] for r in recs)   # one purchase of token-length uncertainty at most
        for b, s in spend.items():
            assert s <= buyers[b] + tol
        if policy.endswith("_compliant"):
            assert m["compliance_violations"] == 0
    assert m["n_purchases"] > 0


# ---------------------------------------------------------------- D2 StageRoute LP
def test_stageroute_lp_budget_and_caps():
    rng = np.random.default_rng(0)
    for _ in range(200):
        n = 3
        mu, c = rng.uniform(0, 1, n), rng.uniform(0.001, 0.05, n)
        alpha = rng.uniform(0.35, 1.0, n)
        b = rng.uniform(c.min(), c.max())
        p = solve_routing_lp(mu, c, b, alpha)
        if alpha.sum() < 1:
            continue
        if p is None:   # infeasible only if even the cheapest cap-feasible mix costs more than b
            q = solve_routing_lp(-c, np.zeros(n), 1.0, alpha)
            assert float(c @ q) > b - 1e-9
            continue
        assert p.sum() == pytest.approx(1.0)
        assert float(c @ p) <= b + 1e-9                     # budget respected in expectation
        assert np.all(p <= alpha + 1e-9) and np.all(p >= -1e-12)   # throughput caps
    # closed form check: two arms, budget forces a mix
    p = solve_routing_lp([1.0, 0.0], [0.02, 0.0], 0.01, [1.0, 1.0])
    assert p == pytest.approx([0.5, 0.5])


# ---------------------------------------------------------------- D3 audited cascade
def test_d3_audit_cost_charged_to_budget(cfg):
    over = {"market": {"audited": {"audit_rate": 0.5}, "audit": {"cost": 0.004}}}
    m, recs, c = _run(cfg, "audited_compliance_cascade", over)
    aud = [r for r in recs if r["audited"]]
    assert aud and all(r["audit_cost"] == pytest.approx(0.004) for r in aud)
    assert m["total_audit_cost"] == pytest.approx(0.004 * len(aud))
    assert m["compliance_violations"] == 0
    for r in recs:
        if r["status"] == "allowed":
            before = r["budget_remaining"] + r["actual_cost"] + r["audit_cost"]
            assert r["expected_cost"] <= before + 1e-9
    spend, budgets = {}, {b.id: b.budget for b in load_buyers(c)}
    for r in recs:
        spend[r["buyer_id"]] = spend.get(r["buyer_id"], 0.0) + r["actual_cost"] + r["audit_cost"]
        if r["final"]:   # budget_remaining reflects audit spend
            assert r["budget_remaining"] == pytest.approx(budgets[r["buyer_id"]] - spend[r["buyer_id"]])
    assert m["swaps_detected"] > 0 and m["trust_q_hat"]["seller_sg"] > 0.3


def test_trust_model_downgrades_swapper(cfg):
    rep = Reputation(cfg["models"], {})

    class S:
        id, claimed_model = "s", "Qwen/Qwen2.5-1.5B-Instruct"
    t = TrustModel(rep, 0.9)
    assert t.quality(S, 3) == pytest.approx(0.70)
    for i in range(10):
        t.record("s", i % 2 == 0, "Qwen/Qwen2.5-0.5B-Instruct")
    assert 0.4 < t.q_hat("s") <= 1.0
    assert t.quality(S, 3) < 0.70


# ---------------------------------------------------------------- A helpers
def test_pareto_and_interp():
    pts = [(0.01, 0.5), (0.02, 0.4), (0.03, 0.8), (0.05, 0.7)]
    assert pareto(pts) == [(0.01, 0.5), (0.03, 0.8)]
    assert interp_at(pts, 0.005) is None
    assert interp_at(pts, 0.02) == pytest.approx(0.65)
    assert interp_at(pts, 0.1) == pytest.approx(0.8)


# ---------------------------------------------------------------- B long tasks
def test_long_subset_loader_parses_golds(tmp_path):
    gsm = tmp_path / "gsm.jsonl"
    rows = [{"question": f"q{i}", "answer": "a\n" * (i % 5 + 1) + f"#### {1000 * i + 7:,}"} for i in range(12)]
    gsm.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    mth = tmp_path / "math.jsonl"
    mrows = [{"problem": "p1", "answer": "42", "level": 3, "unique_id": "a"},
             {"problem": "p2", "answer": "\\frac{1}{2}", "level": 5, "unique_id": "b"},
             {"problem": "p3", "answer": "-5", "level": 4, "unique_id": "c"},
             {"problem": "p4", "answer": "17", "level": 2, "unique_id": "d"}]
    mth.write_text("\n".join(json.dumps(r) for r in mrows) + "\n")
    assert gsm8k_gold("blah\n#### 1,234") == 1234
    sub = build_long_subset(str(gsm), str(mth), n_gsm8k=3, n_math=5, seed=1)
    assert sub == build_long_subset(str(gsm), str(mth), n_gsm8k=3, n_math=5, seed=1)   # deterministic
    g = [r for r in sub if r["source"] == "gsm8k"]
    assert len(g) == 3 and all(r["gold"] == 1000 * r["index"] + 7 for r in g)
    m = [r for r in sub if r["source"] == "math500"]
    assert sorted(r["gold"] for r in m) == [-5, 42]       # integer answers with level >= 3 only
    out = tmp_path / "long.jsonl"
    out.write_text("\n".join(json.dumps(r) for r in sub) + "\n")
    tasks = load_long_tasks(str(out))
    assert [t.gold for t in tasks] == [r["gold"] for r in sub]
    assert {t.difficulty for t in tasks} == {4, 5} and all(t.is_long for t in tasks)
    assert "Answer: <integer>" in render_task_prompt(tasks[0])


def test_repo_long_tasks_file():
    tasks = load_long_tasks(os.path.join(ROOT, "data", "long_tasks.jsonl"))
    assert len(tasks) == 48
    assert sum(t.source == "gsm8k" for t in tasks) == 28 and sum(t.source == "math500" for t in tasks) == 20


class _Fake:
    def __init__(self, name):
        self.name, self.mnts = name, []

    def load(self):
        return self

    def unload(self):
        pass

    def generate(self, prompts, max_new_tokens):
        self.mnts.append(max_new_tokens)
        return [("Answer: 1", 5) for _ in prompts], 0.01


def test_mixed_pool_precompute_uses_long_token_limit(cfg, tmp_path):
    c = copy.deepcopy(cfg)
    c["task_pool"] = dict(c["task_pool"], kind="mixed", size=6, long_path=os.path.join(ROOT, "data", "long_tasks.jsonl"))
    pool = build_task_pool(c)
    assert len(pool) == 6 + 48
    made = []
    rep = precompute(c, OutputCache(str(tmp_path / "c.jsonl")), pool,
                     runner_factory=lambda n: made.append(_Fake(n)) or made[-1], log=QUIET)
    assert all(r["n_new"] == 54 for r in rep.values())
    lm = c["backends"]["local_hf"]["long_max_new_tokens"]
    for model in rep:   # fp32 synthetic batches and bf16 long batches -> one (re)load per dtype
        assert {m for f in made if f.name == model for m in f.mnts} == {256, lm}
        assert len([f for f in made if f.name == model]) == 2
    cache = OutputCache(str(tmp_path / "c.jsonl"))
    long_t = next(t for t in pool if t.is_long)
    assert cache.get("Qwen/Qwen2.5-1.5B-Instruct", render_task_prompt(long_t), lm)["source"] == long_t.source
