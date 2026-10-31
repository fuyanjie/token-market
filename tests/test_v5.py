"""v5 tests: delayed / sparse outcome feedback (FeedbackBuffer, FeedbackRouter, sim plumbing) - mock only, fast."""
import math
import os
import random
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tokenmarket import feedback as fbmod  # noqa: E402
from tokenmarket.config import load_config  # noqa: E402
from tokenmarket.experiments import feedback_over  # noqa: E402
from tokenmarket.feedback import FeedbackBuffer, FeedbackRouter, feedback_params  # noqa: E402
from tokenmarket.logging_schema import validate_record  # noqa: E402

from test_v3 import _run  # noqa: E402

SG = "seller_sg"
N = 200


@pytest.fixture(scope="module")
def cfg():
    return load_config(os.path.join(ROOT, "configs", "default.yaml"))


def _fb(L, pi=1.0):
    return {"market": {"feedback": feedback_over(L, pi), "budget_multiplier": 4.0}}


def _served(recs):
    return [r for r in recs if r["status"] == "allowed"]


# ---------------------------------------------------------------- config / buffer unit tests
def test_feedback_params_modes():
    assert feedback_params({}) == ("immediate", 0.0, 1.0)
    assert feedback_params({"market": {"feedback": {"mode": "immediate", "delay_L": 9, "reveal_prob": 0.1}}}) \
        == ("immediate", 0.0, 1.0)
    assert feedback_params({"market": {"feedback": {"mode": "delayed", "delay_L": 5}}}) == ("delayed", 5.0, 1.0)
    assert feedback_params({"market": {"feedback": {"mode": "delayed", "delay_L": "inf"}}})[1] == math.inf
    assert feedback_params({"market": {"feedback": {"mode": "never"}}})[1] == math.inf
    assert feedback_params({"market": {"feedback": {"mode": "sparse", "delay_L": 7, "reveal_prob": 0.2}}}) \
        == ("sparse", 0.0, 0.2)
    assert feedback_params({"market": {"feedback": {"mode": "delayed_sparse", "delay_L": 20,
                                                    "reveal_prob": 0.2}}}) == ("delayed_sparse", 20.0, 0.2)
    with pytest.raises(ValueError):
        feedback_params({"market": {"feedback": {"mode": "bogus"}}})
    assert feedback_over(0, 1.0)["mode"] == "immediate" and feedback_over("inf", 1.0)["mode"] == "never"


def test_buffer_fifo_by_due_and_flush():
    b = FeedbackBuffer(3, 1.0)
    for t in range(6):
        assert b.push(t, f"task{t}", "B", f"s{t}", t % 2 == 0, 0.1 * t, horizon=7) == (True, min(t + 3, 7))
    assert b.pop_ready(2) == []
    got = b.pop_ready(4)
    assert [(lb.step, lb.task, lb.seller, lb.correct) for lb in got] == [(0, "task0", "s0", True),
                                                                         (1, "task1", "s1", False)]
    rest = b.flush_at_end()
    assert [lb.step for lb in rest] == [2, 3, 4, 5] and b.pending() == 0 and b.n_flushed == 4
    nb = FeedbackBuffer(math.inf, 1.0)
    assert nb.push(0, "t", "B", "s", True, 0.0, horizon=5) == (True, None)
    assert nb.pop_ready(10 ** 9) == [] and nb.flush_at_end() == []
    zb = FeedbackBuffer(0, 0.0)
    assert zb.push(0, "t", "B", "s", True, 0.0, horizon=5) == (False, None) and zb.pop_ready(0) == []


def test_feedback_router_lags_by_L():
    class Stub:
        def __init__(self):
            self.learned, self.costs = [], []

        def observe_cost(self, buyer, seller, c, served=True):
            self.costs.append(c)

        def learn(self, task, seller, correct, cost=0.0):
            self.learned.append((task, seller, correct))

    inner, L = Stub(), 5
    buf = FeedbackBuffer(L, 1.0)
    r = FeedbackRouter(inner, buf)
    counts = []
    for t in range(12):
        r.step = t
        r.deliver(t)                     # start of task t
        buf.push(t, t, "B", f"s{t % 3}", t % 3 == 0, 0.01, horizon=12)
        r.update(t, "B", f"s{t % 3}", t % 3 == 0, 0.01)
        counts.append(len(inner.learned))
    assert len(inner.costs) == 12                                  # costs are immediate
    assert counts[:L] == [0] * L and counts[L] == 1                # first label arrives after L purchases
    assert all(c == max(0, t - L + 1) for t, c in enumerate(counts))
    assert inner.learned == [(t, f"s{t % 3}", t % 3 == 0) for t in range(12 - L)]
    r.flush()
    assert len(inner.learned) == 12 and r.n_label_updates_flush == L


# ---------------------------------------------------------------- sim plumbing
def test_immediate_equals_v4_default(cfg):
    m0, recs0, _ = _run(cfg, "pilot_compliant", {"market": {"budget_multiplier": 4.0}}, n_tasks=N, n_rounds=20)
    m1, recs1, _ = _run(cfg, "pilot_compliant", _fb(0, 1.0), n_tasks=N, n_rounds=20)
    keys = ("task_accuracy", "fraud_share", "joint_objective", "total_cost", "n_purchases")
    assert all(m0[k] == m1[k] for k in keys)
    assert [r["seller_id"] for r in recs0] == [r["seller_id"] for r in recs1]
    # L = 0, pi = 1: every purchase gives exactly one online bandit update
    assert m1["bandit_label_updates"] == m1["bandit_label_updates_online"] == m1["n_purchases"] > 0
    assert m1["feedback_coverage"] == 1.0 and m1["feedback_flushed"] == 0
    assert all(r["feedback_revealed"] and r["feedback_delay_L"] == 0 for r in _served(recs1))
    assert all(validate_record(r) == [] for r in recs1)


@pytest.mark.parametrize("policy", ["pilot_compliant", "stageroute_compliant"])
def test_delay_lags_updates(cfg, policy):
    L = 5
    m, recs, _ = _run(cfg, policy, _fb(L), n_tasks=N, n_rounds=20)
    sv = _served(recs)
    idx = {tid: i for i, tid in enumerate(dict.fromkeys(x["task_id"] for x in recs))}
    online = sum(1 for r in sv if idx[r["task_id"]] + L <= N - 1)
    assert m["bandit_label_updates_online"] == online == m["n_purchases"] - L
    assert m["bandit_label_updates"] == m["n_purchases"]          # remaining L flushed at the end
    assert m["feedback_flushed"] == L
    for r in sv:
        i = idx[r["task_id"]]
        assert r["feedback_delivered_at"] == min(i + L, N)


@pytest.mark.parametrize("L,pi", [("inf", 1.0), (0, 0.0)])
def test_no_labels_never_or_pi0(cfg, L, pi):
    m, recs, _ = _run(cfg, "pilot_compliant", _fb(L, pi), n_tasks=N, n_rounds=20)
    assert m["n_purchases"] > 0
    assert m["bandit_label_updates"] == 0 and m["bandit_label_updates_online"] == 0
    assert m["feedback_coverage"] == 0.0
    assert all(r["feedback_delivered_at"] is None for r in recs)
    assert all(validate_record(r) == [] for r in recs)


def test_sparse_reveal_rate(cfg):
    m, recs, _ = _run(cfg, "pilot_compliant", _fb(0, 0.2), n_tasks=400, n_rounds=40)
    frac = m["bandit_label_updates"] / m["n_purchases"]
    assert 0.12 < frac < 0.28
    assert m["bandit_label_updates"] == sum(r["feedback_revealed"] for r in _served(recs))


def test_delayed_labels_match_purchases(cfg, monkeypatch):
    """Every delivered label carries the arm id and correct bit of ITS purchase, delivered at its due step."""
    seen = []
    orig = fbmod.FeedbackBuffer.pop_ready

    def spy(self, t):
        out = orig(self, t)
        seen.extend((t, lb.task.task_id, lb.seller.id, lb.correct) for lb in out)
        return out

    monkeypatch.setattr(fbmod.FeedbackBuffer, "pop_ready", spy)
    L = 20
    m, recs, _ = _run(cfg, "pilot_compliant", _fb(L, 0.5), n_tasks=N, n_rounds=20)
    expect = sorted((r["feedback_delivered_at"], r["task_id"], r["seller_id"], r["correct"])
                    for r in _served(recs) if r["feedback_revealed"] and r["feedback_delivered_at"] < N)
    assert sorted(seen) == expect and len(seen) == m["bandit_label_updates_online"] > 0
    assert [s[0] for s in seen] == sorted(s[0] for s in seen)     # delivered in due order


def test_d3_audits_independent_of_feedback(cfg):
    over = {"fraud": {"strategy": "learning", "attack_modes_enabled": ["swap", "theft"]}}
    res = {}
    for L in (0, "inf"):
        o = dict(_fb(L), **over)
        m, recs, _ = _run(cfg, "audited_compliance_cascade", o, n_tasks=480, n_rounds=48)
        res[L] = m
        assert m["swaps_detected"] + m["thefts_detected"] > 0
        assert m["bandit_label_updates"] == 0
    a, b = res[0], res["inf"]
    for k in ("task_accuracy", "fraud_share", "swaps_detected", "thefts_detected", "joint_objective"):
        assert a[k] == b[k]                                       # D3 never uses outcome labels
    assert b["learned_swap_q"][SG] < 0.3 and b["learned_theft_q"][SG] < 0.3


def test_bandits_no_audits_in_feedback_ablation(cfg):
    from tokenmarket.sim import policy_audit_rate
    c = load_config(os.path.join(ROOT, "configs", "experiments.yaml"))
    for p in c["experiments"]["F"]["policies"]:
        assert (policy_audit_rate(c, p) > 0) == (p == "audited_compliance_cascade")
