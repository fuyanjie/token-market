"""Decision A preparation tests: synthetic fixtures only, never run the official grid."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from tokenmarket import decision_a as design
from tokenmarket.config import load_config
from tokenmarket.wp1 import cell_config

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/v1.1/PROTOCOL_v1.2.md"
PINS = ["--protocol", str(PROTOCOL), "--protocol-sha256", design.PROTOCOL_SHA256]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/v1.1/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def analysis():
    return load("analyze_decision_a")


def test_official_plan_and_pairing(tmp_path, monkeypatch):
    runner = load("run_wp1")
    monkeypatch.setattr(design, "fresh_output", lambda *args: tmp_path / "plan")
    monkeypatch.setattr(design, "run_job", lambda job: pytest.fail("simulation forbidden"))
    runner.main(["--mode", "decision_a", "--dry-run", "--out", "unused", "--jobs", "8", *PINS])
    meta = json.loads((tmp_path / "plan/run_meta.json").read_text())
    manifest = json.loads((tmp_path / "plan/manifest.json").read_text())
    assert meta["n_runs_planned"] == 2880
    assert meta["n_cells"] == len(manifest) == 48
    assert meta["learners"] == list(design.LEARNERS)
    assert meta["seeds"] == list(range(20))
    assert meta["n_rounds"] == 1000 and meta["n_tasks"] == 10000
    assert meta["budget_multiplier"] == 10000 / 240
    assert sum(c["router"] == "pilot" for c in manifest) == 24
    assert sum(c["router"] == "strongest" for c in manifest) == 24
    assert all(c["pi"] == 1 and not c["trust_feedback"] and c["arm"] == "factorial"
               for c in manifest)
    assert not (tmp_path / "plan/transactions").exists()
    assert not (tmp_path / "plan/completion.json").exists()


@pytest.mark.parametrize("extra", [
    ["--n-rounds", "500"], ["--learner", "egreedy"], ["--learner=exp3"],
    ["--learn", "exp3"], ["--backend-override", "mock"], ["--seeds", "0"],
    ["--cell", "pilot__a0__P0.25__pi1"], ["--cell", "cascade__a0__P0.25__pi1"],
    ["--config", str(ROOT / "configs/default.yaml")],
    ["--protocol-sha256", "0" * 64],
    ["--protocol", str(ROOT / "docs/v1.1/PROTOCOL_v1.1.md")],
])
def test_unofficial_knobs_rejected(tmp_path, extra):
    with pytest.raises(SystemExit):
        load("run_wp1").main(["--mode", "decision_a", "--dry-run",
                              "--out", str(tmp_path / "bad"), *PINS, *extra])
    assert not (tmp_path / "bad").exists()


def test_explicit_pins_required(tmp_path):
    with pytest.raises(SystemExit):
        load("run_wp1").main(["--mode", "decision_a", "--dry-run", "--out", str(tmp_path / "bad")])


@pytest.mark.parametrize("name", design.PROTECTED)
def test_protected_paths_and_descendants(name, analysis):
    for out in (ROOT / "results/v1.1" / name, ROOT / "results/v1.1" / name / "new"):
        with pytest.raises(ValueError, match="protected"):
            analysis.main(["--run", "/not/read", "--out", str(out), *PINS])


def test_output_isolation_symlinks_and_any_published_eval(tmp_path):
    results = tmp_path / "results/v1.1"
    results.mkdir(parents=True)
    published = results / "custom_eval"
    published.mkdir()
    (published / "published_readout.csv").write_text("published data\n")
    (results / "alias").symlink_to(published, target_is_directory=True)
    (results / "escape").symlink_to(tmp_path / "elsewhere", target_is_directory=True)
    for out in (published, published / "new", results / "alias/new",
                results / "escape", results, tmp_path / "outside"):
        with pytest.raises(ValueError):
            design.fresh_output(tmp_path, out)
    run = results / "source_run"
    for out in (run, run / "new", results / "container"):
        with pytest.raises(ValueError):
            design.fresh_output(tmp_path, out, run if out != results / "container" else out / "run")
    out = results / "fresh"
    assert design.fresh_output(tmp_path, out) == out


def test_official_wp2_fact_includes_exp3(analysis):
    fact = analysis.wp2_fact()
    assert fact["recommended_n_rounds"] == 1000
    assert not fact["stop_and_ask"]
    assert fact["EXP3_included_in_direction_consistency"]
    assert fact["voting_learners"] == list(design.LEARNERS)


def vote_rows(deltas=(-1, 0, -1)):
    return [dict(learner=l, testable=True, significant_report=d != 0,
                 significant_decision_a=d != 0, delta_mean=d,
                 router="pilot", audit="a0.1", penalty=0.25, metric="E",
                 audit_efficacy_evidence_allowed=True,
                 astar_relation={"relation": "at_or_above"})
            for l, d in zip(design.LEARNERS, deltas)]


def test_exp3_can_supply_second_vote_and_veto(analysis):
    assert analysis.direction_vote(vote_rows(), "significant_report")["consistent_down"]
    assert not analysis.direction_vote(vote_rows((-1, -1, 1)), "significant_report")["consistent_down"]
    assert analysis.direction_vote(vote_rows((-1, -1, 0)), "significant_report")["consistent_down"]
    with pytest.raises(ValueError):
        analysis.direction_vote(vote_rows()[:2], "significant_report")


def test_classification_and_p16_exclusion(analysis):
    rows = vote_rows()
    verdict = analysis.classify(rows)
    assert verdict["result"] == verdict["routers"]["pilot"]["result"] == 1
    assert verdict["routers"]["strongest"]["result"] == 3
    assert not verdict["both_routers_default_pass"]
    for row in rows:
        row["significant_decision_a"] = False
    assert analysis.classify(rows)["result"] == 2
    for row in rows:
        row.update(penalty=0.015625, audit_efficacy_evidence_allowed=False)
    assert analysis.classify(rows)["result"] == 3
    for row in rows:
        row.update(p_raw=0.0)
    _, count = analysis.correct_families(rows)
    assert count == 0
    assert all(r["p_holm_decision_a"] is None for r in rows)
    assert analysis.classify(rows)["result"] == 3
    assert analysis.classify(vote_rows((-1, -1, 1)))["result"] == 3


def test_one_merged_holm_family_not_per_router_or_learner(analysis):
    rows = []
    for router in ("pilot", "strongest"):
        for row in vote_rows():
            rows.append(dict(row, router=router, p_raw=0.01))
    families, count = analysis.correct_families(rows)
    assert len(families) == 6 and count == 6
    assert {r["decision_a_family"] for r in rows} == {analysis.DECISION_FAMILY}
    assert all(r["significant_report"] and not r["significant_decision_a"] for r in rows)
    assert all(r["p_holm_decision_a"] == pytest.approx(0.06) for r in rows)
    assert analysis.classify(rows)["result"] == 2


@pytest.fixture(scope="module")
def synthetic_rows():
    """Invented measurements, NOT simulations or experimental results."""
    base = load_config(str(ROOT / "configs/v1.0/scale.yaml"))
    rows = []
    for cell in design.cells():
        for learner in design.LEARNERS:
            for seed in range(20):
                cfg = cell_config(base, cell, seed, 1000, learner)
                value = 0.5 + seed / 100 - (0.1 if cell.audit != "a0" else 0)
                rows.append(dict(
                    cell.metadata(), learner=learner, seed=seed, n_rounds=1000, n_tasks=10000,
                    budget_multiplier=design.BUDGET_MULTIPLIER, tail_rounds=250,
                    tail_trade=True, tail_sales=1, strategic_tail_counts={"synthetic": 1},
                    q_delisted_mean=None,
                    E=value, E_tok=value, Q=value, q_swap=value, q_theft=value, q_downgrade=value,
                    accuracy=value, cost_per_task=value, audit_rate_realised=0.1,
                    audit_checks=["identity", "length"],
                    audit_rule="risk_adaptive" if cell.audit == "risk_adaptive" else "fixed",
                    config_hash=hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()))
    return rows


def test_learner_specific_summaries_and_log_names(synthetic_rows, tmp_path, monkeypatch):
    summary = design.summarize(synthetic_rows)
    assert len(summary) == 144 and all(s["n_runs"] == 20 for s in summary)
    assert len({(s["cell_id"], s["learner"]) for s in summary}) == 144
    calls = []
    monkeypatch.setattr(design, "run_cell", lambda job: calls.append(job))
    for learner in design.LEARNERS:
        design.run_job(dict(learner=learner, log_dir=tmp_path))
    assert {j["log_dir"] for j in calls} == {tmp_path / l for l in design.LEARNERS}


def test_paired_bootstrap_and_strict_q_identifiability(analysis, synthetic_rows):
    selected = [copy.deepcopy(r) for r in synthetic_rows if r["router"] == "pilot"
                and r["penalty"] == 0.25 and r["audit"] in ("a0", "a0.1")]
    for r in selected:
        if r["audit"] != "a0":
            r["tail_trade"] = r["seed"] < 10
    payload = analysis.analyze(selected)
    assert analysis.stats.B == 10000
    for c in payload["contrasts"]:
        assert c["delta_mean"] == pytest.approx(-0.1)
        assert c["delta_lo"] == pytest.approx(-0.1)
        assert c["delta_hi"] == pytest.approx(-0.1)
        if c["metric"] == "Q":
            assert not c["testable"] and c["p_raw"] is None
            assert c["p_holm_report"] is None and c["p_holm_decision_a"] is None
        else:
            assert c["testable"] and c["p_raw"] == 0
    assert payload["decision_a_family"]["n_tests"] == 3
    assert all(c["Q"]["mean"] > 0 for c in payload["cells"])
    assert analysis.astar("a0.05", 0.25, 0)["relation"] == "at_or_above"
    assert analysis.astar("a0.02", 0.25, 0)["relation"] == "below"
    assert analysis.astar("risk_adaptive", 0.0625, 0.19)["relation"] == "in_interval"


def test_full_synthetic_validation_and_readout(analysis, synthetic_rows, tmp_path, monkeypatch):
    """Exercise full file plumbing using manufactured data under pytest's temp tree."""
    runner = load("run_wp1")
    fake = tmp_path / "repo"
    fake.mkdir()
    for name in ("configs", "docs"):
        (fake / name).symlink_to(ROOT / name, target_is_directory=True)
    run = fake / "results/v1.1/synthetic_run"
    run.mkdir(parents=True)
    (run / "factorial").mkdir()
    base = load_config(str(ROOT / "configs/v1.0/scale.yaml"))
    meta = dict(mode="decision_a", dry_run=False, protocol_sha256=design.PROTOCOL_SHA256,
                n_rounds=1000, n_tasks=10000, budget_multiplier=design.BUDGET_MULTIPLIER,
                seeds=list(range(20)), learners=list(design.LEARNERS), learner="all",
                backend_override=None, n_cells=48, n_factorial_cells=48, n_control_cells=0,
                n_runs_planned=2880, base_config=base)
    runner.write_json(run / "run_meta.json", meta)
    runner.write_json(run / "manifest.json", [c.metadata() for c in design.cells()])
    runner.write_json(run / "completion.json", {"n_runs_completed": 2880})
    runner.write_json(run / "factorial/cells.json", design.summarize(synthetic_rows))
    runner.write_csv(run / "factorial/per_seed.csv", synthetic_rows)
    (run / "completed_runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in synthetic_rows))
    monkeypatch.setattr(analysis, "ROOT", fake)
    out = fake / "results/v1.1/synthetic_eval"
    args = ["--run", str(run), "--out", str(out), *PINS]
    analysis.main(args)
    payload = json.loads((out / "decision_a_eval.json").read_text())
    assert payload["checks"]["runs"] == 2880
    assert len(payload["cells"]) == 144 and len(payload["contrasts"]) == 252
    assert payload["decision_a_family"]["n_tests"] == 84
    assert set(payload["report_family_sizes"].values()) == {42}
    assert payload["classification"]["result"] == 1
    assert payload["classification"]["both_routers_default_pass"]
    assert all(c["decision_a_family"] is None for c in payload["contrasts"] if c["penalty"] == 0.015625)
    for path in out.iterdir():
        if path.suffix != ".sha256":
            assert (out / (path.name + ".sha256")).read_text() == (
                f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n")
    assert not (fake / "results/v1.1/wp1_eval").exists()
    with pytest.raises(ValueError, match="fresh/empty"):
        analysis.main(args)
    # No output gets created if evidence is incomplete or artifacts disagree.
    with (run / "completed_runs.jsonl").open("a") as fh:
        fh.write(json.dumps(synthetic_rows[0]) + "\n")
    with pytest.raises(ValueError, match="grid required"):
        analysis.main(["--run", str(run), "--out", str(out.parent / "invalid"), *PINS])
    assert not (out.parent / "invalid").exists()
