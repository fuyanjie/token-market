#!/usr/bin/env python3
"""Build the fixed long-task subset data/long_tasks.jsonl from the raw GSM8K / MATH-500 test files.

  python scripts/build_long_tasks.py [--gsm8k data/raw/gsm8k_test.jsonl] [--math500 data/raw/math500_test.jsonl]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tokenmarket.tasks import build_long_subset  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gsm8k", default="data/raw/gsm8k_test.jsonl")
    ap.add_argument("--math500", default="data/raw/math500_test.jsonl")
    ap.add_argument("--out", default="data/long_tasks.jsonl")
    ap.add_argument("--n-gsm8k", type=int, default=28)
    ap.add_argument("--n-math", type=int, default=20)
    ap.add_argument("--seed", type=int, default=2024)
    a = ap.parse_args()
    rows = build_long_subset(a.gsm8k, a.math500, a.n_gsm8k, a.n_math, a.seed)
    with open(a.out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} items to {a.out}: "
          f"{sum(r['source'] == 'gsm8k' for r in rows)} gsm8k, {sum(r['source'] == 'math500' for r in rows)} math500")


if __name__ == "__main__":
    main()
