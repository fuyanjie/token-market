#!/usr/bin/env python3
"""T5 leakage check aligned with scripts/check_t4_leakage.py and docs/PROTOCOL_T5.md §2, §5.

Exit 1 if ANY check fails:
  1. Any non-key feature column is not on tokenmarket.t5_export.WHITELIST or matches the §2 blacklist.
  2. Required KEY_COLUMNS are missing, or any feature column overlaps label columns outside KEY_COLUMNS.
  3. Any test seed (14..19) appears in training feature/label rows.
  4. Any frozen hold-out prompt hash appears in training labels (checked against t5_manifest.json).
  5. Any round == 0 row has non-zero / non-empty historical features (temporal causality violation).
  6. Any numeric non-constant feature has |Pearson corr| > --threshold (default 0.95) with
     leakref_tokens_actual, leakref_billed_minus_actual, leakref_latency_ms, or y_correct_clean.

Protocol §8 stop rule: if this check fails, STOP and do not run official scoring.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tokenmarket.t5_export import (  # noqa: E402
    KEY_COLUMNS,
    LABEL,
    LEAKREF_COLUMNS,
    TEST_SEEDS,
    check_feature_columns,
)


def _read(paths: Sequence[str]) -> Tuple[List[str], List[Dict]]:
    header, rows = None, []
    for p in paths:
        with open(p, encoding="utf-8", newline="") as fh:
            rd = csv.DictReader(fh)
            if header is None:
                header = list(rd.fieldnames or [])
            elif list(rd.fieldnames or []) != header:
                raise SystemExit(f"header mismatch in {p}")
            rows.extend(rd)
    return header or [], rows


def _num(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        x = float(v)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def pearson(xs: Sequence[Optional[float]], ys: Sequence[Optional[float]]) -> Optional[float]:
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 3:
        return None
    n = len(pairs)
    mx = sum(p[0] for p in pairs) / n
    my = sum(p[1] for p in pairs) / n
    sxx = sum((p[0] - mx) ** 2 for p in pairs)
    syy = sum((p[1] - my) ** 2 for p in pairs)
    if sxx <= 1e-12 * max(1.0, mx * mx) * n or syy <= 1e-12 * max(1.0, my * my) * n:
        return None
    return sum((p[0] - mx) * (p[1] - my) for p in pairs) / math.sqrt(sxx * syy)


def check(
    feature_paths: Sequence[str],
    label_paths: Optional[Sequence[str]] = None,
    manifest_path: Optional[str] = None,
    threshold: float = 0.95,
    test_seeds: Sequence[int] = TEST_SEEDS,
) -> Tuple[List[str], List[str], Dict]:
    """Return (offenders, notes, diagnostics). Empty offenders == PASS."""
    header, frows = _read(feature_paths)
    offenders = list(check_feature_columns(header, allow_keys=True))
    for k in KEY_COLUMNS:
        if k not in header:
            offenders.append(f"missing key column {k}")

    notes: List[str] = []
    diag: Dict = {"n_feature_rows": len(frows), "max_abs_corr": {}, "correlations": {}}

    # Split isolation: test seeds must not appear in training features.
    test_seed_set = {int(s) for s in test_seeds}
    bad_seeds = sorted({int(r["seed"]) for r in frows if r.get("seed") not in (None, "") and int(r["seed"]) in test_seed_set})
    if bad_seeds:
        offenders.append(f"test seeds present in training features: {bad_seeds}")

    if not label_paths:
        notes.append("no labels given: correlation, causality, and holdout checks skipped")
        return offenders, notes, diag

    lheader, lrows = _read(label_paths)
    for c in [c for c in header if c in lheader and c not in KEY_COLUMNS]:
        offenders.append(f"{c}: also present in labels file")

    bad_lseeds = sorted({int(r["seed"]) for r in lrows if r.get("seed") not in (None, "") and int(r["seed"]) in test_seed_set})
    if bad_lseeds:
        offenders.append(f"test seeds present in training labels: {bad_lseeds}")

    # Hold-out prompt exclusion check (Protocol §5).
    if manifest_path and os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)
        holdout = set(manifest.get("holdout_prompt_hashes") or [])
        if holdout:
            leaked_prompts = sorted({r.get("prompt_sha256") for r in lrows if r.get("prompt_sha256") in holdout})
            if leaked_prompts:
                offenders.append(f"{len(leaked_prompts)} holdout prompt_sha256 leaked into training labels")

    lab = {(r["run_id"], r["task_id"], r["seller_key"]): r for r in lrows}
    joined = [(f, lab.get((f.get("run_id"), f.get("task_id"), f.get("seller_key")))) for f in frows]
    missing = sum(1 for _, lr in joined if lr is None)
    if missing:
        offenders.append(f"{missing} feature rows have no matching labels row")

    # Temporal causality check at round 0: pre-decision history must be empty.
    r0_bad = 0
    for f, lr in joined:
        if lr is not None and lr.get("round") not in (None, "") and int(lr["round"]) == 0:
            n_h = _num(f.get("hist_n_served"))
            bt_h = f.get("hist_billed_tokens_mean")
            sh_h = _num(f.get("hist_served_share"))
            if (n_h is not None and n_h != 0.0) or (bt_h not in (None, "")) or (sh_h is not None and sh_h != 0.0):
                r0_bad += 1
    if r0_bad:
        offenders.append(f"{r0_bad} round-0 rows have non-empty pre-decision history")

    # Correlation checks against private leakrefs and label.
    refs = {
        c: [_num(lr.get(c)) if lr else None for _, lr in joined]
        for c in LEAKREF_COLUMNS + (LABEL,)
    }
    for c in header:
        if c in KEY_COLUMNS:
            continue
        xs = [_num(f.get(c)) for f, _ in joined]
        if all(x is None for x in xs):
            continue
        diag["correlations"][c] = {}
        max_r = 0.0
        for ref, ys in refs.items():
            r = pearson(xs, ys)
            if r is not None:
                diag["correlations"][c][ref] = round(r, 6)
                max_r = max(max_r, abs(r))
                if abs(r) > threshold:
                    offenders.append(f"{c}: |corr| = {abs(r):.4f} > {threshold} with {ref}")
        diag["max_abs_corr"][c] = round(max_r, 6)

    return offenders, notes, diag


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="T5 feature leakage check (docs/PROTOCOL_T5.md §2)")
    ap.add_argument("--dir", default=None, help="export dir with features_train.csv / labels_train.csv / t5_manifest.json")
    ap.add_argument("--features", nargs="+", default=None)
    ap.add_argument("--labels", nargs="+", default=None)
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--threshold", type=float, default=0.95)
    ap.add_argument("--json-out", default=None, help="optional path to write JSON diagnostics")
    args = ap.parse_args(argv)

    feats = list(args.features or [])
    labels = list(args.labels or [])
    manifest = args.manifest
    if args.dir:
        f_tr = os.path.join(args.dir, "features_train.csv")
        l_tr = os.path.join(args.dir, "labels_train.csv")
        m_tr = os.path.join(args.dir, "t5_manifest.json")
        if os.path.exists(f_tr):
            feats.append(f_tr)
        if os.path.exists(l_tr):
            labels.append(l_tr)
        if manifest is None and os.path.exists(m_tr):
            manifest = m_tr
    if not feats:
        ap.error("no feature files (use --dir or --features)")

    offenders, notes, diag = check(feats, labels, manifest, args.threshold)
    payload = {
        "passed": len(offenders) == 0,
        "threshold": args.threshold,
        "feature_files": feats,
        "label_files": labels,
        "manifest": manifest,
        "offenders": offenders,
        "notes": notes,
        "diagnostics": diag,
    }
    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1)
    for n in notes:
        print(f"note: {n}")
    if offenders:
        print(f"T5 LEAK CHECK FAILED ({len(offenders)} offenders):")
        for o in offenders:
            print(f"  - {o}")
        return 1
    print(f"T5 leak check passed: {len(feats)} feature file(s), {diag['n_feature_rows']} rows, threshold {args.threshold}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
