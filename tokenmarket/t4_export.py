"""v1.0 T4 (seller risk ranking / fraud detection) export: label-stripped features + separate labels.

Unit of prediction = one (run, seller). Features use ONLY the seller's public, audit-free behaviour in the
feature window (rounds 1..feature_rounds, i.e. 0-based `round` < feature_rounds); the label is whether the seller
realised any attack on a served purchase in the target window (rounds feature_rounds+1 .. feature_rounds+
target_rounds). See docs/PROTOCOL_v1.0.md §5.

Input = raw transaction records (tokenmarket.logging_schema rows: TransactionLogger JSONL / _MemLog.records),
which carry latency / compliance fields that the five-layer orders.jsonl does not.

Outputs (under out_dir):
  features_train.csv, features_test.csv   KEY_COLUMNS + whitelisted feature columns ONLY
  labels_train.csv,   labels_test.csv     keys + label + private leak-check reference columns (never features)
  t4_manifest.json                        split, windows, whitelist / blacklist / excluded lists

Split is BY RUN: every run is either train or test (default: by seed, protocol seeds 0-13 train / 14-19 test,
otherwise round(70%) of the sorted seeds train). Train and test use the same windows; for test runs only the
target-window label is scored.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import statistics
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

# Join keys, not features. seller_key is a per-run pseudonym (sha256(run_id|seller_id)): the seller roster is
# fixed across seeds, so the raw seller_id would let a model memorise "seller_sg = fraud" across runs.
KEY_COLUMNS = ("run_id", "seed", "seller_key")

# Whitelisted feature column -> (protocol §5 item, source log field(s), aggregation)
WHITELIST: Dict[str, Tuple[str, str, str]] = {
    "quoted_price_mean": ("quoted price", "price_per_1k", "mean over purchase attempts (allowed+blocked)"),
    "quoted_price_std": ("quoted price", "price_per_1k", "population std over purchase attempts"),
    "declared_model": ("declared model", "claimed_model", "categorical (constant per seller)"),
    "listed_quality_mean": ("listed_quality", "cfg.models[claimed_model].accuracy",
                            "mean listed accuracy over difficulties (public listing; needs cfg)"),
    "latency_mean": ("latency distribution", "latency_ms", "mean over served purchases"),
    "latency_std": ("latency distribution", "latency_ms", "population std over served purchases"),
    "latency_p50": ("latency distribution", "latency_ms", "median over served purchases"),
    "latency_p90": ("latency distribution", "latency_ms", "90th percentile (nearest-rank) over served"),
    "billed_tokens_mean": ("billed tokens", "billed_tokens", "mean over served purchases"),
    "billed_tokens_std": ("billed tokens", "billed_tokens", "population std over served purchases"),
    "billed_tokens_sum": ("billed tokens", "billed_tokens", "sum over served purchases"),
    "seller_jurisdiction": ("compliance label", "seller_jurisdiction", "categorical (constant per seller)"),
    "cross_border_share": ("compliance label", "cross_border", "share of purchase attempts"),
    "blocked_share": ("compliance label", "status == 'blocked'", "share of purchase attempts"),
    "violation_share": ("compliance label", "violation", "share of served purchases"),
    "n_attempts": ("historical trade volume", "rows with this seller_id", "count (allowed+blocked)"),
    "n_served": ("historical trade volume", "status == 'allowed'", "count"),
    "n_buyers": ("historical trade volume", "buyer_id on served purchases", "distinct count"),
    "served_share_of_run": ("historical trade volume", "status == 'allowed'",
                            "n_served / all served purchases in the run's feature window"),
}
CATEGORICAL = ("declared_model", "seller_jurisdiction")
# Protocol §5 (frozen 2026-11-10): the whitelist is EXACTLY these 7 public items.
PROTOCOL_ITEMS = ("listed_quality", "quoted price", "declared model", "latency distribution", "billed tokens",
                  "compliance label", "historical trade volume")
assert {v[0] for v in WHITELIST.values()} == set(PROTOCOL_ITEMS)
LATENCY_COLUMNS = tuple(c for c, v in WHITELIST.items() if v[0] == "latency distribution")


def whitelist_columns(drop_latency: bool = False) -> List[str]:
    """Whitelisted feature columns; drop_latency=True gives the 6-item no-latency ablation (protocol §5)."""
    return [c for c in WHITELIST if not (drop_latency and c in LATENCY_COLUMNS)]

# Not leaky by definition but leaky in the CURRENT simulator; must not be exported until protocol §5b lands.
EXCLUDED_PENDING_SIMULATOR_CHANGE: Dict[str, str] = {
    "answer_length": "v4 theft truncates the real cached output character-proportionally (backends.Backend."
                     "truncate), so answer length tracks tokens_actual and leaks theft. Re-admit only VISIBLE "
                     "answer length once hidden reasoning and visible answer are logged separately (§5b), and only "
                     "after re-running scripts/check_t4_leakage.py.",
    "quality_score": "TrustModel.quality uses audit outcomes (audit-revealed true model) and `correct` uses gold. "
                     "A reference-free quality score may be added only if it uses neither gold nor true model "
                     "identity, with the algorithm documented.",
}

# Exact source/derived names that must never appear as feature columns.
BLACKLIST_EXACT: Set[str] = {
    "tokens_actual", "actual_tokens", "reasoning_tokens", "token_inflation",
    "tokens_actual_minus_billed", "billed_minus_actual", "tokens_billed_minus_actual",
    "hit", "miss", "label_correct", "fraud_realized", "slash_amount", "delist_rounds",
    "actual_model", "confidence", "correct", "final_correct", "answer", "final_answer", "gold",
    "swap_prob", "theft_prob", "audited", "audit_cost", "audit_type", "swap_detected", "theft_detected",
    "escrow_held", "escrow_released", "escrow_slashed", "ban_until", "banned_until_round",
    "stake_remaining", "seller_profit", "buyer_surplus", "seller_id", "downgrade_prob",
    "answer_length", "answer_len", "quality_score",
}
# Substring / token patterns (case-insensitive) for derived columns.
BLACKLIST_PATTERNS: Tuple[str, ...] = (
    r"tokens?_actual", r"actual_tokens?", r"reasoning_tokens?", r"token_inflation", r"billed_minus_actual",
    r"actual_minus_billed", r"token_gap",
    r"attack", r"learned_q", r"latent_q", r"fraud", r"slash", r"delist", r"(^|_)ban", r"escrow",
    r"audit", r"detected", r"(^|_)(hit|miss)(_|$)", r"label",
    r"actual_model", r"confidence", r"correct", r"answer", r"gold", r"swap_prob", r"theft_prob",
    r"profit", r"surplus", r"^quality", r"quality_score", r"trust", r"q_hat",
    r"downgrade",   # v1.0: selective-downgrade fields (downgrade_prob, ...)
)
_BL_RE = [re.compile(p, re.IGNORECASE) for p in BLACKLIST_PATTERNS]

LABEL = "fraud_future"
# v1.0 per-attack-type labels (protocol §5: AUROC / AP per attack type): 1 if the seller realised that attack on a
# served purchase in the target window, 0 if it served without it, empty if it served nothing there.
ATTACK_TYPE_MODES = {"swap": ("swap", "both"), "theft": ("theft", "both", "downgrade+theft"),
                     "downgrade": ("downgrade", "downgrade+theft")}
TYPE_LABELS = {k: f"{LABEL}_{k}" for k in ATTACK_TYPE_MODES}
LEAKREF_COLUMNS = ("leakref_tokens_actual_mean", "leakref_billed_minus_actual_mean")
LABEL_COLUMNS = ("run_id", "seed", "seller_key", "seller_id", LABEL) + tuple(TYPE_LABELS.values()) + \
    ("n_target_served", "fraud_order_share_target", "fraud_billed_token_share_target") + LEAKREF_COLUMNS


def blacklist_hits(col: str) -> List[str]:
    """Blacklist rules matched by a column name (empty = clean). Applied to whitelisted names too."""
    hits = [f"exact:{col}"] if col in BLACKLIST_EXACT else []
    return hits + [f"pattern:{r.pattern}" for r in _BL_RE if r.search(col)]


def check_feature_columns(cols: Iterable[str]) -> List[str]:
    """Problems with a feature header: non-key columns must be whitelisted and not blacklisted."""
    errs = []
    for c in cols:
        if c in KEY_COLUMNS:
            continue
        if c not in WHITELIST:
            errs.append(f"{c}: not on WHITELIST")
        bl = blacklist_hits(c)
        if bl:
            errs.append(f"{c}: BLACKLIST {bl}")
    return errs


def assert_public(cols: Iterable[str]) -> None:
    errs = check_feature_columns(cols)
    if errs:
        raise ValueError("T4 feature columns violate whitelist/blacklist: " + "; ".join(errs))


# --------------------------------------------------------------------------- split
def default_train_seeds(seeds: Sequence[int]) -> Set[int]:
    """Protocol §5: seeds 0-13 train / 14-19 test for 20 seeds; otherwise round(70%) of sorted seeds (≥1 test)."""
    s = sorted(set(int(x) for x in seeds))
    if len(s) < 2:
        raise ValueError(f"need ≥2 seeds for a by-run split, got {s}")
    n_train = min(len(s) - 1, max(1, int(math.floor(0.7 * len(s) + 0.5))))
    return set(s[:n_train])


def split_runs(run_seeds: Dict[str, int], train_seeds: Optional[Iterable[int]] = None,
               train_runs: Optional[Iterable[str]] = None) -> Tuple[List[str], List[str]]:
    """Return (train_run_ids, test_run_ids). train_runs (explicit run ids) wins over train_seeds; with neither,
    default_train_seeds. Every run lands in exactly one split."""
    if train_runs is not None:
        tr = set(train_runs)
        unknown = tr - set(run_seeds)
        if unknown:
            raise ValueError(f"train_runs not in logs: {sorted(unknown)}")
    else:
        ts = set(int(s) for s in train_seeds) if train_seeds is not None else default_train_seeds(run_seeds.values())
        tr = {r for r, s in run_seeds.items() if s in ts}
    train = sorted(tr)
    test = sorted(set(run_seeds) - tr)
    assert not set(train) & set(test)
    if not train or not test:
        raise ValueError(f"split must be non-empty on both sides (train={train}, test={test})")
    return train, test


# --------------------------------------------------------------------------- features / labels
def seller_key(run_id: str, seller_id: str) -> str:
    return hashlib.sha256(f"{run_id}|{seller_id}".encode("utf-8")).hexdigest()[:12]


def _pstd(xs: List[float]) -> Optional[float]:
    return statistics.pstdev(xs) if xs else None


def _mean(xs: List[float]) -> Optional[float]:
    return statistics.fmean(xs) if xs else None


def _pctl(xs: List[float], q: float) -> Optional[float]:
    if not xs:
        return None
    s = sorted(xs)
    return s[max(0, min(len(s) - 1, int(math.ceil(q * len(s))) - 1))]


def _listed_quality_mean(cfg: Optional[Dict], model: Optional[str]) -> Optional[float]:
    if not cfg or not model:
        return None
    acc = cfg.get("models", {}).get(model, {}).get("accuracy", {})
    return statistics.fmean(float(v) for v in acc.values()) if acc else None


def _is_attack(r: Dict) -> bool:
    return (r.get("attack_mode") or "none") != "none"


def build_unit_rows(records: Sequence[Dict], cfg: Optional[Dict] = None, feature_rounds: int = 32,
                    target_rounds: int = 16) -> Tuple[List[Dict], List[Dict]]:
    """(features, labels), one row each per (run, seller) that made ≥1 purchase attempt in the feature window.
    Features read ONLY whitelisted source fields of feature-window rows; labels read the target window."""
    lo_t, hi_t = feature_rounds, feature_rounds + target_rounds
    by_unit: Dict[Tuple[str, str], Dict[str, List[Dict]]] = {}
    run_seed: Dict[str, int] = {}
    run_served_feat: Dict[str, int] = {}
    for r in records:
        sid, rnd = r.get("seller_id"), int(r["round"])
        run_seed[r["run_id"]] = int(r["seed"])
        if sid is None:   # unfilled line
            continue
        u = by_unit.setdefault((r["run_id"], sid), {"feat": [], "target": []})
        if rnd < feature_rounds:
            u["feat"].append(r)
            if r["status"] == "allowed":
                run_served_feat[r["run_id"]] = run_served_feat.get(r["run_id"], 0) + 1
        elif lo_t <= rnd < hi_t:
            u["target"].append(r)
    feats, labels = [], []
    for (run_id, sid), u in sorted(by_unit.items()):
        fr = u["feat"]
        if not fr:
            continue
        served = [r for r in fr if r["status"] == "allowed"]
        price = [float(r["price_per_1k"]) for r in fr]
        lat = [float(r["latency_ms"]) for r in served]
        billed = [float(r["billed_tokens"]) for r in served]
        key = seller_key(run_id, sid)
        claimed = fr[0].get("claimed_model")
        row = {
            "run_id": run_id, "seed": run_seed[run_id], "seller_key": key,
            "quoted_price_mean": _mean(price), "quoted_price_std": _pstd(price),
            "declared_model": claimed,
            "latency_mean": _mean(lat), "latency_std": _pstd(lat),
            "latency_p50": _pctl(lat, 0.5), "latency_p90": _pctl(lat, 0.9),
            "billed_tokens_mean": _mean(billed), "billed_tokens_std": _pstd(billed),
            "billed_tokens_sum": float(sum(billed)),
            "seller_jurisdiction": fr[0].get("seller_jurisdiction"),
            "cross_border_share": _mean([1.0 if r.get("cross_border") else 0.0 for r in fr]),
            "blocked_share": _mean([1.0 if r["status"] == "blocked" else 0.0 for r in fr]),
            "violation_share": _mean([1.0 if r.get("violation") else 0.0 for r in served]),
            "n_attempts": len(fr), "n_served": len(served),
            "n_buyers": len({r["buyer_id"] for r in served}),
            "served_share_of_run": len(served) / run_served_feat[run_id] if run_served_feat.get(run_id) else 0.0,
        }
        if cfg is not None:
            row["listed_quality_mean"] = _listed_quality_mean(cfg, claimed)
        feats.append(row)
        tgt = [r for r in u["target"] if r["status"] == "allowed"]
        tb = sum(float(r["billed_tokens"]) for r in tgt)
        act = [float(r["actual_tokens"]) for r in served]
        labels.append({
            "run_id": run_id, "seed": run_seed[run_id], "seller_key": key, "seller_id": sid,
            LABEL: (1 if any(_is_attack(r) for r in tgt) else 0) if tgt else None,
            **{lab: (1 if any(r.get("attack_mode") in ATTACK_TYPE_MODES[k] for r in tgt) else 0) if tgt else None
               for k, lab in TYPE_LABELS.items()},
            "n_target_served": len(tgt),
            "fraud_order_share_target": _mean([1.0 if _is_attack(r) else 0.0 for r in tgt]),
            "fraud_billed_token_share_target":
                sum(float(r["billed_tokens"]) for r in tgt if _is_attack(r)) / tb if tb else None,
            # private references for the leak checker (feature window, same rows as the features)
            "leakref_tokens_actual_mean": _mean(act),
            "leakref_billed_minus_actual_mean": _mean([b - a for b, a in zip(billed, act)]),
        })
    return feats, labels


def feature_columns(rows: Sequence[Dict], drop_latency: bool = False) -> List[str]:
    present = set().union(*(r.keys() for r in rows)) if rows else set()
    return list(KEY_COLUMNS) + [c for c in whitelist_columns(drop_latency) if c in present]


def _write_csv(path: str, rows: Sequence[Dict], cols: Sequence[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            w.writerow(["" if r.get(c) is None else r[c] for c in cols])


def export_t4(records: Sequence[Dict], out_dir: str, cfg: Optional[Dict] = None,
              train_seeds: Optional[Iterable[int]] = None, train_runs: Optional[Iterable[str]] = None,
              feature_rounds: int = 32, target_rounds: int = 16, drop_latency: bool = False) -> Dict:
    feats, labels = build_unit_rows(records, cfg, feature_rounds, target_rounds)
    run_seeds = {r["run_id"]: int(r["seed"]) for r in records}
    train, test = split_runs(run_seeds, train_seeds, train_runs)
    cols = feature_columns(feats, drop_latency)
    assert_public(cols)
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for name, runs in (("train", set(train)), ("test", set(test))):
        f = [r for r in feats if r["run_id"] in runs]
        lab = [r for r in labels if r["run_id"] in runs]
        paths[f"features_{name}"] = os.path.join(out_dir, f"features_{name}.csv")
        paths[f"labels_{name}"] = os.path.join(out_dir, f"labels_{name}.csv")
        _write_csv(paths[f"features_{name}"], f, cols)
        _write_csv(paths[f"labels_{name}"], lab, LABEL_COLUMNS)
    manifest = {
        "task": "T4 seller risk ranking (docs/PROTOCOL_v1.0.md §5)",
        "unit": "(run_id, seller_key)", "label": LABEL,
        "label_definition": "1 if the seller realised any attack (attack_mode != none) on a served purchase in the "
                            "target window, 0 if it served without attacking, empty if it served nothing there",
        "feature_rounds_1based": [1, feature_rounds], "target_rounds_1based": [feature_rounds + 1,
                                                                                 feature_rounds + target_rounds],
        "log_round_index": "0-based: features use round < feature_rounds",
        "train_runs": train, "test_runs": test,
        "train_seeds": sorted({run_seeds[r] for r in train}), "test_seeds": sorted({run_seeds[r] for r in test}),
        "feature_columns": cols, "whitelist": {k: list(v) for k, v in WHITELIST.items()},
        "protocol_items": list(PROTOCOL_ITEMS), "drop_latency": bool(drop_latency),
        "type_labels": TYPE_LABELS,
        "excluded_pending_simulator_change": EXCLUDED_PENDING_SIMULATOR_CHANGE,
        "blacklist_exact": sorted(BLACKLIST_EXACT), "blacklist_patterns": list(BLACKLIST_PATTERNS),
        "n_units": {"train": sum(r["run_id"] in set(train) for r in feats),
                    "test": sum(r["run_id"] in set(test) for r in feats)},
    }
    paths["manifest"] = os.path.join(out_dir, "t4_manifest.json")
    with open(paths["manifest"], "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    return {"paths": paths, "manifest": manifest}


def read_records(paths: Sequence[str]) -> List[Dict]:
    out = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            out.extend(json.loads(line) for line in fh if line.strip())
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="T4 label-stripped export from raw transaction logs")
    ap.add_argument("--logs", nargs="+", required=True, help="raw transaction JSONL (logging_schema rows)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--config", default=None, help="config for listed_quality (omitted if not given)")
    ap.add_argument("--train-seeds", type=int, nargs="+", default=None)
    ap.add_argument("--train-runs", nargs="+", default=None)
    ap.add_argument("--feature-rounds", type=int, default=32)
    ap.add_argument("--target-rounds", type=int, default=16)
    ap.add_argument("--drop-latency", action="store_true", help="omit latency columns (6-item ablation, §5)")
    args = ap.parse_args(argv)
    cfg = None
    if args.config:
        from .config import load_config
        cfg = load_config(args.config)
    res = export_t4(read_records(args.logs), args.out, cfg, args.train_seeds, args.train_runs,
                    args.feature_rounds, args.target_rounds, args.drop_latency)
    print(json.dumps({"paths": res["paths"], "n_units": res["manifest"]["n_units"],
                      "train_seeds": res["manifest"]["train_seeds"], "test_seeds": res["manifest"]["test_seeds"]},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
