"""Fast CPU-only v1.1 checks; no official grids or long-horizon simulation."""
import copy
import importlib.util
import itertools
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tokenmarket.audit_v1 import audit_rule, trust_feedback_on  # noqa: E402
from tokenmarket.config import deep_merge, load_config  # noqa: E402
from tokenmarket.portfolio import AUDITED_POLICIES  # noqa: E402
from tokenmarket.sim import policy_audit_checks, policy_audit_rate  # noqa: E402
from tokenmarket.wp1 import (AUDIT_RATES, PENALTIES, PIS, POLICIES, Cell, cell_config,  # noqa: E402
                             enumerate_wp1, run_cell, scale_horizon, summarize_cells)
from test_v3 import _run  # noqa: E402


@pytest.fixture
def base():
    return load_config(str(ROOT / "configs/v1.0/scale.yaml"))


@pytest.fixture
def runner():
    spec = importlib.util.spec_from_file_location("run_wp1", ROOT / "scripts/v1.1/run_wp1.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_complete_frozen_grid():
    cells = enumerate_wp1()
    assert AUDIT_RATES == (0, 0.01, 0.02, 0.03, 0.05, 0.10, 0.20)
    assert PENALTIES == (0.25, 0.0625, 0.015625)
    assert PIS == (1, 0.1, 0)
    assert len(cells) == len({c.cell_id for c in cells}) == 240
    assert sum(c.arm == "factorial" for c in cells) == 216
    assert sum(c.arm == "control" for c in cells) == 24
    audits = {f"a{a:g}" for a in AUDIT_RATES} | {"risk_adaptive"}
    for router in POLICIES:
        expected = set(itertools.product(audits, PENALTIES, PIS if router in ("pilot", "stageroute") else (1,)))
        assert {(c.audit, c.penalty, c.pi) for c in cells if c.router == router} == expected
    for cell in cells:
        assert cell.metadata()["audit_efficacy_evidence_allowed"] == (cell.penalty != 0.015625)


def test_all_cell_audit_and_trust_settings(base):
    original = copy.deepcopy(base)
    for cell in enumerate_wp1():
        cfg = cell_config(base, cell, 0)
        assert trust_feedback_on(cfg, cell.policy, AUDITED_POLICIES) == (cell.arm == "control")
        assert policy_audit_checks(cfg, cell.policy) == ["identity", "length"]
        assert policy_audit_rate(cfg, cell.policy) == (0.1 if cell.audit == "risk_adaptive"
                                                      else float(cell.audit[1:]))
        assert audit_rule(cfg, cell.policy, AUDITED_POLICIES) == (
            "risk_adaptive" if cell.audit == "risk_adaptive" else "fixed")
        assert cfg["fraud"]["penalty"] == cell.penalty
        assert cfg["fraud"]["strategy"] == "learning"
        assert cfg["fraud"]["learning"]["learner"] == "egreedy"
        assert cfg["run"]["n_rounds"] == 48 and cfg["run"]["n_tasks"] == 480
        assert cfg["market"]["audited"]["reputation_rounds"] == cfg["fraud"]["reputation_rounds"] == 0
        assert not cfg["market"]["audited"]["adaptive_audit"]
        assert not cfg["market"]["audited"]["escrow"]
    assert base == original


@pytest.mark.parametrize("n_rounds", [48, 200, 500])
def test_horizon_pairs_tasks_budgets_and_does_not_compound(base, n_rounds):
    original = copy.deepcopy(base)
    cfg = scale_horizon(base, n_rounds)
    assert cfg["run"]["n_tasks"] == 10 * n_rounds
    assert cfg["run"]["n_rounds"] == n_rounds
    factor = cfg["run"]["n_tasks"] / 480
    assert cfg["market"]["budget_multiplier"] == pytest.approx(base["market"]["budget_multiplier"] * factor)
    for before, after in zip(base["buyers"], cfg["buyers"]):
        assert after["budget"] * cfg["market"]["budget_multiplier"] == pytest.approx(
            before["budget"] * base["market"]["budget_multiplier"] * factor)
    assert scale_horizon(cfg, n_rounds) == cfg
    assert scale_horizon(scale_horizon(base, 200), 500) == scale_horizon(base, 500)
    assert base == original
    for router in POLICIES:
        point = cell_config(base, Cell(router, "a0.1", 0.25, 1), 0, n_rounds)
        assert point["run"] == cfg["run"]
        assert point["market"]["budget_multiplier"] == cfg["market"]["budget_multiplier"]


@pytest.mark.parametrize("n_rounds", [0, -1, 1.5, True])
def test_bad_horizon_rejected(base, n_rounds):
    with pytest.raises(ValueError):
        scale_horizon(base, n_rounds)


@pytest.mark.parametrize("router", list(POLICIES))
def test_routing_isolated_from_audit_results_except_trust(monkeypatch, router):
    import tokenmarket.sim as sim
    cfg = cell_config(load_config(str(ROOT / "configs/default.yaml")), Cell(router, "a0.1", 0.25, 1), 0, 4)
    # Freeze behavior and remove monetary/budget confounds: only audit information varies.
    cfg = deep_merge(cfg, {
        "fraud": {"strategy": "static", "penalty": 0, "q_static": 1},
        "market": {"budget_multiplier": 100, "audit_v11": {"rate": 1},
                   "audited": {"cascade": {"confidence_threshold": 1, "max_steps": 3}}},
    })
    original_policy = sim.run_policy

    def execute(caught):
        snapshots = []

        def observe(policy, cands, price, exp_cost, quality, *args, **kwargs):
            snapshots.append({s.id: quality(s) for s in cands})
            return original_policy(policy, cands, price, exp_cost, quality, *args, **kwargs)

        monkeypatch.setattr(sim, "run_policy", observe)
        monkeypatch.setattr(sim.IdentityCheckDetector, "detect", lambda self, cheap, rng: bool(cheap and caught))
        monkeypatch.setattr(sim.TokenLengthAuditor, "detect", lambda *a: False)
        m, records, _ = _run(cfg, POLICIES[router], n_tasks=40, n_rounds=4)
        assert m["n_audits"] > 0
        assert all(r["audit_type"] == "both" for r in records if r["audited"])
        return m, records, snapshots

    miss_m, miss, miss_q = execute(False)
    catch_m, catch, catch_q = execute(True)
    if router == "cascade+trust":
        assert catch_m["trust_feedback"] is True
        assert catch_m["swaps_detected"] > 0
        assert any(v > 0 for v in catch_m["trust_q_hat"].values())
        assert catch_q != miss_q  # Audit outcomes actually reach the cascade quality callback.
        assert [(r["task_id"], r["seller_id"]) for r in catch] != [
            (r["task_id"], r["seller_id"]) for r in miss]
    else:
        assert catch_m["trust_feedback"] is False
        assert "trust_q_hat" not in catch_m
        assert catch_q == miss_q
        assert [(r["task_id"], r["seller_id"]) for r in catch] == [
            (r["task_id"], r["seller_id"]) for r in miss]
    assert miss_m["swaps_detected"] == 0


@pytest.mark.parametrize("router", list(POLICIES))
def test_risk_adaptive_works_for_every_router(monkeypatch, router):
    import tokenmarket.sim as sim
    cfg = cell_config(load_config(str(ROOT / "configs/default.yaml")),
                      Cell(router, "risk_adaptive", 0.25, 1), 0, 4)
    cfg = deep_merge(cfg, {"market": {"budget_multiplier": 100,
                                      "audit_v11": {"risk_adaptive": {"a_min": 1, "a_max": 1}}}})
    recorded = []
    original = sim.RiskAdaptiveAudit.record

    def record(self, sid, caught):
        recorded.append((sid, caught))
        original(self, sid, caught)

    monkeypatch.setattr(sim.RiskAdaptiveAudit, "record", record)
    m, records, _ = _run(cfg, POLICIES[router], n_tasks=40, n_rounds=4)
    served = [r for r in records if r["status"] == "allowed"]
    assert served and len(recorded) == m["n_audits"] == len(served)
    assert m["audit_rule"] == "risk_adaptive"
    assert not m["adaptive_audit"]
    assert all(r["audit_type"] == "both" for r in served)


def test_disabled_block_keeps_legacy_behavior():
    base = load_config(str(ROOT / "configs/default.yaml"))
    cfg = deep_merge(base, {"market": {"audit_v11": {"enabled": False, "rate": 1,
                                                   "audit_rule": "risk_adaptive", "trust_feedback": False}}})
    for policy in POLICIES.values():
        assert policy_audit_rate(cfg, policy) == policy_audit_rate(base, policy)
        assert policy_audit_checks(cfg, policy) == policy_audit_checks(base, policy)
        assert audit_rule(cfg, policy, AUDITED_POLICIES) == audit_rule(base, policy, AUDITED_POLICIES)
        assert trust_feedback_on(cfg, policy, AUDITED_POLICIES) == (policy in AUDITED_POLICIES)


def test_run_cell_and_identifiability_summary(base, tmp_path):
    cell = Cell("strongest", "a0.1", 0.015625, 1)
    row = run_cell({"base": base, "cell": cell, "seed": 0, "n_rounds": 4, "learner": "egreedy",
                    "backend": "mock", "cache_file": "", "log_dir": tmp_path})
    assert row["n_tasks"] == 40 and row["tail_rounds"] == 1
    assert sum(row["strategic_tail_counts"].values()) == row["tail_sales"]
    assert row["q_swap"] == row["Q_swap"] and row["q_theft"] == row["Q_theft"]
    assert row["audit_checks"] == ["identity", "length"]
    records = [json.loads(line) for line in next(tmp_path.glob("*.jsonl")).read_text().splitlines()]
    strategic = set(row["strategic_tail_counts"])
    assert row["tail_sales"] == sum(r["status"] == "allowed" and r["seller_id"] in strategic
                                    and r["round"] == 3 for r in records)
    summary = summarize_cells([dict(row, tail_trade=True), dict(row, seed=1, tail_trade=False)])[0]
    assert summary["tail_trade_runs"] == 1 and summary["tail_trade_rate"] == 0.5
    assert not summary["Q_identifiable"] and not summary["audit_efficacy_evidence_allowed"]
    assert len(summary["per_run_strategic_tail_counts"]) == 2
    assert summarize_cells([dict(row, tail_trade=True)])[0]["Q_identifiable"]


def test_runner_dry_run_does_not_simulate(runner, tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "output_path", lambda value: Path(value))
    monkeypatch.setattr(runner, "run_cell", lambda job: pytest.fail("dry-run executed simulation"))
    runner.main(["--dry-run", "--out", str(tmp_path / "plan")])
    manifest = json.loads((tmp_path / "plan/manifest.json").read_text())
    meta = json.loads((tmp_path / "plan/run_meta.json").read_text())
    assert len(manifest) == 240 and meta["n_runs_planned"] == 4800
    assert not (tmp_path / "plan/completion.json").exists()


def test_runner_smoke_outputs_and_overwrite_guard(runner, tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "output_path", lambda value: Path(value))
    args = ["--mode", "smoke", "--backend-override", "mock", "--cell",
            "pilot__a0.1__P0.25__pi1", "--cell", "cascade+trust__a0.1__P0.25__pi1",
            "--out", str(tmp_path / "smoke")]
    runner.main(args)
    assert json.loads((tmp_path / "smoke/completion.json").read_text())["n_runs_completed"] == 2
    for arm in ("factorial", "control"):
        assert (tmp_path / f"smoke/{arm}/per_seed.csv").exists()
        assert b"\r" not in (tmp_path / f"smoke/{arm}/per_seed.csv").read_bytes()
        assert len(json.loads((tmp_path / f"smoke/{arm}/cells.json").read_text())) == 1
    with pytest.raises(SystemExit):
        runner.main(args)


@pytest.mark.parametrize("extra", [
    ["--seeds", "0"], ["--cell", "pilot__a0__P0.25__pi1"],
    ["--n-rounds", "200"], ["--learner", "exp3"], ["--backend-override", "mock"],
    ["--mode", "smoke"], ["--mode", "smoke", "--cell", "pilot__a0__P0.25__pi1", "--n-rounds", "200"],
])
def test_runner_rejects_partial_official_or_large_smoke(runner, tmp_path, extra):
    with pytest.raises(SystemExit):
        runner.main(["--out", str(tmp_path / "bad")] + extra)
    assert not (tmp_path / "bad").exists()


@pytest.mark.parametrize("path", ["results/v1.0/x", "release/v1.0/x", "release/v0.1/x", "/tmp/wp1"])
def test_runner_protected_outputs(runner, path):
    with pytest.raises(ValueError):
        runner.output_path(path)


def test_output_symlink_escape_rejected(runner, tmp_path, monkeypatch):
    fake = tmp_path / "repo"
    (fake / "results/v1.1").mkdir(parents=True)
    (fake / "results/v1.1/escape").symlink_to(tmp_path, target_is_directory=True)
    monkeypatch.setattr(runner, "ROOT", fake)
    with pytest.raises(ValueError):
        runner.output_path(fake / "results/v1.1/escape/protected")
