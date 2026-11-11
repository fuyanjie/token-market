"""Review checks; run with pytest -q -p no:cacheprovider on this file."""
import importlib.util
import itertools
import json
from pathlib import Path
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tokenmarket.v1_metrics import intent  # noqa: E402


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/v1.1/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analysis = load("analyze_wp2")
runner = load("run_wp2")
wp1 = load("analyze_wp1")


@pytest.mark.parametrize("n", [48, 200, 500])
def test_quarters_match_official_intent_on_uneven_modes_and_absences(n):
    rng = np.random.default_rng(13)
    modes = {"a": ["swap", "theft"], "b": ["swap"], "c": ["downgrade"],
             "d": ["swap"], "e": ["theft"]}
    m = {"strategic_modes": modes, "strategic_delisted_rounds":
         {sid: list(range(i, n, 7 + i)) for i, sid in enumerate(modes)}}
    for mode, field in runner._HIST.items():
        m[field] = {sid: rng.random(n if sid != "e" else n - 3).tolist()
                    for sid, enabled in modes.items() if mode in enabled}
    records = [{"status": "allowed", "seller_id": sid, "round": r}
               for r in range(n) for sid in modes if r % 3 == 0]
    windows, k = runner.quarter_bounds(n)
    for name, start, end in windows[2:]:
        # Truncate at the quarter end and ask official intent() for that final k.
        official = intent(m, [r for r in records if r["round"] < end], end,
                          tail_frac=k / end, tail_trade_rounds=k)
        segment = runner.intent_window(m, records, start, end)
        for field in ("Q", "Q_swap", "Q_theft", "Q_downgrade", "tail_trade",
                      "tail_sales", "Q_present_rounds"):
            assert segment[field] == official[field], (n, name, field)
        assert segment["delisted_rounds"] == official["delisted_rounds_tail"]


def test_bootstrap_independent_reference_and_determinism():
    d = np.linspace(-0.1, 0.2, 20)
    key = "reference"
    got = analysis.paired_bootstrap(d, key)
    import hashlib
    seed = int.from_bytes(hashlib.sha256(f"20261111:{key}".encode()).digest()[:8], "little")
    rng = np.random.default_rng(seed)
    # Independent sequential resampling, rather than the vectorized implementation.
    means = [float(np.mean([d[i] for i in rng.integers(20, size=20)])) for _ in range(10000)]
    lo, hi = np.percentile(means, [2.5, 97.5])
    assert got["lo"] == lo and got["hi"] == hi
    assert got == analysis.paired_bootstrap(d, key)
    assert analysis.paired_bootstrap([0] * 20, key) == {
        "mean": 0, "lo": 0, "hi": 0, "p_two_sided_descriptive": 1}
    assert analysis.inside_margin(-0.05, 0.05)
    assert not analysis.inside_margin(-0.051, 0.051)  # Contains zero, still fails.


@pytest.mark.parametrize("bad", [[0] * 19, [0] * 21, [0] * 19 + [float("nan")]])
def test_incomplete_or_nonfinite_pairs_rejected(bad):
    with pytest.raises(ValueError):
        analysis.paired_bootstrap(bad, "bad")


def fake_groups(delta=0.0):
    return {(router, learner, n):
            [{"seed": seed, "Q3": delta, "Q4": 0.0, "Q": 0.0, "E": 0.0,
              "tail_trade": seed < (0 if router == "cascade" else 20)}
             for seed in range(20)]
            for router, learner, n in itertools.product(
                analysis.ROUTERS, analysis.LEARNERS, analysis.HORIZONS)}


def test_smallest_horizon_and_cascade_exclusion():
    results, recommended, _ = analysis.analyze(fake_groups())
    assert recommended == 48
    assert all(not r["converged"] for r in results if r["router"] == "cascade")
    groups = fake_groups()
    for key, rows in groups.items():
        if key[0] == "pilot" and key[2] == 48:
            for r in rows:
                r["Q3"] = 0.2
    assert analysis.analyze(groups)[1] == 200


def test_strict_identifiability_and_no_recommendation():
    groups = fake_groups()
    for r in groups["pilot", "egreedy", 48]:
        r["tail_trade"] = r["seed"] < 10
    results, recommended, _ = analysis.analyze(groups)
    group = results[0]
    assert group["CI_inside_margin"] and not group["Q_identifiable"]
    assert recommended == 200
    _, recommended, exp3_ok = analysis.analyze(fake_groups(0.2))
    assert recommended is None and not exp3_ok


def test_wp1_all_contrasts_and_holm_independent_reference():
    p = json.loads((ROOT / "results/v1.1/wp1_eval/wp1_eval.json").read_text())
    rows = []
    for arm in ("factorial", "control"):
        rows += wp1.load_per_seed(ROOT / f"results/v1.1/wp1/{arm}/per_seed.csv")
    index = {(r["cell_id"], r["seed"]): r for r in rows}
    cells = {c["cell_id"]: c for c in p["cells"]}
    families = {}
    decision = []
    for c in p["contrasts"]:
        diffs = [index[c["cell_id"], s][c["metric"]] -
                 index[c["baseline_cell_id"], s][c["metric"]] for s in range(20)]
        rng = wp1.contrast_rng(f"delta:{c['cell_id']}:{c['metric']}")
        bm = np.asarray(diffs)[rng.integers(20, size=(10000, 20))].mean(axis=1)
        lo, hi = np.percentile(bm, [2.5, 97.5])
        assert (c["delta_mean"], c["delta_lo"], c["delta_hi"], c["p_raw"]) == (
            float(np.mean(diffs)), float(lo), float(hi),
            float(min(1, 2 * min(np.mean(bm <= 0), np.mean(bm >= 0)))))
        testable = c["metric"] == "E" or (
            cells[c["cell_id"]]["tail_trade_runs"] > 10 and
            cells[c["baseline_cell_id"]]["tail_trade_runs"] > 10)
        assert c["testable"] == testable
        if testable:
            families.setdefault((c["router"], c["pi"]), []).append(c)
            if c["router"] in ("pilot", "strongest") and c["pi"] == 1 and c["penalty"] == 0.25:
                decision.append(c)
        else:
            assert c["p_holm_report"] is None and not c["significant_report"]
    assert len(decision) == 28 and len(families) == 10
    for family, field in [(v, "p_holm_report") for v in families.values()] + [
            (decision, "p_holm_decision_a")]:
        ordered = sorted(family, key=lambda c: c["p_raw"])
        for i, c in enumerate(ordered):
            expected = min(1.0, max((len(ordered) - j) * ordered[j]["p_raw"]
                                    for j in range(i + 1)))
            assert c[field] == expected
