"""Fast runner/analysis regressions; no official grids are executed."""
from collections import defaultdict
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import types

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    path = ROOT / f"scripts/v1.1/{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("name", ["run_wp1", "run_wp2"])
def test_default_plan_byte_compatible_with_head(name, tmp_path, monkeypatch):
    runner = load(name)
    old = types.ModuleType("old_runner")
    old.__file__ = str(ROOT / f"scripts/v1.1/{name}.py")
    source = subprocess.check_output(
        ["git", "--no-pager", "-C", str(ROOT), "show", f"HEAD:scripts/v1.1/{name}.py"],
        text=True)
    exec(compile(source, old.__file__, "exec"), old.__dict__)
    for module, dest in ((old, tmp_path / "old"), (runner, tmp_path / "new")):
        monkeypatch.setattr(module, "output_path", lambda value, dest=dest: dest)
        module.main(["--dry-run", "--out", "same-argv"])
    for filename in ("manifest.json", "run_meta.json"):
        assert (tmp_path / "old" / filename).read_bytes() == (
            tmp_path / "new" / filename).read_bytes()


@pytest.mark.parametrize("name", ["run_wp1", "run_wp2"])
def test_protocol_override_and_fail_closed(name, tmp_path, monkeypatch):
    runner = load(name)
    protocol = tmp_path / "frozen.txt"
    protocol.write_text("Test-only protocol pin; not a v1.2 protocol.\n")
    digest = hashlib.sha256(protocol.read_bytes()).hexdigest()
    out = tmp_path / "out"
    monkeypatch.setattr(runner, "output_path", lambda value: out)
    monkeypatch.setattr(runner, "run_cell" if name == "run_wp1" else "run_wp2_cell",
                        lambda job: pytest.fail("dry-run simulated"))
    args = ["--dry-run", "--out", str(out), "--protocol", str(protocol)]
    with pytest.raises(SystemExit):
        runner.main(args)
    assert not out.exists()
    runner.main(args + ["--protocol-sha256", digest])
    meta = json.loads((out / "run_meta.json").read_text())
    assert meta["protocol_sha256"] == digest
    assert meta["protocol_path"] == str(protocol)
    assert meta["n_runs_planned"] == (4800 if name == "run_wp1" else 540)


def test_official_r1000_plan(tmp_path, monkeypatch, capsys):
    runner = load("run_wp2")
    out = tmp_path / "plan"
    monkeypatch.setattr(runner, "output_path", lambda value: out)
    monkeypatch.setattr(runner, "run_wp2_cell", lambda job: pytest.fail("dry-run simulated"))
    runner.main(["--official-r1000", "--dry-run", "--out", str(out)])
    meta = json.loads((out / "run_meta.json").read_text())
    assert runner.WP2_ROUNDS == (48, 200, 500)
    assert meta["official"] and meta["n_runs_planned"] == 180
    assert meta["n_rounds"] == [1000] and meta["n_run_groups"] == 9
    assert meta["pairing"]["1000"]["n_tasks"] == 10000
    assert meta["pairing"]["1000"]["budget_multiplier"] == 2 * 10000 / 480
    jobs = [json.loads(line) for line in capsys.readouterr().out.splitlines()][1:]
    assert {(j["router"], j["learner"], j["seed"], j["n_rounds"]) for j in jobs} == set(
        itertools.product(("pilot", "strongest", "cascade"), runner.WP2_LEARNERS, range(20), (1000,)))
    assert len(jobs) == 180 and not (out / "completion.json").exists()


@pytest.mark.parametrize("extra", [
    ["--seeds", "0"], ["--learner", "egreedy"], ["--n-rounds", "48"],
    ["--cell", "pilot__a0.1__P0.25__pi1"], ["--official"],
])
def test_partial_r1000_official_rejected(tmp_path, extra):
    with pytest.raises(SystemExit):
        load("run_wp2").main(["--official-r1000", "--out", str(tmp_path / "bad"), *extra])
    assert not (tmp_path / "bad").exists()


def test_one_cell_smoke_selection(tmp_path, monkeypatch):
    runner = load("run_wp2")
    out = tmp_path / "plan"
    monkeypatch.setattr(runner, "output_path", lambda value: out)
    runner.main(["--dry-run", "--out", str(out), "--n-rounds", "1000",
                 "--seeds", "0", "--learner", "egreedy",
                 "--cell", "pilot__a0.1__P0.25__pi1"])
    meta = json.loads((out / "run_meta.json").read_text())
    assert meta["n_runs_planned"] == 1 and not meta["official"]


def test_existing_analysis_exact_reproduction():
    analysis = load("analyze_wp2")
    groups, checks, _ = analysis.validate_inputs()
    results, recommended, exp3 = analysis.analyze(groups)
    old = json.loads((ROOT / "results/v1.1/wp2_eval/wp2_eval.json").read_text())
    assert results == old["groups"]
    assert checks == old["checks"]
    assert recommended == old["recommended_n_rounds"]
    assert exp3 == old["EXP3_converged_both_decision_routers_at_500"]
    assert analysis.result_table(results) in (
        ROOT / "results/v1.1/wp2_eval/wp2_eval.md").read_text()


def fake_groups(analysis):
    horizons = (*analysis.HORIZONS, 1000)
    return defaultdict(list, {
        (router, learner, n): [
            {"seed": seed, "Q3": 0.2 if n < 1000 else 0.0, "Q4": 0.0,
             "Q": 0.0, "E": 0.0, "tail_trade": True} for seed in range(20)]
        for router, learner, n in itertools.product(analysis.ROUTERS, analysis.LEARNERS, horizons)})


def test_r1000_recommendation_and_strict_identifiability():
    analysis = load("analyze_wp2")
    groups = fake_groups(analysis)
    horizons = (*analysis.HORIZONS, 1000)
    assert analysis.analyze(groups, horizons)[1] == 1000
    for row in groups["pilot", "egreedy", 1000]:
        row["tail_trade"] = row["seed"] < 10
    assert analysis.analyze(groups, horizons)[1] is None
    for row in groups["pilot", "egreedy", 1000]:
        row["Q3"] = 0.2
    assert analysis.analyze(groups, horizons)[1] is None


@pytest.mark.parametrize("fail", [False, True])
def test_extended_report_and_sidecars(tmp_path, monkeypatch, fail):
    analysis = load("analyze_wp2")
    groups = fake_groups(analysis)
    if fail:
        for row in groups["pilot", "egreedy", 1000]:
            row["Q3"] = 0.2
    monkeypatch.setattr(analysis, "ROOT", tmp_path)
    monkeypatch.setattr(analysis, "combined_inputs", lambda *args, **kwargs: (
        groups, {"runs": 720, "trajectories_checked": 720}, {}))
    analysis.main(["--include-r1000"])
    out = tmp_path / "results/v1.1/wp2_eval_r1000"
    payload = json.loads((out / "wp2_eval.json").read_text())
    assert len(payload["groups"]) == 36
    assert payload["stop_and_ask"] == fail
    assert payload["recommended_n_rounds"] == (None if fail else 1000)
    for name in ("wp2_eval.json", "wp2_eval.md"):
        digest = hashlib.sha256((out / name).read_bytes()).hexdigest()
        assert (out / (name + ".sha256")).read_text() == f"{digest}  {name}\n"
    with pytest.raises(ValueError, match="fresh/empty"):
        analysis.main(["--include-r1000"])


def test_r1000_validator_rejects_smoke(tmp_path):
    analysis = load("analyze_wp2")
    (tmp_path / "run_meta.json").write_text(json.dumps({"official": False, "dry_run": False}))
    (tmp_path / "completion.json").write_text("{}")
    with pytest.raises(ValueError, match="not an official"):
        analysis.validate_inputs(tmp_path, (1000,))


def test_combined_validation_with_synthetic_r1000_files(tmp_path, monkeypatch):
    """Transform existing R500 records into test fixtures, never experimental results."""
    analysis = load("analyze_wp2")
    runner = load("run_wp2")
    fake = tmp_path / "repo"
    fake.mkdir()
    for name in ("docs", "scripts", "tokenmarket", "configs"):
        (fake / name).symlink_to(ROOT / name, target_is_directory=True)
    results = fake / "results/v1.1"
    results.mkdir(parents=True)
    for name in ("wp1", "wp2"):
        (results / name).symlink_to(ROOT / "results/v1.1" / name, target_is_directory=True)
    run = results / "wp2_r1000"
    (run / "trajectories").mkdir(parents=True)
    base = runner.load_config(str(ROOT / "configs/v1.0/scale.yaml"))
    rows = []
    for line in (ROOT / "results/v1.1/wp2/completed_runs.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["n_rounds"] != 500:
            continue
        old_id = row["wp2_run_id"]
        cell = runner.Cell(row["router"], "a0.1", 0.25, 1.0)
        cfg = runner.cell_config(base, cell, row["seed"], 1000, row["learner"])
        row.update(n_rounds=1000, n_tasks=10000, quarter_k=250, tail_rounds=250,
                   budget_multiplier=cfg["market"]["budget_multiplier"],
                   Q3_start=500, Q3_end=750, Q4_start=750, Q4_end=1000,
                   wp2_run_id=runner.run_id(cell, row["learner"], 1000, row["seed"]),
                   config_hash=hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest())
        trajectory = json.loads(
            (ROOT / "results/v1.1/wp2/trajectories" / f"{old_id}.json").read_text())
        trajectory.update(wp2_run_id=row["wp2_run_id"], n_rounds=1000,
                          q_round=trajectory["q_round"] * 2)
        for q in ("Q3", "Q4"):
            trajectory[q].update(start=row[f"{q}_start"], end=row[f"{q}_end"])
        runner.write_json(run / "trajectories" / f"{row['wp2_run_id']}.json", trajectory)
        rows.append(row)
    meta = json.loads((ROOT / "results/v1.1/wp2/run_meta.json").read_text())
    meta.update(n_rounds=[1000], n_run_groups=9, n_runs_planned=180)
    runner.write_json(run / "run_meta.json", meta)
    runner.write_json(run / "completion.json", {"n_runs_completed": 180})
    runner.write_json(run / "cells.json", runner.summarize(rows))
    runner.write_json(run / "manifest.json", [
        {"cell_id": c.cell_id, "learner": learner, "n_rounds": 1000}
        for c in runner.WP2_CELLS for learner in runner.WP2_LEARNERS])
    runner.write_csv(run / "per_seed.csv", rows)
    (run / "completed_runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    monkeypatch.setattr(analysis, "ROOT", fake)
    groups, checks, hashes = analysis.combined_inputs(results / "wp2", run)
    assert len(groups) == checks["groups"] == 36
    assert checks["runs"] == checks["trajectories_checked"] == 720
    assert checks["WP1_R48_shared_field_matches"] == 60
    assert len([p for p in hashes if "/trajectories/" in p]) == 720
    protocol = fake / "frozen-test.txt"
    protocol.write_text("Test fixture only; not a protocol freeze.\n")
    digest = hashlib.sha256(protocol.read_bytes()).hexdigest()
    custom = results / "custom_wp2"
    custom.mkdir()
    for p in (ROOT / "results/v1.1/wp2").iterdir():
        if p.name != "run_meta.json":
            (custom / p.name).symlink_to(p, target_is_directory=p.is_dir())
    custom_meta = json.loads((ROOT / "results/v1.1/wp2/run_meta.json").read_text())
    custom_meta["protocol_sha256"] = digest
    runner.write_json(custom / "run_meta.json", custom_meta)
    meta["protocol_sha256"] = digest
    (run / "run_meta.json").write_text(json.dumps(meta))
    validation = {"protocol": protocol, "protocol_sha256": digest, "wp1_run": results / "wp1"}
    assert analysis.combined_inputs(custom, run, **validation)[1]["runs"] == 720
    with pytest.raises(ValueError, match="run protocol mismatch"):
        analysis.combined_inputs(results / "wp2", run, **validation)
    # A duplicate summary must not conceal a missing group.
    summaries = json.loads((run / "cells.json").read_text())
    summaries[-1] = summaries[0]
    (run / "cells.json").write_text(json.dumps(summaries))
    with pytest.raises(ValueError, match="summary grid mismatch"):
        analysis.validate_inputs(run, (1000,), **validation)
