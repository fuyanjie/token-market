"""v1.0 infrastructure tests: scale roster, selective downgrade, alternative seller learners, protocol §1 E/Q,
audit rules, A2 compliance switch, LP/MIP solvers, faithful PILOT / StageRoute, method registry, price table,
runner, and a v0.1 golden-number guard."""
import collections
import csv
import itertools
import math
import os
import random
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from tokenmarket.audit_v1 import RandomAuditRate, RiskAdaptiveAudit, audit_rule, present_rounds  # noqa: E402
from tokenmarket.baselines import (PilotV1Router, StageRouteV1Router, f_rad, pilot_preference_prior,  # noqa: E402
                                   solve_routing_lp, _cos, _unit, context)
from tokenmarket.config import deep_merge, load_config  # noqa: E402
from tokenmarket.logging_schema import validate_record  # noqa: E402
from tokenmarket.lp import box_lp_max, deploy_mip, linprog, milp_binary  # noqa: E402
from tokenmarket.portfolio import AUDITED_POLICIES  # noqa: E402
from tokenmarket.prices import load_prices, verified_rows  # noqa: E402
from tokenmarket.registry import ALIASES, DEFAULT_MAIN_TABLE, METHODS, resolve  # noqa: E402
from tokenmarket.roster import generate_roster, materialize, roster_seed, strategic_ids  # noqa: E402
from tokenmarket.sellers import Reputation, load_sellers  # noqa: E402
from tokenmarket.strategic import AttackStrategy, attack_mode, make_strategy  # noqa: E402
from tokenmarket.tasks import build_task_pool  # noqa: E402
from tokenmarket.v1_metrics import exposure, intent  # noqa: E402

from test_v3 import _run  # noqa: E402

SCALE = os.path.join(ROOT, "configs", "v1.0", "scale.yaml")


@pytest.fixture(scope="module")
def default_cfg():
    return load_config(os.path.join(ROOT, "configs", "default.yaml"))


@pytest.fixture(scope="module")
def scale_cfg():
    return load_config(SCALE)


# ---------------------------------------------------------------- 1. scale config / roster
def test_scale_config_protocol_section2(scale_cfg):
    c = materialize(scale_cfg)
    sellers = c["sellers"]
    strat = strategic_ids(c)
    assert len(sellers) >= 40 and len(sellers) - len(strat) >= 30 and len(strat) >= 3
    modes = {m for s in sellers for m in s.get("strategy", {}).get("attack_modes", [])}
    assert modes == {"swap", "theft", "downgrade"}
    assert c["run"]["n_rounds"] == 48 and len(c["run"]["seeds"]) >= 20
    grid = c["v1"]["pi_grid"]
    expected = [round(0.02 * i, 2) for i in range(16)] + [0.11, 0.5, 1.0]
    assert sorted(grid) == sorted(expected)
    assert len({s["id"] for s in sellers}) == len(sellers)


def test_roster_deterministic_and_resample(scale_cfg):
    a, b = materialize(scale_cfg, 0), materialize(scale_cfg, 7)
    assert a["sellers"] == b["sellers"]                     # fixed roster by default
    spec = dict(scale_cfg["roster"], resample_per_seed=True)
    r0 = generate_roster(spec, roster_seed(spec, 0))
    r1 = generate_roster(spec, roster_seed(spec, 1))
    assert r0 == generate_roster(spec, roster_seed(spec, 0)) and r0 != r1
    # ids are shuffled: strategic sellers are not a contiguous id block
    idx = sorted(int(s["id"][1:]) for s in a["sellers"] if s.get("strategy"))
    assert idx != list(range(idx[0], idx[0] + len(idx)))


def test_materialize_noop_without_roster(default_cfg):
    assert materialize(default_cfg, 3) is default_cfg


def test_roster_sellers_build_strategies(scale_cfg):
    c = materialize(scale_cfg)
    for scfg in c["sellers"]:
        st = make_strategy(scfg, c, 0.1, None, ["identity", "length"])
        if scfg.get("strategy"):
            assert st is not None and st.enabled_modes() == scfg["strategy"]["attack_modes"]
        else:
            assert st is None


# ---------------------------------------------------------------- 2. selective downgrade
def _downgrade_cfg(cfg, q=1.0, min_d=3, extra=None):
    over = {"fraud": {"strategy": "static", "attack_modes_enabled": ["downgrade"], "q_downgrade_static": q,
                      "downgrade_min_difficulty": min_d},
            "market": {"policies": ["single_best_compliant"]}}
    return deep_merge(cfg, deep_merge(over, extra or {}))


def test_downgrade_only_on_hard_tasks(default_cfg):
    m, recs, _ = _run(_downgrade_cfg(default_cfg), "single_best_compliant")
    sg = [r for r in recs if r["seller_id"] == "seller_sg" and r["status"] == "allowed"]
    assert sg
    for r in sg:
        assert validate_record(r) == []
        if r["difficulty"] >= 3:
            assert r["attack_mode"] == "downgrade" and r["actual_model"] != r["claimed_model"]
        else:
            assert r["attack_mode"] == "none" and r["actual_model"] == r["claimed_model"]
        assert r["downgrade_prob"] == 1.0 and r["swap_prob"] == 0.0
    served = [r for r in recs if r["status"] == "allowed"]
    n_dg = sum(r["attack_mode"] == "downgrade" for r in served)
    assert n_dg > 0 and m["fraud_share"] == pytest.approx(n_dg / len(served))   # included in fraud_share
    assert m["attack_mode_counts"]["downgrade"] == n_dg
    assert m["strategic_modes"] == {"seller_sg": ["downgrade"]}


def test_downgrade_threshold_configurable(default_cfg):
    _, recs, _ = _run(_downgrade_cfg(default_cfg, min_d=2), "single_best_compliant")
    sg = [r for r in recs if r["seller_id"] == "seller_sg" and r["status"] == "allowed"]
    assert {r["attack_mode"] for r in sg if r["difficulty"] == 2} == {"downgrade"}


def test_downgrade_detected_by_identity_audit(default_cfg):
    extra = {"market": {"audited": {"audit_rate": 1.0}}, "fraud": {"detect_prob": 1.0}}
    _, recs, _ = _run(_downgrade_cfg(default_cfg, extra=extra), "audited_compliance_cascade")
    dg = [r for r in recs if r["attack_mode"] == "downgrade" and r["audited"]]
    assert dg and all(r["swap_detected"] for r in dg)


def test_downgrade_with_theft_mode_and_metrics(default_cfg):
    cfg = _downgrade_cfg(default_cfg, extra={"fraud": {"attack_modes_enabled": ["downgrade", "theft"],
                                                       "q_theft_static": 1.0}})
    m, recs, _ = _run(cfg, "single_best_compliant")
    modes = collections.Counter(r["attack_mode"] for r in recs if r["seller_id"] == "seller_sg"
                                and r["status"] == "allowed")
    assert modes["downgrade+theft"] > 0 and modes["theft"] > 0 and modes["swap"] == 0
    assert m["thefts_served"] == modes["downgrade+theft"] + modes["theft"]


def test_attack_mode_encoding():
    assert attack_mode(False, False) == "none" and attack_mode(True, True) == "both"
    assert attack_mode(False, False, True) == "downgrade"
    assert attack_mode(False, True, True) == "downgrade+theft"
    assert attack_mode(True, False, True) == "swap"            # swap wins: modes are disjoint


def test_multilinear_reward_weights_sum_to_one():
    st = AttackStrategy(kind="learning", swap_enabled=True, theft_enabled=True, downgrade_enabled=True)
    st._n_all, st._n_hard = 10, 4
    ones = {c: 1.0 for c in st._cells()}
    for qs, qt, qd in itertools.product([0, 0.3, 1], repeat=3):
        assert st._reward(qs, qt, ones, qd) == pytest.approx(1.0)


def test_reward_reduces_to_bilinear_without_downgrade():
    st = AttackStrategy(kind="learning", swap_enabled=True, theft_enabled=True)
    assert all(p[2] == 0.0 for p in st._pairs) and len(st._pairs) == 121
    means = {(False, False, False): 1.0, (True, False, False): 2.0, (False, True, False): 3.0,
             (True, True, False): 5.0}
    qs, qt = 0.3, 0.6
    expect = (1 - qs) * (1 - qt) * 1 + qs * (1 - qt) * 2 + (1 - qs) * qt * 3 + qs * qt * 5
    assert st._reward(qs, qt, means) == expect


# ---------------------------------------------------------------- 3. alternative learners
def test_unknown_learner_rejected():
    with pytest.raises(ValueError):
        AttackStrategy(kind="learning", learner="nope")


def test_exp3_updates_only_played_arm_and_mixes():
    st = AttackStrategy(kind="learning", learner="exp3", exp3_gamma=0.2, scale=0.01, penalty=0.1)
    rng = random.Random(0)
    st.start_epoch(rng)
    arm = st._arm
    assert st._arm_p >= 0.2 / len(st._pairs)
    st.observe(True, 0.01)
    before = list(st._logw)
    st.start_epoch(rng)
    changed = [i for i, (a, b) in enumerate(zip(before, st._logw)) if a != b]
    assert changed == [arm]
    # epoch without purchases: no update
    before = list(st._logw)
    st.start_epoch(rng)
    assert st._logw == before


def _feed(st, sw_profit, honest_profit, n=30):
    for _ in range(n):
        st.observe(True, sw_profit)
        st.observe(False, honest_profit)


def test_fictitious_play_responds_to_empirical_payoffs():
    st = AttackStrategy(kind="learning", learner="fictitious_play", scale=0.02, fp_temperature=0.1)
    rng = random.Random(0)
    st.start_epoch(rng)
    assert st.q == 0.5                                       # no data: keep mixed strategy
    _feed(st, -0.05, 0.01)                                   # swapping caught often -> unprofitable
    st.start_epoch(rng)
    assert st.q < 0.01
    st2 = AttackStrategy(kind="learning", learner="fictitious_play", scale=0.02, fp_temperature=0.1)
    _feed(st2, 0.03, 0.01)
    st2.start_epoch(rng)
    assert st2.q > 0.99


def test_learner_selectable_by_config(default_cfg):
    for learner in ("exp3", "fictitious_play"):
        cfg = deep_merge(default_cfg, {"fraud": {"strategy": "learning", "learning": {"learner": learner}}})
        st = make_strategy(cfg["sellers"][1], cfg, 0.1)
        assert st.learner == learner
        m, _, _ = _run(cfg, "single_best_compliant", n_tasks=120, n_rounds=12)
        assert len(m["swap_q_history"]["seller_sg"]) == 12


# ---------------------------------------------------------------- 4. protocol §1 E and Q
def test_intent_excludes_delisted_rounds_and_simple_mean():
    n = 8                                   # tail = last 2 rounds (6, 7)
    m = {"strategic_modes": {"a": ["swap"], "b": ["theft", "downgrade"]},
         "swap_q_history": {"a": [0.0] * 6 + [0.2, 0.4], "b": [0.0] * 8},
         "theft_q_history": {"a": [0.0] * 8, "b": [0.0] * 6 + [1.0, 0.6]},
         "downgrade_q_history": {"a": [0.0] * 8, "b": [0.0] * 6 + [0.2, 0.2]},
         "strategic_delisted_rounds": {"a": [7], "b": []}}
    recs = [{"status": "allowed", "seller_id": "b", "round": 6, "billed_tokens": 100},
            {"status": "allowed", "seller_id": "a", "round": 6, "billed_tokens": 300}]
    q = intent(m, recs, n)
    assert q["Q_swap"] == pytest.approx(0.2)                 # round 7 delisted -> excluded
    assert q["Q_theft"] == pytest.approx(0.8) and q["Q_downgrade"] == pytest.approx(0.2)
    assert q["Q"] == pytest.approx((0.2 + 0.8 + 0.2) / 3)    # unweighted mean of the mode values
    assert q["delisted_rounds_tail"] == 1 and q["q_delisted_mean"] == pytest.approx(0.4)
    assert "Q_tokw" not in q
    assert q["tail_trade"] and q["tail_trade_sellers"] == 2 and q["tail_sales"] == 2


def test_intent_q_is_not_token_weighted():
    """口径补正 1: billed tokens must not move Q; a sale counts for tail_trade regardless of its token count."""
    m = {"strategic_modes": {"a": ["swap", "theft"]},
         "swap_q_history": {"a": [0.0] * 6 + [0.1, 0.9]}, "theft_q_history": {"a": [0.0] * 6 + [0.3, 0.3]},
         "strategic_delisted_rounds": {}}
    q1 = intent(m, [{"status": "allowed", "seller_id": "a", "round": 7, "billed_tokens": 10_000}], 8)
    q2 = intent(m, [{"status": "allowed", "seller_id": "a", "round": 6, "billed_tokens": 0}], 8)
    assert q1["Q"] == q2["Q"] == pytest.approx((0.5 + 0.3) / 2)
    assert q1["Q_swap"] == pytest.approx(0.5) and q1["tail_trade"] and q2["tail_trade"]


def test_tail_trade_window_and_rate():
    """tail_trade = >=1 served purchase from a strategic seller in the last quarter (last 12 of 48 rounds)."""
    import run_v1
    m = {"strategic_modes": {"a": ["swap"]}, "swap_q_history": {"a": [0.5] * 48}, "strategic_delisted_rounds": {}}
    early = [{"status": "allowed", "seller_id": "a", "round": 35},          # just before the window
             {"status": "blocked", "seller_id": "a", "round": 40},          # not a sale
             {"status": "allowed", "seller_id": "honest", "round": 40}]     # not a strategic seller
    assert intent(m, early, 48)["tail_trade"] is False
    assert intent(m, early + [{"status": "allowed", "seller_id": "a", "round": 36}], 48)["tail_trade"] is True
    rows = [{"method": "x", "pi": 1.0, "tail_trade": t} for t in (True, False, False, True)]
    rows += [{"method": "x", "pi": 0.1, "tail_trade": False}]
    rates = {(r["method"], r["pi"]): r["tail_trade_rate"] for r in run_v1.tail_trade_rates(rows)}
    assert rates == {("x", 0.1): 0.0, ("x", 1.0): 0.5}


def test_intent_no_tail_trade():
    m = {"strategic_modes": {"a": ["swap"]}, "swap_q_history": {"a": [0.5] * 8}, "strategic_delisted_rounds": {}}
    q = intent(m, [], 8)
    assert q["Q"] == 0.5 and q["tail_trade"] is False and q["tail_sales"] == 0


def test_run_metrics_E_tok_matches_exposure(default_cfg):
    cfg = deep_merge(default_cfg, {"fraud": {"strategy": "learning"}})
    m, recs, _ = _run(cfg, "single_best_compliant", n_tasks=120, n_rounds=12)
    e = exposure(recs)
    assert m["fraud_share"] == e["fraud_share"] > 0
    assert m["E_tok"] == pytest.approx(e["E_tok"]) and 0 < m["E_tok"] <= 1


def test_present_rounds_window():
    tail, pres, dl = present_rounds(48, [40, 47, 3])
    assert tail == list(range(36, 48)) and dl == [40, 47] and len(pres) == 10


def test_exposure_token_vs_purchase_share():
    recs = [{"status": "allowed", "attack_mode": "none", "billed_tokens": 100},
            {"status": "allowed", "attack_mode": "downgrade", "billed_tokens": 300},
            {"status": "blocked", "attack_mode": None, "billed_tokens": 0}]
    e = exposure(recs)
    assert e["fraud_share"] == 0.5 and e["E"] == 0.5 and e["E_tok"] == 0.75     # 口径补正 7: E per purchase
    assert e["fraud_share_downgrade"] == 0.5 and e["fraud_share_swap"] == 0.0


# ---------------------------------------------------------------- 5. audit rules + A2 switch
def test_audit_rule_selection(default_cfg):
    assert audit_rule(default_cfg, "audited_compliance_cascade", AUDITED_POLICIES) == "fixed"
    c = deep_merge(default_cfg, {"market": {"audited": {"audit_rule": "risk_adaptive"}}})
    assert audit_rule(c, "audited_compliance_cascade", AUDITED_POLICIES) == "risk_adaptive"
    assert audit_rule(c, "pilot_compliant", AUDITED_POLICIES) == "fixed"
    with pytest.raises(ValueError):
        audit_rule(deep_merge(default_cfg, {"market": {"audited": {"audit_rule": "x"}}}),
                   "audited_compliance_cascade", AUDITED_POLICIES)


def test_risk_adaptive_rate_increases_with_posterior():
    ra = RiskAdaptiveAudit(["identity", "length"], 0.9, 0.9)
    r0 = ra.rate("s")
    assert r0 == pytest.approx(0.05 + 0.45 * 0.1)
    for _ in range(5):
        ra.record("s", caught=True)
    assert ra.rate("s") > r0
    for _ in range(50):
        ra.record("h", caught=False)
    assert ra.rate("h") < r0 and ra.rate("h") >= 0.05


def test_random_audit_rate_bounds_and_mean():
    r = RandomAuditRate(0.1, random.Random(1))
    xs = [r.start_round() for _ in range(4000)]
    assert min(xs) >= 0 and max(xs) <= 0.2 and abs(sum(xs) / len(xs) - 0.1) < 0.005


@pytest.mark.parametrize("rule", ["random", "risk_adaptive"])
def test_audit_rules_run_in_sim(default_cfg, rule):
    cfg = deep_merge(default_cfg, {"fraud": {"strategy": "learning"},
                                   "market": {"audited": {"audit_rule": rule, "audit_rate": 0.1}}})
    m, recs, _ = _run(cfg, "audited_compliance_cascade", n_tasks=120, n_rounds=12)
    assert m["audit_rule"] == rule and m["n_audits"] > 0
    if rule == "random":
        assert len(m["random_audit_rate_history"]) == 12


def test_compliance_filter_switch_a2(default_cfg):
    on, _, _ = _run(default_cfg, "single_cheapest_compliant", n_tasks=120, n_rounds=12)
    off, _, _ = _run(deep_merge(default_cfg, {"market": {"compliance_filter": False}}), "single_cheapest_compliant",
                     n_tasks=120, n_rounds=12)
    assert on["compliance_violations"] == 0 and on["compliance_filter"] is True
    assert off["compliance_violations"] > 0 and off["filtered_candidates"] == 0 and off["compliance_filter"] is False


# ---------------------------------------------------------------- 6. LP / MIP
def test_box_lp_matches_vertex_enumeration():
    rng = np.random.default_rng(1)
    for _ in range(100):
        n = int(rng.integers(2, 6))
        mu, c, a = rng.random(n), rng.random(n), rng.uniform(0.3, 1, n)
        b = float(rng.uniform(0, 1))
        p1, p2 = solve_routing_lp(mu, c, b, a), box_lp_max(mu, c, b, a)
        assert (p1 is None) == (p2 is None)
        if p1 is not None:
            assert mu @ p1 == pytest.approx(mu @ p2, abs=1e-8)
            assert c @ p2 <= b + 1e-8 and np.all(p2 <= a + 1e-8) and p2.sum() == pytest.approx(1)


def test_deploy_mip_matches_brute_force():
    rng = np.random.default_rng(2)
    for _ in range(40):
        n, k = int(rng.integers(3, 7)), None
        k = int(rng.integers(1, n + 1))
        mu, c, a, b = rng.random(n), rng.random(n), rng.uniform(0.2, 0.7, n), float(rng.uniform(0.1, 0.8))
        best = None
        for S in itertools.combinations(range(n), k):
            S = list(S)
            p = solve_routing_lp(mu[S], c[S], b, a[S]) if a[S].sum() >= 1 else None
            if p is not None and (best is None or mu[S] @ p > best):
                best = mu[S] @ p
        res = deploy_mip(mu, c, b, a, k)
        assert (res is None) == (best is None)
        if res is not None:
            d, z = res
            assert mu @ d == pytest.approx(best, abs=1e-8) and z.sum() == k and np.all(d <= a * z + 1e-9)


def test_linprog_infeasible_and_milp():
    assert linprog([1, 1], A_eq=[[1, 1]], b_eq=[1], ub=[0.2, 0.2]).status == "infeasible"
    r = milp_binary([-1, -1, -1], A_ub=[[1, 1, 1]], b_ub=[2], ub=[1, 1, 1], binary=[0, 1, 2])
    assert r.fun == pytest.approx(-2) and set(np.round(r.x)) <= {0, 1}


# ---------------------------------------------------------------- 7. faithful PILOT / StageRoute
class _B:
    def __init__(self, i, budget):
        self.id, self.budget = i, budget


def test_stageroute_v1_stages_mip_and_bounds(default_cfg):
    sellers = load_sellers(default_cfg)
    buyers = [_B("b", 1.0)]
    r = StageRouteV1Router(sellers, buyers, {"b": 125}, default_cfg, 125, 10, random.Random(0))
    assert r.K == 5 and r.m_max == math.ceil(3 ** (2 / 3))
    s = sellers[0]
    r.n[s.id], r.mu[s.id], r.n_c[s.id], r.c[s.id] = 3, 0.5, 3, 0.02
    mu_u, c_l = r.bounds(s)
    assert mu_u == pytest.approx(min(1, 0.5 + 2 * f_rad(0.5, 4, r.gamma)))
    assert c_l == pytest.approx(min(r.c2, max(r.c1, 0.02 - 2 * f_rad(0.02, 4, r.gamma))))
    pool = build_task_pool(default_cfg)
    for t in range(125):
        ch = r.choose(pool[t % len(pool)], buyers[0], sellers, lambda s: 0.01)
        assert ch.id in r.deployed or r.n_fallback_cands > 0
        r.update(None, buyers[0], ch, bool(t % 2), 0.01)
        r.end_query(buyers[0])
    assert len(r.deploy_log) == 5 and all(len(d["deployed"]) == min(r.m_max, 3) for d in r.deploy_log)


def test_pilot_preference_prior_orders_claimed_models(default_cfg):
    rep = Reputation(default_cfg["models"], {})
    pool = build_task_pool(default_cfg)
    pri = pilot_preference_prior(["Qwen/Qwen2.5-1.5B-Instruct", "Qwen/Qwen2.5-0.5B-Instruct", "sim-fast-mock"],
                                 rep, pool)
    wins = sum(_cos(pri["Qwen/Qwen2.5-1.5B-Instruct"], _unit(context(t)))
               > _cos(pri["Qwen/Qwen2.5-0.5B-Instruct"], _unit(context(t))) for t in pool)
    assert wins / len(pool) > 0.9


def test_pilot_v1_lambda_bins_and_insufficient_budget(default_cfg):
    rep = Reputation(default_cfg["models"], {})
    pool = build_task_pool(default_cfg)
    sellers = load_sellers(default_cfg)
    r = PilotV1Router(sellers, rep, [_B("b", 0.0)], {"b": 8}, default_cfg, pool)
    s = sellers[0]
    acc = np.mean([rep.accuracy(s.claimed_model, d) for d in (1, 2, 3)])
    assert r.lam[s.id] == pytest.approx(1 / acc)
    assert r.state["b"]["N"] == 4 and r.state["b"]["S"] == 2
    # zero budget: ZCL threshold may admit arms at z = 0, but fallback cap is 0 -> force insufficiency
    r.lb, r.ub = 1e6, 2e6
    assert r.choose(pool[0], _B("b", 0.0), sellers, lambda s: 0.01) is None and r.n_insufficient == 1
    r.end_query(_B("b", 0.0))


@pytest.mark.parametrize("policy", ["pilot_v1_compliant", "stageroute_v1_compliant", "pilot_v1", "stageroute_v1"])
def test_v1_routers_run_in_sim(default_cfg, policy):
    cfg = deep_merge(default_cfg, {"fraud": {"strategy": "learning", "attack_modes_enabled": ["swap", "theft"]}})
    m, recs, _ = _run(cfg, policy, n_tasks=120, n_rounds=12)
    assert m["n_purchases"] > 0 and all(validate_record(r) == [] for r in recs)
    if policy.endswith("_compliant"):
        assert m["compliance_violations"] == 0


# ---------------------------------------------------------------- 8. registry / prices / runner
def test_registry_names_aliases_labels():
    for name in ["pilot", "stageroute", "cheapest_fixed", "strongest_fixed", "random_audit", "fixed_audit_a0.05",
                 "fixed_audit_a0.10", "fixed_audit_a0.20", "risk_adaptive_audit"]:
        assert name in METHODS and name in DEFAULT_MAIN_TABLE
    assert resolve("d3").name == "fixed_audit_a0.10" == resolve("audited_compliance_cascade").name
    for a in (0.05, 0.10, 0.20):
        m = METHODS[f"fixed_audit_a{a:.2f}"]
        assert "fixed-rate audit reference baseline" in m.label
        assert m.over["market"]["audited"]["audit_rate"] == a
    assert resolve("stageroute").policy == "stageroute_v1_compliant"
    assert all("our" not in m.label.lower() for m in METHODS.values())
    with pytest.raises(KeyError):
        resolve("nope")
    assert set(ALIASES.values()) <= set(METHODS)
    u = resolve("audited_cascade_unfiltered")                       # A2: D3 without the hard compliance filter
    assert u.policy == "audited_cascade_unfiltered" and resolve("d3_unfiltered") is u
    assert u.over == METHODS["fixed_audit_a0.10"].over and u.name not in DEFAULT_MAIN_TABLE


def test_price_table_real_sources():
    t = load_prices(os.path.join(ROOT, "configs", "v1.0", "prices.yaml"))
    rows = verified_rows(t)
    assert len({r["provider"] for r in rows}) >= 3
    for prov, p in t["providers"].items():
        assert p["source_url"].startswith("https://") and p["accessed"]
        for model, r in (p.get("models") or {}).items():
            if r.get("output") is None:
                assert r.get("todo"), (prov, model)
            else:
                assert 0 < r["input"] <= r["output"]


def test_run_v1_smoke_and_out_guard(tmp_path):
    import run_v1
    out = tmp_path / "v1"
    run_v1.main(["--config", SCALE, "--seeds", "0", "--pi-grid", "1.0", "0.1", "--methods", "pilot", "stageroute",
                 "d3", "risk_adaptive_audit", "--backend-override", "mock", "--n-tasks", "48", "--n-rounds", "8",
                 "--out", str(out), "--log-dir", str(tmp_path / "logs")])
    rows = list(csv.DictReader(open(out / "per_seed.csv")))
    assert len(rows) == 8
    for c in ("E", "E_tok", "fraud_share", "Q", "Q_swap", "Q_theft", "Q_downgrade", "J", "cost", "quality",
              "tail_trade"):
        assert c in rows[0]
    assert "Q_tokw" not in rows[0] and all(r["E"] == r["fraud_share"] for r in rows)
    tt = list(csv.DictReader(open(out / "tail_trade_rate.csv")))
    assert len(tt) == 8 and {r["tail_trade_rate"] for r in tt} <= {"0.0", "1.0"}   # 4 methods x 2 pi, 1 seed
    assert {r["method"] for r in rows} == {"pilot", "stageroute", "fixed_audit_a0.10", "risk_adaptive_audit"}
    assert len(os.listdir(tmp_path / "logs")) == 8
    with pytest.raises(SystemExit):
        run_v1.main(["--config", SCALE, "--seeds", "0", "--out", os.path.join(ROOT, "results", "pi_dense", "x")])


def test_run_v1_audited_cascade_unfiltered(tmp_path):
    import run_v1
    out = tmp_path / "a2"
    run_v1.main(["--config", SCALE, "--seeds", "0", "--pi-grid", "1.0", "--methods", "audited_cascade_unfiltered",
                 "fixed_audit_a0.10", "--backend-override", "mock", "--n-tasks", "96", "--n-rounds", "8",
                 "--out", str(out)])
    rows = {r["method"]: r for r in csv.DictReader(open(out / "per_seed.csv"))}
    off, on = rows["audited_cascade_unfiltered"], rows["fixed_audit_a0.10"]
    assert off["policy"] == "audited_cascade_unfiltered" and on["policy"] == "audited_compliance_cascade"
    assert float(on["violation_rate"]) == 0.0
    assert float(off["violation_rate"]) >= float(on["violation_rate"])


# ---------------------------------------------------------------- 9. v0.1 golden numbers (cache-backed)
CACHE = os.path.join(ROOT, "cache", "llm_outputs.jsonl")
GOLDEN = [  # (override, policy, seed, J, fraud_share, total_cost) from the pre-v1.0 code, n_tasks=120, n_rounds=12
    ({}, "audited_compliance_cascade", 0, 0.7850340136054422, 0.16326530612244897, 3.5074984),
    ({}, "stageroute_compliant", 1, 0.8375, 0.008333333333333333, 2.5447754000000002),
    ({"market": {"feedback": {"mode": "sparse", "delay_L": 0, "reveal_prob": 0.1}}}, "pilot_compliant", 0,
     0.5666666666666667, 0.23333333333333334, 2.7998388),
    ({"fraud": {"learning": {"learner": "hedge"}}, "market": {"audited": {"reputation_rounds": 5}}},
     "audited_compliance_cascade", 1, 0.7995318352059925, 0.08426966292134831, 3.0927618),
    ({"market": {"audited": {"adaptive_audit": True, "escrow": True}}}, "audited_compliance_cascade", 0,
     0.802247191011236, 0.09550561797752809, 3.0410788),
]


@pytest.mark.skipif(not os.path.exists(CACHE), reason="LLM cache not present")
@pytest.mark.parametrize("over,policy,seed,J,fs,cost", GOLDEN)
def test_v01_numbers_unchanged(over, policy, seed, J, fs, cost):
    from tokenmarket.sim import build_backends, prepare, run_single
    from test_v3 import _Log
    cfg = deep_merge(load_config(os.path.join(ROOT, "configs", "benchmark", "production.yaml")), over)
    cfg["run"]["n_tasks"], cfg["run"]["n_rounds"] = 120, 12
    pool, cache, stats, _ = prepare(cfg, None, CACHE, None, lambda *a: None)
    be = build_backends(cfg, {s.get("backend", "mock") for s in cfg["sellers"]}, cache)
    m = run_single(cfg, "posted_price", policy, seed, be, Reputation(cfg["models"], stats), _Log(), pool, None, None)
    assert m["joint_objective"] == J and m["fraud_share"] == fs and m["total_cost"] == cost
