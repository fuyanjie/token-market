#!/usr/bin/env python3
"""Entry point: python run_sim.py --config configs/default.yaml [--seeds 0 1 2] [--backend mock|local_hf] [--n-tasks N]"""
import argparse
import sys

import yaml

from tokenmarket.sim import run_all


def main(argv=None):
    ap = argparse.ArgumentParser(description="token-market v1 sandbox simulation")
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--seeds", type=int, nargs="+", default=None)
    ap.add_argument("--backend", choices=["mock", "local_hf", "real"], default=None)
    ap.add_argument("--n-tasks", type=int, default=None)
    ap.add_argument("--results-dir", default=None)
    ap.add_argument("--auction-format", choices=["second_price", "first_price"], default=None)
    args = ap.parse_args(argv)

    with open(args.config, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if args.auction_format:
        cfg["market"]["auction"]["format"] = args.auction_format
    summary = run_all(cfg, seeds=args.seeds, backend_name=args.backend, n_tasks=args.n_tasks,
                      results_dir=args.results_dir)
    print(f"wrote {summary['log_lines']} transactions to {summary['log_file']} in {summary['elapsed_s']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
