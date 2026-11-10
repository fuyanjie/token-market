"""--per-seed-out for experiment F (pi_dense / T2): per-seed table written, default outputs byte-identical."""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import run_experiments  # noqa: E402
from tokenmarket.experiments import PER_SEED_F_COLS, per_seed_F_rows  # noqa: E402

D3 = "audited_compliance_cascade"
TINY = f"""extends: {os.path.join(ROOT, "configs", "pi_dense.yaml")}
run:
  n_tasks: 24
  n_rounds: 4
experiments:
  seeds: [0, 1]
  F:
    policies: [pilot_compliant, {D3}]
    reveal_probs: [1.0, 0.1]
    delays: [0]
    combined: []
"""


def _run(tmp_path, name, extra):
    cfg = tmp_path / "tiny_F.yaml"
    cfg.write_text(TINY, encoding="utf-8")
    rd = tmp_path / name
    assert run_experiments.main(["--config", str(cfg), "--only", "F", "--seeds", "0", "1",
                                 "--backend-override", "mock", "--results-dir", str(rd)] + extra) == 0
    return rd


def _strip_timing(text):
    return "\n".join(ln for ln in text.splitlines() if not ln.startswith("_total experiment time"))


def test_per_seed_out_writes_table_and_keeps_defaults(tmp_path):
    base = _run(tmp_path, "plain", [])
    out = tmp_path / "tables" / "F_per_seed"
    flagged = _run(tmp_path, "flagged", ["--per-seed-out", f"{out}.csv"])   # suffix dropped -> .md + .csv

    # default outputs unchanged (summary differs only in its wall-clock line)
    assert sorted(os.listdir(base)) == sorted(os.listdir(flagged))
    for name in ("feedback_ablation.json", "feedback_ablation.md"):
        assert (base / name).read_bytes() == (flagged / name).read_bytes(), name
    assert _strip_timing((base / "experiments_summary.md").read_text(encoding="utf-8")) == \
        _strip_timing((flagged / "experiments_summary.md").read_text(encoding="utf-8"))
    assert not (base / "F_per_seed.csv").exists()

    with open(f"{out}.csv", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert tuple(rows[0]) == PER_SEED_F_COLS
    assert len(rows) == 2 * 2 * 2           # policies x pi x seeds
    assert {r["seed"] for r in rows} == {"0", "1"} and {float(r["pi"]) for r in rows} == {1.0, 0.1}
    for r in rows:
        twin = next(x for x in rows if x["method"] == D3 and x["seed"] == r["seed"] and x["pi"] == r["pi"])
        assert abs(float(r["dJ_vs_D3"]) - (float(twin["J"]) - float(r["J"]))) < 1e-12
        if r["method"] == D3:
            assert float(r["dJ_vs_D3"]) == 0.0
    md = open(f"{out}.md", encoding="utf-8").read()
    assert md.count("\n| ") == len(rows) + 1  # header + one line per row

    # per-seed means reproduce the aggregate rows in feedback_ablation.json
    import json
    agg = json.loads((flagged / "feedback_ablation.json").read_text(encoding="utf-8"))["rows"]
    for a in agg:
        js = [float(r["J"]) for r in rows if r["method"] == a["policy"] and float(r["pi"]) == a["reveal_prob"]]
        assert abs(sum(js) / len(js) - a["joint_objective"]) < 1e-12


def test_per_seed_rows_missing_d3_is_none():
    rows = [{"seed": 0, "sweep": "delay", "delay_L": 0, "pi": 1.0, "method": "pilot_compliant", "J": 0.5,
             "fraud_share": 0.1, "learned_q_swap": 0.2, "learned_q_theft": 0.3}]
    assert per_seed_F_rows(rows)[0]["dJ_vs_D3"] is None
