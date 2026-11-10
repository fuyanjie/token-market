"""Smoke tests for v1 five-layer benchmark export + CLI knobs."""
import json
import os
import sys

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tokenmarket.benchmark_export import (  # noqa: E402
    AUDIT_FIELDS, BUYER_FIELDS, EPISODE_FIELDS, LABEL_FIELDS, LAYER_FILES, ORDER_FIELDS,
    ORDER_LABEL_FIELDS, SELLER_FIELDS, SELLER_LABEL_FIELDS, export_benchmark, export_knobs,
)
from tokenmarket.config import load_config  # noqa: E402


@pytest.fixture(scope="module")
def cfg():
    return load_config(os.path.join(ROOT, "configs", "default.yaml"))


def test_export_knobs_keys(cfg):
    k = export_knobs(cfg)
    for key in ("a", "pi", "L", "reputation_rounds", "adaptive_audit", "escrow"):
        assert key in k
    assert k["adaptive_audit"] is False
    assert k["escrow"] is False
    assert int(k["reputation_rounds"]) == 0


def test_five_layer_export(tmp_path, cfg):
    out = tmp_path / "exp"
    res = export_benchmark(cfg, str(out), policy="audited_compliance_cascade", seed=0,
                           n_tasks=24, knobs_path=str(tmp_path / "knobs.yaml"))
    for key, fname in LAYER_FILES.items():
        path = out / fname
        assert path.exists(), fname
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) >= 1, fname
        row = json.loads(lines[0])
        if key == "sellers":
            for f in SELLER_FIELDS:
                assert f in row
        elif key == "buyers":
            for f in BUYER_FIELDS:
                assert f in row
        elif key == "orders":
            for f in ORDER_FIELDS:
                assert f in row
            assert row["state"] in ("locked", "delivered", "audited", "settled", "slashed",
                                    "blocked", "unfilled")
        elif key == "audits":
            for f in AUDIT_FIELDS:
                assert f in row
            assert row["sampled"] in (0, 1)
        elif key == "episodes":
            for f in EPISODE_FIELDS:
                assert f in row
            assert "active_attack_rate" in row and "fraud_share" in row
    assert res["n_orders"] >= 1
    knobs = yaml.safe_load((tmp_path / "knobs.yaml").read_text(encoding="utf-8"))
    assert "a" in knobs and "pi" in knobs and "L" in knobs


def test_export_script_help():
    import scripts.export_benchmark_layers as m  # noqa: F401 — path via ROOT
    # argparse smoke: module importable; CLI exercised via export_benchmark above
    assert os.path.exists(os.path.join(ROOT, "scripts", "export_benchmark_layers.py"))
    assert os.path.exists(os.path.join(ROOT, "scripts", "run_leaderboard.py"))
    assert os.path.exists(os.path.join(ROOT, "scripts", "run_benchmark_tasks.py"))
    assert os.path.exists(os.path.join(ROOT, "docs", "DATA_SCHEMA.md"))


def test_leaderboard_argparse_smoke():
    import argparse
    # ensure script defines --smoke
    src = open(os.path.join(ROOT, "scripts", "run_leaderboard.py"), encoding="utf-8").read()
    assert "--smoke" in src and "active_attack_rate" in src and "NOT the primary" in src


def test_optional_labels_export(tmp_path, cfg):
    out = tmp_path / "lab"
    res = export_benchmark(cfg, str(out), seed=0, n_tasks=16, with_labels=True)
    assert res["labels_path"]
    path = out / "labels.jsonl"
    assert path.exists()
    rows = [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(rows) == res["n_orders"]
    for f in LABEL_FIELDS:
        assert f in rows[0]
    sellers = [json.loads(ln) for ln in (out / "sellers.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
    for f in SELLER_LABEL_FIELDS:
        assert f in sellers[0]
    orders = [json.loads(ln) for ln in (out / "orders.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
    for f in ORDER_LABEL_FIELDS:
        assert f in orders[0]


def test_default_export_skips_labels_file(tmp_path, cfg):
    out = tmp_path / "nolab"
    res = export_benchmark(cfg, str(out), seed=0, n_tasks=12, with_labels=False)
    assert res.get("labels_path") is None
    assert not (out / "labels.jsonl").exists()
