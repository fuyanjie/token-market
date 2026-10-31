import copy
import os
import random
import subprocess
import sys

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tokenmarket.backends import MockLLM, format_confidence, parse_answer, parse_final_number  # noqa: E402
from tokenmarket.buyers import load_buyers  # noqa: E402
from tokenmarket.cache import OutputCache  # noqa: E402
from tokenmarket.compliance import ComplianceEngine  # noqa: E402
from tokenmarket.gateway import CrossBorderGateway  # noqa: E402
from tokenmarket.logging_schema import FIELDS, read_log, validate_record  # noqa: E402
from tokenmarket.matching import run_auction  # noqa: E402
from tokenmarket.portfolio import HARD_POLICIES, Purchase, majority_vote, run_policy  # noqa: E402
from tokenmarket.precompute import model_stats, precompute  # noqa: E402
from tokenmarket.sellers import load_sellers  # noqa: E402
from tokenmarket.sim import run_all  # noqa: E402
from tokenmarket.tasks import Task, build_task_pool, generate_stream, sample_run_tasks  # noqa: E402
from tokenmarket.verification import TEEAttestationVerifier, TrustingVerifier, VerificationModule  # noqa: E402

REQUIRED = ["ts", "round", "run_id", "mechanism", "policy", "seed", "buyer_id", "buyer_jurisdiction",
            "task_id", "sensitivity", "seller_id", "seller_jurisdiction", "claimed_model", "actual_model",
            "cross_border", "price_per_1k", "reasoning_tokens", "cost", "fee", "latency_ms", "answer",
            "gold", "correct", "status", "rule_id", "buyer_surplus", "seller_profit",
            # v2
            "portfolio_step", "final", "final_answer", "final_correct", "expected_cost", "actual_cost",
            "cost_overrun", "budget_remaining", "budget_overrun", "violation", "confidence", "backend"]
N_TASKS = 60
QUIET = lambda *a, **k: None  # noqa: E731


@pytest.fixture(scope="module")
def cfg():
    with open(os.path.join(ROOT, "configs", "default.yaml"), encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="module")
def small_run(cfg, tmp_path_factory):
    out = tmp_path_factory.mktemp("results")
    c = copy.deepcopy(cfg)
    c["run"]["n_rounds"] = 3
    summary = run_all(c, seeds=[0, 1], backend_name="mock", n_tasks=N_TASKS, results_dir=str(out),
                      cache_path=str(out / "no_cache.jsonl"), log=QUIET)
    assert not os.path.exists(out / "no_cache.jsonl")  # mock override never touches the cache
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
        for k in ("id", "jurisdiction", "backend", "claimed_model", "actual_model", "price_per_1k", "latency",
                  "capacity_per_round"):
            assert k in s
    by = {s["id"]: s for s in sellers}
    assert by["seller_cn"]["backend"] == by["seller_sg"]["backend"] == "local_hf"
    assert by["seller_br"]["backend"] == "mock"
    assert by["seller_cn"]["claimed_model"] == by["seller_cn"]["actual_model"] == "Qwen/Qwen2.5-1.5B-Instruct"
    fraud = [s for s in sellers if s["claimed_model"] != s["actual_model"]]
    assert len(fraud) == 1 and fraud[0]["id"] == "seller_sg"
    assert fraud[0]["claimed_model"] == "Qwen/Qwen2.5-1.5B-Instruct"
    assert fraud[0]["actual_model"] == "Qwen/Qwen2.5-0.5B-Instruct"
    assert fraud[0]["price_per_1k"] < by["seller_cn"]["price_per_1k"]
    m = cfg["models"]
    assert m[fraud[0]["actual_model"]]["accuracy"][3] < m[fraud[0]["claimed_model"]]["accuracy"][3]


def test_sim_runs_full_matrix(small_run):
    summary, _, out = small_run
    pols = ("single_cheapest_compliant", "single_best_compliant", "cascade_compliant", "vote_k_compliant",
            "compliance_unaware_cheapest")
    expected = {f"posted_price/{p}" for p in pols} | {
        f"sealed_bid/{p}" for p in ("single_cheapest_compliant", "single_best_compliant",
                                    "compliance_unaware_cheapest")}
    assert set(summary["combos"]) == expected
    for f in ("summary.json", "summary.md", "model_accuracy.md"):
        assert os.path.exists(os.path.join(out, f))
    md = open(os.path.join(out, "summary.md"), encoding="utf-8").read()
    assert "C2 baseline comparison" in md and "Mechanism comparison" in md


def test_one_log_line_per_purchase(small_run):
    summary, recs, _ = small_run
    assert len(recs) == summary["log_lines"]
    keys = [(r["run_id"], r["task_id"], r["portfolio_step"]) for r in recs]
    assert len(set(keys)) == len(keys)  # one line per (task, seller purchase)
    by_task = {}
    for r in recs:
        by_task.setdefault((r["run_id"], r["task_id"]), []).append(r)
    assert len(by_task) == 8 * 2 * N_TASKS  # every task of every run appears
    for lines in by_task.values():
        assert sum(r["final"] for r in lines) == 1 and lines[-1]["final"]
        assert [r["portfolio_step"] for r in lines] == list(range(len(lines)))
        assert len({r["seller_id"] for r in lines}) == len(lines)  # never buys the same seller twice
    for c in summary["combos"].values():
        for m in c["per_seed"]:
            assert m["n_lines"] == m["n_purchases"] + m["n_blocked"] + m["n_unfilled"]
            assert m["n_tasks"] == N_TASKS


def test_schema_valid(small_run):
    _, recs, _ = small_run
    assert set(REQUIRED) <= set(FIELDS)
    for r in recs:
        assert validate_record(r) == [], r
    assert validate_record({"status": "allowed"})  # missing fields detected
    assert validate_record(dict(recs[0], final=False, final_answer=3))
    assert validate_record(dict(recs[0], status="allowed", violation=True, rule_id=None))
    statuses = {r["status"] for r in recs}
    assert "allowed" in statuses and statuses <= {"allowed", "blocked", "unfilled"}


def test_hard_policies_zero_violations(small_run):
    summary, recs, _ = small_run
    for c in summary["combos"].values():
        if c["policy"] in HARD_POLICIES:
            for m in c["per_seed"]:
                assert m["compliance_violations"] == 0
                assert m["audit_violations_enforced"] == 0
                assert m["blocked_at_gateway"] == 0  # infeasible sellers are filtered BEFORE purchase
            assert c["aggregate"]["filtered_candidates"]["mean"] > 0
    for r in recs:
        if r["policy"] in HARD_POLICIES:
            assert r["violation"] is False and r["status"] != "blocked"


def test_unaware_baseline_has_violations(small_run):
    summary, recs, _ = small_run
    c = summary["combos"]["posted_price/compliance_unaware_cheapest"]
    assert all(m["compliance_violations"] > 0 for m in c["per_seed"])
    v = [r for r in recs if r["violation"]]
    assert v and all(r["policy"] == "compliance_unaware_cheapest" for r in v)
    assert all(r["status"] == "allowed" and r["rule_id"] and r["cross_border"] for r in v)


def test_budget_expected_cost_check(small_run):
    _, recs, _ = small_run
    n = 0
    for r in recs:
        if r["status"] != "allowed":
            continue
        n += 1
        before = r["budget_remaining"] + r["actual_cost"]
        assert r["expected_cost"] <= before + 1e-9            # purchase made only if expected cost fits
        assert r["actual_cost"] == pytest.approx(r["cost"] + r["fee"])
        assert r["cost_overrun"] == pytest.approx(r["actual_cost"] - r["expected_cost"])
        assert r["budget_overrun"] == (r["budget_remaining"] < -1e-12)
    assert n


def test_cascade_buys_between_1_and_n(small_run, cfg):
    _, recs, _ = small_run
    n = len(cfg["sellers"])
    by_task = {}
    for r in recs:
        if r["policy"] == "cascade_compliant" and r["status"] == "allowed":
            by_task.setdefault((r["run_id"], r["task_id"]), []).append(r)
    assert by_task
    sizes = [len(v) for v in by_task.values()]
    assert min(sizes) >= 1 and max(sizes) <= n and max(sizes) > 1
    thr = cfg["market"]["cascade"]["confidence_threshold"]
    for v in by_task.values():   # escalation only happens after a low-confidence answer
        for r in v[:-1]:
            assert r["answer"] is None or r["confidence"] < thr


class _S:
    def __init__(self, id, q, c):
        self.id, self.q, self.c = id, q, c


def test_vote_majority_logic():
    a, b, c = _S("a", 0.9, 3), _S("b", 0.6, 1), _S("c", 0.7, 2)
    P = lambda s, ans: Purchase(s, ans, 0.5, s.q)  # noqa: E731
    assert majority_vote([P(a, 5), P(b, 7), P(c, 7)]) == 7                 # majority beats quality
    assert majority_vote([P(a, 5), P(b, 7)]) == 5                          # tie -> higher-quality seller
    assert majority_vote([P(b, 7), P(c, 9)]) == 9
    assert majority_vote([P(a, None), P(b, 7)]) == 7                       # unparsed answers ignored
    assert majority_vote([Purchase(a, 5, None, 0.9, served=False), P(b, 7)]) == 7
    assert majority_vote([]) is None
    answers, bought = {"a": 5, "b": 7, "c": 7}, []

    def buy(s, price, step):
        if s.id == "c":
            return None  # budget refusal
        bought.append((s.id, step))
        return Purchase(s, answers[s.id], 0.5, s.q)
    d = run_policy("vote_k_compliant", [a, b, c], lambda s: 1.0, lambda s: s.c, lambda s: s.q, buy,
                   {"vote": {"k": 3}})
    assert bought == [("a", 0), ("b", 1)] and d.final_answer == 5 and d.stop_reason == "budget"


def test_cascade_policy_logic():
    cheap, mid, strong = _S("cheap", 0.5, 1), _S("mid", 0.8, 2), _S("strong", 0.9, 3)
    conf, log = {"cheap": 0.3, "mid": 0.9, "strong": 0.95}, []

    def buy(s, price, step):
        log.append(s.id)
        return Purchase(s, 42 if s.id != "cheap" else 41, conf[s.id], s.q)
    mk = {"cascade": {"confidence_threshold": 0.7, "max_steps": 3}}
    args = ([strong, mid, cheap], lambda s: 1.0, lambda s: s.c, lambda s: s.q, buy, mk)
    d = run_policy("cascade_compliant", *args)
    assert log == ["cheap", "mid"] and d.final_answer == 42 and d.stop_reason == "confident"
    conf["cheap"] = 0.8
    log.clear()
    d = run_policy("cascade_compliant", *args)
    assert log == ["cheap"] and d.final_answer == 41
    conf.update(cheap=0.1, mid=0.2, strong=0.3)
    log.clear()
    d = run_policy("cascade_compliant", *args)
    assert log == ["cheap", "mid", "strong"] and d.stop_reason == "exhausted" and d.final_answer == 42


def test_fraud_seller_logs_claimed_ne_actual(small_run):
    _, recs, _ = small_run
    sg = [r for r in recs if r["seller_id"] == "seller_sg" and r["status"] == "allowed"]
    assert sg
    assert all(r["claimed_model"] == "Qwen/Qwen2.5-1.5B-Instruct" and
               r["actual_model"] == "Qwen/Qwen2.5-0.5B-Instruct" for r in sg)
    honest = [r for r in recs if r["seller_id"] in ("seller_cn", "seller_br")]
    assert all(r["claimed_model"] == r["actual_model"] for r in honest)
    assert all(r["backend"] == "mock" for r in recs if r["backend"])  # override applied


def test_gateway_audit_mode(cfg):
    eng = ComplianceEngine.from_config(cfg)
    b = {x.id: x for x in load_buyers(cfg)}["buyer_cn_1"]
    s = {x.id: x for x in load_sellers(cfg)}["seller_sg"]
    t = Task("t", "logic", 1, "q", 1, b.id, "important_data")
    res = CrossBorderGateway(eng, cfg, mode="audit_only").route(b, s, t)
    assert res.allowed and res.violation and res.rule_id == "CN-DSL-31"
    res = CrossBorderGateway(eng, cfg, mode="enforce").route(b, s, t)
    assert not res.allowed and not res.violation


def test_task_pool_fixed_and_seed_sampling(cfg):
    pool = build_task_pool(cfg)
    assert len(pool) == 80 and pool == build_task_pool(cfg)
    assert {t.difficulty for t in pool} == {1, 2, 3}
    buyers = load_buyers(cfg)
    a, b = sample_run_tasks(pool, buyers, 160, 0), sample_run_tasks(pool, buyers, 160, 1)
    qs = {t.question for t in pool}
    assert all(t.question in qs for t in a + b)                 # always from the fixed pool -> cache hits
    assert [t.question for t in a] != [t.question for t in b]   # seeds vary sampling
    assert len({t.task_id for t in a}) == 160


class FakeRunner:
    """Stands in for LocalHFRunner: no model load, deterministic outputs."""
    instances = []

    def __init__(self, name):
        self.name, self.loaded, self.calls = name, False, 0
        FakeRunner.instances.append(self)

    def load(self):
        self.loaded = True
        return self

    def unload(self):
        self.loaded = False

    def generate(self, prompts, max_new_tokens):
        assert self.loaded
        self.calls += 1
        n = 40 if "1.5B" in self.name else 25
        return [(f"1 + 1 = 2\nAnswer: {len(p) % 7}", n) for p in prompts], 0.01 * len(prompts)


def test_local_cache_read_write(cfg, tmp_path):
    c = copy.deepcopy(cfg)
    c["task_pool"]["size"] = 12
    c["backends"]["local_hf"]["batch_size"] = 5
    pool = build_task_pool(c)
    path = str(tmp_path / "llm_outputs.jsonl")
    FakeRunner.instances.clear()
    rep = precompute(c, OutputCache(path), pool, runner_factory=FakeRunner, log=QUIET)
    assert {m: r["n_new"] for m, r in rep.items()} == {"Qwen/Qwen2.5-0.5B-Instruct": 12,
                                                       "Qwen/Qwen2.5-1.5B-Instruct": 12}
    assert [r.calls for r in FakeRunner.instances] == [3, 3]           # one model at a time, batched
    assert all(not r.loaded for r in FakeRunner.instances)              # freed after use
    assert len(open(path, encoding="utf-8").read().splitlines()) == 24
    cache = OutputCache(path)                                           # re-read from disk
    rec = next(iter(cache._data.values()))
    for k in ("model_name", "prompt_sha256", "max_new_tokens", "raw_text", "parsed_answer", "correct",
              "reasoning_tokens", "gen_time_s"):
        assert k in rec
    FakeRunner.instances.clear()
    rep2 = precompute(c, cache, pool, runner_factory=FakeRunner, log=QUIET)
    assert all(r["n_new"] == 0 for r in rep2.values()) and FakeRunner.instances == []   # cache hit, no load
    st = model_stats(cache, pool, "Qwen/Qwen2.5-1.5B-Instruct", c["backends"]["local_hf"]["max_new_tokens"])
    assert st["tokens_mean"] == 40 and st["n"] == 12
    assert model_stats(cache, pool, "Qwen/Qwen2.5-1.5B-Instruct", 999) is None   # key includes max_new_tokens
    out = tmp_path / "res"
    summ = run_all(c, seeds=[0], n_tasks=24, results_dir=str(out), cache_path=path,
                   runner_factory=FakeRunner, log=QUIET)
    assert FakeRunner.instances == []
    recs = read_log(os.path.join(str(out), "transactions.jsonl"))
    sg = [r for r in recs if r["seller_id"] == "seller_sg" and r["status"] == "allowed"]
    assert sg and all(r["backend"] == "local_hf" and r["reasoning_tokens"] == 25 for r in sg)
    r15 = summ["reputation"]["Qwen/Qwen2.5-1.5B-Instruct"]
    assert r15["source"] == "measured" and r15["tokens_mean"] == 40
    # fraud seller: expected cost uses the CLAIMED model's tokens (40); actual uses 25 -> negative overrun
    assert all(r["cost_overrun"] < 0 for r in sg)


def test_mock_run_needs_no_torch(tmp_path):
    code = ("import sys, builtins, yaml\n"
            "real = builtins.__import__\n"
            "def guard(n, *a, **k):\n"
            "    if n.split('.')[0] in ('torch', 'transformers'):\n"
            "        raise ImportError('blocked ' + n)\n"
            "    return real(n, *a, **k)\n"
            "builtins.__import__ = guard\n"
            f"sys.path.insert(0, {ROOT!r})\n"
            "from tokenmarket.sim import run_all\n"
            f"cfg = yaml.safe_load(open({os.path.join(ROOT, 'configs', 'default.yaml')!r}))\n"
            f"run_all(cfg, seeds=[0], backend_name='mock', n_tasks=12, results_dir={str(tmp_path)!r}, "
            "log=lambda *a: None)\n")
    subprocess.run([sys.executable, "-c", code], check=True)


def test_answer_parser_and_confidence():
    assert parse_answer("x = 85\nAnswer: \\( 85 \\)") == (85, True, 1)
    assert parse_answer("**Answer:** $1,234") == (1234, True, 1)
    assert parse_answer("Answer: 3. Wait. Answer: 5") == (5, True, 2)
    assert parse_answer("the result is 12 then 14") == (14, False, 0)
    assert parse_answer("no numbers") == (None, False, 0)
    assert format_confidence("2+2=4\nAnswer: 4", 4, 10, 256) == 0.9
    assert format_confidence("so\nAnswer: 4", 4, 10, 256) == 0.6
    assert format_confidence("2+2=4 so 4", 4, 10, 256) == 0.2
    assert format_confidence("2+2=4\nAnswer: 4", 4, 256, 256) == 0.2   # truncated
    assert format_confidence("Answer: 3. Answer: 4", 4, 10, 256) == 0.4
    assert format_confidence("nothing", None, 10, 256) == 0.0


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
