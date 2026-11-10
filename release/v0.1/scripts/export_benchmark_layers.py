#!/usr/bin/env python3
"""One-click export of the five v1 publishable JSONL layers.

  /workspace/tmvenv/bin/python scripts/export_benchmark_layers.py
  /workspace/tmvenv/bin/python scripts/export_benchmark_layers.py --out exports/demo --seed 0 --n-tasks 48
  /workspace/tmvenv/bin/python scripts/export_benchmark_layers.py --full --use-cache

Writes: sellers.jsonl buyers.jsonl orders.jsonl audits.jsonl episodes.jsonl
Also dumps knobs (a, π, L, reputation_rounds, ...) to configs/exported_benchmark.yaml by default.
With --full: seeds {0,1,2}, n_tasks=480, n_rounds=48 → exports/production/ (does not clobber exports/latest smoke).
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tokenmarket.benchmark_export import (  # noqa: E402
    LAYER_FILES, export_benchmark, export_knobs, run_export_episode, write_jsonl, write_layers,
)
from tokenmarket.config import deep_merge, load_config  # noqa: E402


def _merge_layers(acc, layers):
    for k, rows in layers.items():
        acc.setdefault(k, []).extend(rows)
    return acc


def main(argv=None):
    ap = argparse.ArgumentParser(description="Export five-layer benchmark JSONL")
    ap.add_argument("--config", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--policy", default="audited_compliance_cascade")
    ap.add_argument("--seed", type=int, default=None, help="single seed (default 0; ignored if --seeds/--full)")
    ap.add_argument("--seeds", type=int, nargs="+", default=None)
    ap.add_argument("--n-tasks", type=int, default=None)
    ap.add_argument("--export-config", default=os.path.join(ROOT, "configs", "exported_benchmark.yaml"))
    ap.add_argument("--learning", action="store_true",
                    help="use learning fraud strategy (default: keep config; smoke uses static)")
    ap.add_argument("--with-labels", action="store_true",
                    help="also write optional labels.jsonl (held-out supervision; default five tables unchanged)")
    ap.add_argument("--full", action="store_true",
                    help="production scale → exports/production/; seeds 0,1,2; n_tasks=480; learning on")
    ap.add_argument("--use-cache", action="store_true",
                    help="use per-seller backends + llm cache (align closer to pi_dense/v6)")
    args = ap.parse_args(argv)

    if args.full:
        cfg_path = args.config or os.path.join(ROOT, "configs", "benchmark", "production.yaml")
        out = args.out or os.path.join(ROOT, "exports", "production")
        seeds = args.seeds or [0, 1, 2]
        n_tasks = args.n_tasks or 480
        learning = True
    else:
        cfg_path = args.config or os.path.join(ROOT, "configs", "default.yaml")
        out = args.out or os.path.join(ROOT, "exports", "latest")
        seeds = args.seeds or ([args.seed] if args.seed is not None else [0])
        n_tasks = args.n_tasks if args.n_tasks is not None else 48
        learning = args.learning

    cfg = load_config(cfg_path)
    over = {"fraud": {"strategy": "learning"}} if learning else {}
    over = deep_merge({
        "market": {"audited": {"adaptive_audit": False, "escrow": False,
                               "reputation_rounds": int(cfg.get("market", {}).get("audited", {}).get("reputation_rounds", 0))},
                   "budget_multiplier": float(cfg.get("market", {}).get("budget_multiplier", 2.0 if args.full else
                                                                          cfg.get("market", {}).get("budget_multiplier", 1.0)))},
    }, over)
    if args.full:
        over = deep_merge(over, {"fraud": {"strategy": "learning", "attack_modes_enabled": ["swap", "theft"]},
                                 "market": {"budget_multiplier": 2.0,
                                            "feedback": {"mode": "immediate", "delay_L": 0, "reveal_prob": 1.0}}})
    cfg = deep_merge(cfg, over)

    if args.use_cache:
        # patch run_export_episode path: build layers via prepare+cache
        from tokenmarket.sim import prepare, build_backends, run_single
        from tokenmarket.sellers import Reputation
        from tokenmarket.benchmark_export import (
            build_sellers_rows, build_buyers_rows, build_orders_rows, build_audits_rows,
            build_episode_row, config_hash, _MemLog, build_labels_rows,
        )

        def log(*a):
            print(*a, flush=True)

        pool, cache, stats, _ = prepare(cfg, None, cfg["run"].get("cache_file"), None, log)
        sb = {s.get("backend", "mock") for s in cfg["sellers"]}
        backends = build_backends(cfg, sb, cache)
        acc = {}
        episodes = []
        last_metrics = None
        for seed in seeds:
            chash = config_hash(cfg)
            lg = _MemLog()
            rep = Reputation(cfg["models"], stats if isinstance(stats, dict) else {})
            metrics = run_single(cfg, "posted_price", args.policy, seed, backends, rep, lg, pool, n_tasks, None)
            run_id = f"posted_price__{args.policy}__seed{seed}"
            layers = {
                "sellers": build_sellers_rows(cfg, metrics, run_id, seed),
                "buyers": build_buyers_rows(cfg, lg.records, args.policy, run_id, seed),
                "orders": build_orders_rows(lg.records, args.policy, chash),
                "audits": build_audits_rows(lg.records, metrics, cfg, args.policy),
                "episodes": [build_episode_row(metrics, cfg, run_id, seed, chash, records=lg.records)],
            }
            _merge_layers(acc, layers)
            episodes.append(layers["episodes"][0])
            last_metrics = metrics
            print(json.dumps({"seed": seed, "episode": layers["episodes"][0]}, default=str), flush=True)
        paths = write_layers(out, acc)
        labels_path = None
        if args.with_labels:
            labels = build_labels_rows(acc["sellers"], acc["orders"])
            labels_path = os.path.join(out, "labels.jsonl")
            write_jsonl(labels_path, labels)
            paths["labels"] = labels_path
        knobs = export_knobs(cfg)
        with open(args.export_config, "w", encoding="utf-8") as fh:
            import yaml
            yaml.safe_dump(knobs, fh, sort_keys=False, allow_unicode=True)
        res = {
            "out_dir": out, "paths": paths, "n_orders": len(acc["orders"]),
            "n_audits": len(acc["audits"]), "n_sellers": len(acc["sellers"]),
            "n_buyers": len(acc["buyers"]), "episodes": episodes,
            "episode": episodes[0] if episodes else None,
            "knobs_path": args.export_config, "labels_path": labels_path,
            "seeds": seeds, "n_tasks": n_tasks, "full": True, "use_cache": True,
        }
        print(json.dumps({k: res[k] for k in res if k != "episodes"}, indent=2, default=str))
        print(json.dumps({"episodes": episodes}, indent=2, default=str))
        return 0

    # single-seed path (smoke / default) — keep original behaviour for seed=0
    if len(seeds) == 1:
        res = export_benchmark(cfg, out, policy=args.policy, seed=seeds[0],
                               n_tasks=n_tasks, knobs_path=args.export_config,
                               with_labels=args.with_labels)
        print(json.dumps({k: res[k] for k in ("out_dir", "paths", "n_orders", "n_audits",
                                              "n_sellers", "n_buyers", "episode", "knobs_path", "labels_path")},
                         indent=2, default=str))
        return 0

    # multi-seed mock path
    acc = {}
    episodes = []
    for seed in seeds:
        metrics, records, layers = run_export_episode(cfg, args.policy, seed, n_tasks=n_tasks)
        _merge_layers(acc, layers)
        episodes.append(layers["episodes"][0])
        print(json.dumps({"seed": seed, "episode": layers["episodes"][0]}, default=str), flush=True)
    paths = write_layers(out, acc)
    labels_path = None
    if args.with_labels:
        from tokenmarket.benchmark_export import build_labels_rows
        labels = build_labels_rows(acc["sellers"], acc["orders"])
        labels_path = os.path.join(out, "labels.jsonl")
        write_jsonl(labels_path, labels)
        paths["labels"] = labels_path
    knobs = export_knobs(cfg)
    with open(args.export_config, "w", encoding="utf-8") as fh:
        import yaml
        yaml.safe_dump(knobs, fh, sort_keys=False, allow_unicode=True)
    res = {
        "out_dir": out, "paths": paths, "n_orders": len(acc["orders"]),
        "n_audits": len(acc["audits"]), "n_sellers": len(acc["sellers"]),
        "n_buyers": len(acc["buyers"]), "episodes": episodes,
        "episode": episodes[0] if episodes else None,
        "knobs_path": args.export_config, "labels_path": labels_path,
        "seeds": seeds, "n_tasks": n_tasks, "full": bool(args.full),
    }
    print(json.dumps({k: res[k] for k in res if k != "episodes"}, indent=2, default=str))
    print(json.dumps({"episodes": episodes}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
