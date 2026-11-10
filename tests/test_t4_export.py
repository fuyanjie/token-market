"""T4 label-stripped export + leak checker (docs/PROTOCOL_v1.0.md §5) - mock only, fast."""
import csv
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import check_t4_leakage  # noqa: E402
from tokenmarket.benchmark_export import run_export_episode  # noqa: E402
from tokenmarket.config import deep_merge, load_config  # noqa: E402
from tokenmarket.t4_export import (KEY_COLUMNS, LABEL, WHITELIST, assert_public, blacklist_hits,  # noqa: E402
                                   default_train_seeds, export_t4, split_runs)

SEEDS = [0, 1, 2, 3, 4]


@pytest.fixture(scope="module")
def cfg():
    c = load_config(os.path.join(ROOT, "configs", "default.yaml"))
    return deep_merge(c, {"run": {"n_rounds": 48},
                          "fraud": {"strategy": "learning", "attack_modes_enabled": ["swap", "theft"]},
                          "market": {"budget_multiplier": 4.0}})


@pytest.fixture(scope="module")
def records(cfg):
    recs = []
    for s in SEEDS:
        for pol in ("audited_compliance_cascade", "single_best_compliant"):
            recs += run_export_episode(cfg, pol, s, n_tasks=96)[1]
    return recs


@pytest.fixture()
def export(tmp_path, records, cfg):
    return export_t4(records, str(tmp_path / "t4"), cfg)


def _read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        return list(rd.fieldnames), list(rd)


def _write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------- whitelist / blacklist
@pytest.mark.parametrize("col", ["tokens_actual", "actual_tokens", "reasoning_tokens", "token_inflation",
                                 "billed_minus_actual_mean", "tokens_actual_minus_billed", "hit", "miss",
                                 "audits_hit", "label_correct", "fraud_realized", "slash_amount", "delist_rounds",
                                 "learned_q_swap", "learned_q_theft", "attack_mode", "n_attacks",
                                 "active_attack_rate", "actual_model", "confidence_mean", "correct",
                                 "answer_length", "quality_score", "trust_quality", "swap_prob", "seller_id"])
def test_blacklist_rejected(col):
    assert blacklist_hits(col)
    with pytest.raises(ValueError):
        assert_public(list(KEY_COLUMNS) + ["latency_mean", col])


def test_whitelist_names_clean_and_unlisted_rejected():
    for c in WHITELIST:
        assert not blacklist_hits(c), c
    assert_public(list(KEY_COLUMNS) + list(WHITELIST))
    with pytest.raises(ValueError):   # innocuous-looking but not whitelisted
        assert_public(list(KEY_COLUMNS) + ["price_ratio"])


def test_whitelist_only_output(export, records):
    p = export["paths"]
    for split in ("train", "test"):
        header, rows = _read_csv(p[f"features_{split}"])
        assert header[:3] == list(KEY_COLUMNS)
        assert set(header) <= set(KEY_COLUMNS) | set(WHITELIST)
        assert LABEL not in header and "seller_id" not in header
        sids = {r["seller_id"] for r in records if r["seller_id"]}
        assert not any(v in sids for r in rows for v in r.values())   # raw seller ids never leak
        lh, lrows = _read_csv(p[f"labels_{split}"])
        assert LABEL in lh and not (set(lh) & set(WHITELIST))
        assert len(lrows) == len(rows)
    labels = _read_csv(p["labels_train"])[1] + _read_csv(p["labels_test"])[1]
    assert {r[LABEL] for r in labels} >= {"0", "1"}
    assert all(r[LABEL] in ("0", "") for r in labels if r["seller_id"] != "seller_sg")   # "" = no target trades
    assert all((r[LABEL] == "") == (r["n_target_served"] == "0") for r in labels)


# ---------------------------------------------------------------- split
def test_split_by_run_no_overlap(export, records):
    m = export["manifest"]
    assert m["train_seeds"] == [0, 1, 2, 3] and m["test_seeds"] == [4]   # round(0.7 * 5) = 4 train seeds
    assert not set(m["train_runs"]) & set(m["test_runs"])
    assert set(m["train_runs"]) | set(m["test_runs"]) == {r["run_id"] for r in records}
    tr = {r["run_id"] for r in _read_csv(export["paths"]["features_train"])[1]}
    te = {r["run_id"] for r in _read_csv(export["paths"]["features_test"])[1]}
    assert tr and te and not tr & te


def test_split_rules():
    assert default_train_seeds(range(20)) == set(range(14))
    assert default_train_seeds(range(30)) == set(range(21))
    runs = {f"pol{p}__seed{s}": s for s in range(6) for p in range(2)}
    tr, te = split_runs(runs, train_seeds=[0, 2, 4])
    assert {runs[r] for r in tr} == {0, 2, 4} and {runs[r] for r in te} == {1, 3, 5}
    tr, te = split_runs(runs, train_runs=["pol0__seed0"])
    assert tr == ["pol0__seed0"] and len(te) == 11 and "pol0__seed0" not in te
    with pytest.raises(ValueError):
        split_runs(runs, train_seeds=range(6))       # empty test side
    with pytest.raises(ValueError):
        split_runs(runs, train_runs=["nope"])


def test_target_window_rounds(records, cfg, tmp_path):
    res = export_t4(records, str(tmp_path / "w"), cfg, feature_rounds=32, target_rounds=16)
    m = res["manifest"]
    assert m["feature_rounds_1based"] == [1, 32] and m["target_rounds_1based"] == [33, 48]
    # target counts = served purchases of that seller in 0-based rounds 32..47
    lab = _read_csv(res["paths"]["labels_test"])[1][0]
    n = sum(1 for r in records if r["run_id"] == lab["run_id"] and r["seller_id"] == lab["seller_id"]
            and r["status"] == "allowed" and 32 <= r["round"] < 48)
    assert int(lab["n_target_served"]) == n


# ---------------------------------------------------------------- leak checker
def test_leak_checker_passes_clean_export(export):
    d = os.path.dirname(export["paths"]["manifest"])
    assert check_t4_leakage.main(["--dir", d]) == 0


def test_leak_checker_catches_injected_tokens_actual_column(export, tmp_path):
    p = export["paths"]
    fh, frows = _read_csv(p["features_train"])
    _, lrows = _read_csv(p["labels_train"])
    ref = {(r["run_id"], r["seller_key"]): float(r["leakref_tokens_actual_mean"]) for r in lrows}

    # (a) a new, unwhitelisted column derived from tokens_actual
    bad = [dict(r, tok_est=3.0 * ref[(r["run_id"], r["seller_key"])] + 1.0) for r in frows]
    fa = str(tmp_path / "fa.csv")
    _write_csv(fa, fh + ["tok_est"], bad)
    off, _ = check_t4_leakage.check([fa], [p["labels_train"]])
    assert any(o.startswith("tok_est: not on WHITELIST") for o in off)
    assert any("tok_est: |corr|" in o and "leakref_tokens_actual_mean" in o for o in off)

    # (b) leaky values smuggled under a WHITELISTED name: only the correlation test can catch it
    smug = [dict(r, billed_tokens_mean=2.0 * ref[(r["run_id"], r["seller_key"])] - 5.0) for r in frows]
    fb = str(tmp_path / "fb.csv")
    _write_csv(fb, fh, smug)
    off, _ = check_t4_leakage.check([fb], [p["labels_train"]])
    assert off and all(o.startswith("billed_tokens_mean: |corr|") for o in off)
    assert check_t4_leakage.main(["--features", fb, "--labels", p["labels_train"]]) == 1

    # (c) a blacklisted name fails even without labels
    fc = str(tmp_path / "fc.csv")
    _write_csv(fc, fh + ["tokens_actual"], [dict(r, tokens_actual=1) for r in frows])
    assert check_t4_leakage.main(["--features", fc]) == 1
