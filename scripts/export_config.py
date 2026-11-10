#!/usr/bin/env python3
"""Export benchmark knobs (a, π, L, reputation_rounds, adaptive_audit, escrow) to YAML."""
import argparse
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tokenmarket.benchmark_export import export_knobs  # noqa: E402
from tokenmarket.config import load_config  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(ROOT, "configs", "default.yaml"))
    ap.add_argument("--out", default=os.path.join(ROOT, "configs", "exported_benchmark.yaml"))
    args = ap.parse_args(argv)
    knobs = export_knobs(load_config(args.config))
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        yaml.safe_dump(knobs, fh, sort_keys=False, allow_unicode=True)
    print(args.out)
    print(yaml.safe_dump(knobs, sort_keys=False, allow_unicode=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
