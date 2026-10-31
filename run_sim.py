#!/usr/bin/env python3
"""Entry point.

  python run_sim.py --config configs/default.yaml               # precompute (if needed) + market simulation
  python run_sim.py --config configs/default.yaml --precompute-only
  python run_sim.py --config configs/default.yaml --backend-override mock   # all sellers mock: no torch needed
"""
import argparse
import sys

import yaml

from tokenmarket.sim import run_all


def main(argv=None):
    ap = argparse.ArgumentParser(description="token-market v2 sandbox simulation")
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--seeds", type=int, nargs="+", default=None)
    ap.add_argument("--backend-override", "--backend", dest="backend_override",
                    choices=["mock", "local_hf", "real"], default=None,
                    help="force every seller onto this backend (default: per-seller `backend` in config)")
    ap.add_argument("--precompute-only", action="store_true",
                    help="only run local models over the task pool and fill the output cache")
    ap.add_argument("--n-tasks", type=int, default=None)
    ap.add_argument("--results-dir", default=None)
    ap.add_argument("--cache-file", default=None)
    ap.add_argument("--auction-format", choices=["second_price", "first_price"], default=None)
    args = ap.parse_args(argv)

    with open(args.config, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if args.auction_format:
        cfg["market"]["auction"]["format"] = args.auction_format
    summary = run_all(cfg, seeds=args.seeds, backend_name=args.backend_override, n_tasks=args.n_tasks,
                      results_dir=args.results_dir, cache_path=args.cache_file,
                      precompute_only=args.precompute_only)
    if args.precompute_only:
        print(f"precompute done in {summary['precompute_s']}s: {summary['precompute']}")
        return 0
    print(f"precompute {summary['precompute_s']}s, market sim {summary['market_sim_s']}s: wrote "
          f"{summary['log_lines']} transaction lines to {summary['log_file']} (total {summary['elapsed_s']}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
