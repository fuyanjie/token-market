#!/usr/bin/env python3
"""WP0 reproduction gate: compare a re-run per_seed.csv against the reference per_seed.csv on (method, pi, seed).

  python scripts/v1.1/compare_repro.py --ref results/v1.0/main/per_seed.csv --new results/v1.1/wp0_repro/per_seed.csv \
      --seeds 0 1 2 --tol 1e-9 --out results/v1.1/wp0_repro
Numeric columns: |delta| <= tol; non-numeric columns: exact string equality. Read-only on --ref.
"""
import argparse
import csv
import json
import math
import os

KEY = ("method", "pi", "seed")


def load(path, seeds):
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    out = {}
    for r in rows:
        if int(r["seed"]) in seeds:
            k = (r["method"], float(r["pi"]), int(r["seed"]))
            assert k not in out, f"duplicate key {k} in {path}"
            out[k] = r
    return out, (list(rows[0].keys()) if rows else [])


def num(x):
    if x == "":
        return None
    if x in ("True", "False"):
        return float(x == "True")
    try:
        return float(x)
    except ValueError:
        return "str"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--seeds", nargs="+", type=int, required=True)
    ap.add_argument("--tol", type=float, default=1e-9)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ref, rcols = load(a.ref, set(a.seeds))
    new, ncols = load(a.new, set(a.seeds))
    only_ref, only_new = sorted(set(ref) - set(new)), sorted(set(new) - set(ref))
    common = sorted(set(ref) & set(new))
    cols = [c for c in rcols if c not in KEY]
    numeric, textual = [], []
    for c in cols:
        kinds = {type(num(ref[k][c])) for k in common} | {type(num(new[k][c])) for k in common}
        (textual if str in kinds else numeric).append(c)
    maxd = {c: 0.0 for c in numeric}
    mism = []
    for k in common:
        bad = {}
        for c in numeric:
            x, y = num(ref[k][c]), num(new[k][c])
            if x is None or y is None:
                d = 0.0 if x is None and y is None else math.inf
            elif math.isnan(x) or math.isnan(y):
                d = 0.0 if math.isnan(x) and math.isnan(y) else math.inf
            else:
                d = abs(x - y)
            maxd[c] = max(maxd[c], d)
            if d > a.tol:
                bad[c] = (ref[k][c], new[k][c])
        for c in textual:
            if ref[k][c] != new[k][c]:
                bad[c] = (ref[k][c], new[k][c])
        if bad:
            mism.append({"key": list(k), "diffs": bad})
    passed = not only_ref and not only_new and not mism and rcols == ncols
    res = {"ref": a.ref, "new": a.new, "seeds": a.seeds, "tol": a.tol, "passed": passed,
           "columns_identical": rcols == ncols, "n_rows_ref": len(ref), "n_rows_new": len(new),
           "n_rows_compared": len(common), "rows_only_in_ref": [list(k) for k in only_ref],
           "rows_only_in_new": [list(k) for k in only_new], "numeric_columns": numeric,
           "text_columns_exact": textual, "max_abs_delta": maxd,
           "max_abs_delta_overall": max(maxd.values()) if maxd else 0.0, "mismatching_rows": mism}
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "compare.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    L = ["# WP0 reproduction gate: v1.1 re-run vs v1.0 main (seeds " + " ".join(map(str, a.seeds)) + ")", "",
         f"- reference: `{a.ref}`", f"- re-run: `{a.new}`", f"- match key: (method, pi, seed); tolerance |Δ| ≤ {a.tol:g}",
         f"- **result: {'PASS' if passed else 'FAIL'}**", f"- rows: ref {len(ref)}, new {len(new)}, compared {len(common)}; "
         f"only in ref {len(only_ref)}, only in new {len(only_new)}", f"- column lists identical: {rcols == ncols}",
         f"- max |Δ| over all numeric columns: {res['max_abs_delta_overall']:.3g}",
         f"- mismatching rows: {len(mism)}", "", f"## Numeric columns ({len(numeric)}): max |Δ|", "",
         "| column | max abs Δ |", "|---|---|"]
    L += [f"| {c} | {maxd[c]:.3g} |" for c in numeric]
    L += ["", f"## Text columns compared by exact equality ({len(textual)})", "", ", ".join(textual), ""]
    if mism:
        L += ["## Mismatching rows (first 50)", ""]
        L += [f"- {m['key']}: {m['diffs']}" for m in mism[:50]]
    with open(os.path.join(a.out, "compare.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print("PASS" if passed else "FAIL", res["n_rows_compared"], res["max_abs_delta_overall"], len(mism))


if __name__ == "__main__":
    main()
