# Release v0.1 — Cross-Border Reasoning Token Markets (Benchmark)

**EN** / **中文**

## What this is / 这是什么
Camera-ready **Datasets & Benchmarks** production board for the Cross-Border Reasoning Token Markets simulator.
Not a CLOB; not a live exchange scrape. This is a **reproducible generator export** (five JSONL layers + T1–T3 task boards).

本包是跨境推理 token 交易模拟器的可发布 benchmark 板，不是真实交易所爬取，也不是 CLOB。

## Primary metrics / 主榜指标
- **Primary:** `active_attack_rate` + `fraud_share`
- **Side columns (not primary):** `learned_q_swap`, `learned_q_theft`, `J`
- `active_attack_rate` ≠ epoch-mean learned q (especially under delist / adaptive knobs)

主榜只看攻击率与 `fraud_share`；`learned_q_*` / `J` 旁列。

## Board vs smoke / 主榜 vs 冒烟
| Path | Role |
|---|---|
| `exports/production/` | **Board** — production five-layer JSONL (+ optional `labels.jsonl`) |
| `results/benchmark/production/` | **Board** — T1 / T2 / T3 episodes, `T2_crossover.json`, `tasks_summary.json` |
| `exports/latest/` (repo root, **not shipped**) | Smoke only — **NOT** the board |

`exports/latest` 仅冒烟样例，**不是**主榜。请只用本包 `exports/production` + `results/benchmark/production`。

## Headline production numbers (frozen) / 冻结数字
From `results/benchmark/production/tasks_summary.json` (do not reinvent):

- T1 summary: `active_attack_rate` ≈ 0.1011, `fraud_share` ≈ 0.1011, `J` ≈ 0.7661
- T2 π\* (J crossover, appendix note): **π\* ∈ (0.10, 0.12)** — primary board remains attack/fraud
- Default knobs keep `adaptive_audit=false`, `reputation_rounds=0`, `escrow=false` so legacy F/J stay reproducible

## Tests / 测试
- `pytest` **76 passed** (project tree at freeze time)

## Layout / 目录
```
release/v0.1/
  exports/production/     # sellers, buyers, orders, audits, episodes, labels, knobs
  results/benchmark/production/  # T1/T2/T3 + crossover + tasks_summary
  docs/DATA_SCHEMA.md
  docs/COLLECT_GUIDE.md
  configs/benchmark/production.yaml
  scripts/                # copies of export / tasks / leaderboard entrypoints
  MANIFEST.json
  SHA256SUMS
  RELEASE_NOTES.md
  REPRODUCE.md
  DONE.flag
```

## One-click reproduce / 一键复现
See `REPRODUCE.md`. From repo root (`/workspace/token-market`):

```bash
python scripts/export_benchmark_layers.py --full --use-cache --with-labels
python scripts/run_benchmark_tasks.py --full --use-cache
python scripts/run_leaderboard.py --smoke   # optional sanity; production board already frozen above
```

Verify integrity:

```bash
cd release/v0.1 && sha256sum -c SHA256SUMS
```

## Non-goals / 刻意不做
- Multi-buyer congestion (paper limitation)
- CLOB matching
- Changing production numbers or inventing new primary metrics
