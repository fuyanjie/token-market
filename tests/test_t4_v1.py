"""v1.0 T4 additions: exact 7-item whitelist, --drop-latency, per-attack-type labels, numpy baselines/metrics,
rule baseline, and scripts/run_t4_eval.py end to end."""
import csv
import os
import random
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from tokenmarket.t4_export import (BLACKLIST_EXACT, LATENCY_COLUMNS, PROTOCOL_ITEMS, TYPE_LABELS, WHITELIST,  # noqa
                                   blacklist_hits, export_t4, whitelist_columns)
from tokenmarket.t4_models import GBDT, Encoder, LogisticRegression, auroc, average_precision, precision_at_k, \
    rule_scores  # noqa: E402


def test_whitelist_is_exactly_the_seven_protocol_items():
    assert set(PROTOCOL_ITEMS) == {"listed_quality", "quoted price", "declared model", "latency distribution",
                                   "billed tokens", "compliance label", "historical trade volume"}
    assert {v[0] for v in WHITELIST.values()} == set(PROTOCOL_ITEMS)


def test_confidence_actual_model_downgrade_blacklisted():
    for c in ("confidence", "actual_model", "downgrade_prob", "attack_mode", "learned_q_downgrade"):
        assert blacklist_hits(c), c
    assert {"confidence", "actual_model"} <= BLACKLIST_EXACT
    for c in WHITELIST:
        assert not blacklist_hits(c)


def test_drop_latency_removes_only_latency():
    full, nolat = whitelist_columns(), whitelist_columns(drop_latency=True)
    assert set(full) - set(nolat) == set(LATENCY_COLUMNS) and LATENCY_COLUMNS
    assert {WHITELIST[c][0] for c in nolat} == set(PROTOCOL_ITEMS) - {"latency distribution"}


def _records(n_runs=4, n_sellers=6, rounds=48, seed=0):
    """Synthetic logs: seller k attacks with mode MODES[k % 3] when k >= 3 (strategic), cheaper price and longer
    latency for swap sellers; honest sellers never attack."""
    rng = random.Random(seed)
    modes = ["swap", "theft", "downgrade"]
    recs = []
    for run in range(n_runs):
        rid = f"posted_price__x__seed{run}"
        for rnd in range(rounds):
            for k in range(n_sellers):
                strat = k >= 3
                m = modes[k % 3] if strat and rng.random() < 0.6 else "none"
                lat = 300 + (200 if m == "swap" else 0) + rng.gauss(0, 20)
                billed = 150 if m == "theft" else int(rng.gauss(140, 10))
                recs.append({"run_id": rid, "seed": run, "round": rnd, "seller_id": f"s{k}", "buyer_id": "b",
                             "status": "allowed", "price_per_1k": 0.15 if strat else 0.2,
                             "claimed_model": "M", "seller_jurisdiction": "SG", "cross_border": False,
                             "violation": False, "latency_ms": lat, "billed_tokens": billed,
                             "actual_tokens": 40 if m == "theft" else billed, "attack_mode": m})
    return recs


def test_export_drop_latency_and_type_labels(tmp_path):
    res = export_t4(_records(), str(tmp_path / "full"))
    res6 = export_t4(_records(), str(tmp_path / "nolat"), drop_latency=True)
    cols, cols6 = res["manifest"]["feature_columns"], res6["manifest"]["feature_columns"]
    assert set(cols) - set(cols6) == {c for c in LATENCY_COLUMNS if c in cols}
    assert res6["manifest"]["drop_latency"] is True
    labs = list(csv.DictReader(open(tmp_path / "full" / "labels_train.csv")))
    for lab in TYPE_LABELS.values():
        assert lab in labs[0]
    s4 = [r for r in labs if r["seller_id"] == "s4"]          # theft seller
    assert all(r[TYPE_LABELS["theft"]] == "1" and r[TYPE_LABELS["swap"]] == "0" for r in s4)
    s0 = [r for r in labs if r["seller_id"] == "s0"]
    assert all(r["fraud_future"] == "0" for r in s0)


def test_metrics_known_values():
    y, s = [0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]
    assert auroc(y, s) == pytest.approx(0.75)
    assert average_precision(y, s) == pytest.approx((1 / 1 + 2 / 3) / 2)
    assert precision_at_k(y, s, 2) == 0.5
    assert auroc([1, 1], [0.1, 0.2]) is None and average_precision([0, 0], [1, 2]) is None
    assert auroc([0, 1], [0.5, 0.5]) == 0.5                   # ties -> average rank


def test_logreg_and_gbdt_fit_separable():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(200, 3))
    y = (X[:, 0] + 0.5 * X[:, 1] > 0).astype(float)
    for m in (LogisticRegression(), GBDT(n_estimators=30)):
        assert auroc(y, m.fit(X, y).predict(X)) > 0.95
    Xnl = rng.normal(size=(300, 2))
    ynl = ((Xnl[:, 0] > 0) ^ (Xnl[:, 1] > 0)).astype(float)    # XOR: trees win, linear fails
    assert auroc(ynl, GBDT(n_estimators=50).fit(Xnl, ynl).predict(Xnl)) > 0.9


def test_encoder_categorical_and_impute():
    rows = [{"a": "1", "declared_model": "M"}, {"a": "", "declared_model": "N"}, {"a": "3", "declared_model": "M"}]
    enc = Encoder(["a", "declared_model"]).fit(rows)
    X = enc.transform(rows + [{"a": "2", "declared_model": "Z"}])
    assert X.shape == (4, 3) and X[3, 1:].sum() == 0 and X[1, 0] == pytest.approx(0.0)


def test_rule_scores_low_price_high_billed():
    rows = [{"run_id": "r", "declared_model": "M", "quoted_price_mean": p, "billed_tokens_mean": b}
            for p, b in [(0.2, 140), (0.2, 141), (0.15, 150), (0.21, 139)]]
    s = rule_scores(rows)
    assert int(np.argmax(s)) == 2
    assert np.all(rule_scores(rows[:1]) == 0)                 # singleton peer group -> 0


def test_run_t4_eval_end_to_end(tmp_path):
    import json
    import run_t4_eval
    logs = tmp_path / "logs.jsonl"
    with open(logs, "w") as fh:
        for r in _records(n_runs=6, n_sellers=9):
            fh.write(json.dumps(r) + "\n")
    run_t4_eval.main(["--logs", str(logs), "--out", str(tmp_path / "ev"), "--n-boot", "50"])
    res = json.load(open(tmp_path / "ev" / "t4_eval.json"))
    types = {r["attack_type"] for r in res["results"]}
    assert {"swap", "theft", "downgrade", "any"} <= types
    assert {r["model"] for r in res["results"]} == {"logreg", "gbdt", "rule"}
    for r in res["results"]:
        assert {"full7", "nolat6", "diff_full_minus_nolat", "diff_ci_lo", "diff_ci_hi"} <= set(r)
        if r["model"] == "rule":
            assert r["diff_full_minus_nolat"] == 0
    assert not set(res["latency_columns"]) & set(res["feature_columns"]["nolat6"])
    # swap sellers are identified by latency in this synthetic data: dropping latency must hurt logreg AUROC
    sw = [r for r in res["results"] if r["attack_type"] == "swap" and r["model"] == "logreg" and r["metric"] == "auroc"]
    assert sw[0]["full7"] >= sw[0]["nolat6"]
    run_t4_eval.main(["--export-dir", str(tmp_path / "ev" / "export"), "--out", str(tmp_path / "ev6"),
                      "--drop-latency", "--n-boot", "10"])
    res6 = json.load(open(tmp_path / "ev6" / "t4_eval.json"))
    assert list(res6["feature_columns"]) == ["nolat6"]


def test_official_is_mean_of_per_run_not_pooled():
    """Official AUROC is the mean of per-run scores; pooled-over-sellers is stored separately and may differ."""
    import run_t4_eval
    from tokenmarket.t4_models import auroc
    # two test runs, one easy (AUROC 1) and one hard (AUROC 0) with different sizes so the pool != the mean
    y = [1, 0, 0,  1, 0]
    s = [1, 0, 0,  0, 1]
    runs = ["r1", "r1", "r1", "r2", "r2"]
    per = run_t4_eval.per_run_scores(y, s, runs, "auroc")
    assert per["r1"] == 1.0 and per["r2"] == 0.0
    assert run_t4_eval._mean(per.values()) == 0.5
    assert auroc(y, s) != 0.5
