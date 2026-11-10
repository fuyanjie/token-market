#!/usr/bin/env python3
"""Heuristic leak check for the T4 export (docs/PROTOCOL_v1.0.md §5). Exit 1 if any feature column

  * is not on tokenmarket.t4_export.WHITELIST (key columns run_id / seed / seller_key excepted),
  * matches the blacklist (exact names or patterns), or
  * has |Pearson corr| > --threshold (default 0.95) with tokens_actual (feature-window mean, and the
    billed − actual gap) or with the label, computed over all rows of the given files.

Correlations need the labels file(s): they carry the label and the private leakref_* columns, joined on
(run_id, seller_key). Categorical / constant columns are skipped for the correlation test.

  /workspace/tmvenv/bin/python scripts/check_t4_leakage.py --dir exports/t4
  /workspace/tmvenv/bin/python scripts/check_t4_leakage.py --features f_train.csv f_test.csv --labels l_train.csv l_test.csv
"""
import argparse
import csv
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tokenmarket.t4_export import KEY_COLUMNS, LABEL, LEAKREF_COLUMNS, check_feature_columns  # noqa: E402


def _read(paths):
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


def _num(v):
    if v is None or v == "":
        return None
    try:
        x = float(v)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def pearson(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 3:
        return None
    n = len(pairs)
    mx = sum(p[0] for p in pairs) / n
    my = sum(p[1] for p in pairs) / n
    sxx = sum((p[0] - mx) ** 2 for p in pairs)
    syy = sum((p[1] - my) ** 2 for p in pairs)
    if sxx <= 1e-12 * max(1.0, mx * mx) * n or syy <= 1e-12 * max(1.0, my * my) * n:
        return None   # constant column
    return sum((p[0] - mx) * (p[1] - my) for p in pairs) / math.sqrt(sxx * syy)


def check(feature_paths, label_paths=None, threshold=0.95):
    """Return (offenders, notes). offenders: list of human-readable problems (empty = pass)."""
    header, frows = _read(feature_paths)
    offenders = list(check_feature_columns(header))
    for k in KEY_COLUMNS:
        if k not in header:
            offenders.append(f"missing key column {k}")
    notes = []
    if not label_paths:
        notes.append("no labels given: correlation checks against tokens_actual / label skipped")
        return offenders, notes
    lheader, lrows = _read(label_paths)
    for c in [c for c in header if c in lheader and c not in KEY_COLUMNS]:
        offenders.append(f"{c}: also present in labels file")
    lab = {(r["run_id"], r["seller_key"]): r for r in lrows}
    joined = [(f, lab.get((f.get("run_id"), f.get("seller_key")))) for f in frows]
    missing = sum(1 for _, lr in joined if lr is None)
    if missing:
        notes.append(f"{missing} feature rows have no labels row")
    refs = {c: [_num(lr.get(c)) if lr else None for _, lr in joined] for c in LEAKREF_COLUMNS + (LABEL,)}
    for c in header:
        if c in KEY_COLUMNS:
            continue
        xs = [_num(f.get(c)) for f, _ in joined]
        if all(x is None for x in xs):
            continue   # categorical / empty
        for ref, ys in refs.items():
            r = pearson(xs, ys)
            if r is not None and abs(r) > threshold:
                offenders.append(f"{c}: |corr| = {abs(r):.4f} > {threshold} with {ref}")
    return offenders, notes


def main(argv=None):
    ap = argparse.ArgumentParser(description="T4 feature leak check")
    ap.add_argument("--dir", default=None, help="export dir with features_*.csv / labels_*.csv")
    ap.add_argument("--features", nargs="+", default=None)
    ap.add_argument("--labels", nargs="+", default=None)
    ap.add_argument("--threshold", type=float, default=0.95)
    args = ap.parse_args(argv)
    feats, labels = args.features or [], args.labels or []
    if args.dir:
        feats += [os.path.join(args.dir, f"features_{s}.csv") for s in ("train", "test")
                  if os.path.exists(os.path.join(args.dir, f"features_{s}.csv"))]
        labels += [os.path.join(args.dir, f"labels_{s}.csv") for s in ("train", "test")
                   if os.path.exists(os.path.join(args.dir, f"labels_{s}.csv"))]
    if not feats:
        ap.error("no feature files (use --dir or --features)")
    offenders, notes = check(feats, labels, args.threshold)
    for n in notes:
        print(f"note: {n}")
    if offenders:
        print(f"T4 LEAK CHECK FAILED ({len(offenders)} offenders):")
        for o in offenders:
            print(f"  - {o}")
        return 1
    print(f"T4 leak check passed: {len(feats)} feature file(s), threshold {args.threshold}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
