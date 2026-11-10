# Collect guide — expanding the benchmark dataset without breaking T1–T3

**One page.** Goal: grow coverage (more seeds / knob settings) while keeping the **same protocol** as the v0.1 production board.

## Do / 要做
1. **Keep the five-layer schema** (`sellers`, `buyers`, `orders`, `audits`, `episodes`; optional `labels`). See `docs/DATA_SCHEMA.md`.
2. **Keep join keys:** `run_id`, `seed`, `order_id`, `config_hash`.
3. **Primary board metrics stay** `active_attack_rate` + `fraud_share`. Put `learned_q_*` / `J` in side columns only.
4. **Vary only advertised knobs**, and write them into the export dir:
   - seeds (e.g. extend beyond `{0,1,2}`)
   - `pi` grid points for T2-style sweeps
   - `a` (audit rate) for T1-style fixed-audit cells
   - keep `adaptive_audit` / `escrow` / `reputation_rounds` **OFF** unless you intentionally open a *new* appendix track (legacy F/J break otherwise)
5. **Export into a new dated dir**, never overwrite `exports/production/` or `release/v0.1/`:
   ```bash
   python scripts/export_benchmark_layers.py --use-cache --with-labels \
     --seeds 3 4 5 --out exports/collect_seeds345/
   python scripts/run_benchmark_tasks.py --use-cache \
     --seeds 3 4 5 --out results/benchmark/collect_seeds345/
   ```
6. **Record `config_hash` + knobs.yaml** next to every collect run so leaderboards can filter apples-to-apples.

## Don’t / 不要
- Don’t mix smoke (`exports/latest`) into the primary board.
- Don’t change field names or move labels into feature tables.
- Don’t treat `learned_q_*` as the ranking metric.
- Don’t enable adaptive audit / escrow / reputation in the same directory as the frozen production board.

## Feature / Label hygiene / 特征与标签卫生
| Layer | Use as features? | Use as labels? |
|---|---|---|
| `sellers` / `buyers` / `orders` / `audits` / `episodes` | Yes (protocol features) | Episode metrics are *evaluation*, not training targets for detectors |
| `labels.jsonl` | **No** for training-time features | Yes — held-out supervision (fraud detection, compliance intercept). Join after split; never leak into T1–T3 ranking features |

Downstream detectors must train on feature tables only and evaluate against `labels.jsonl` with a documented split. T1–T3 leaderboard rows come from `episodes` / task episode files, not from detector scores.

## Protocol lock (T1–T3)
- **T1:** fixed audit rate, report attack/fraud (primary).
- **T2:** sweep reveal probability π; report π\* regime (production: **(0.10, 0.12)** for J crossover note); primary board still attack/fraud.
- **T3:** equal-budget adaptive audit — **appendix / cost**, not primary leaderboard.

Changing task definitions or primary metrics requires a new release tag, not a silent overwrite of v0.1.
