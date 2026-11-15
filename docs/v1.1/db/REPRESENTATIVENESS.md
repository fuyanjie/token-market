# Coverage and external evidence — documentation version 1 (2026-11-15)

This matrix preserves the paper's target scenario and claims. Wording follows `results/v1.1/v1.2_price_representativeness/FINDINGS.md`. Table 10 is a descriptive comparison of internal price spreads in different units. The public snapshot was not applied and prices were not rescaled. There are no real marketplace transaction logs.

| Dimension | In-simulator coverage / source | External evidence | Unsupported inference |
|---|---|---|---|
| Prices | Synthetic `price_per_1k` roster ranges; `configs/v1.0/scale.yaml` | Table 10 public-list spread comparison only | USD price levels, applied market mapping, real transaction pricing; no input/output simulator split |
| Task types | Arithmetic, word problems, sequence, logic; separate public long math subset; `tokenmarket/tasks.py` | None for market workload representativeness | General language tasks, industry task mix, task-disjoint transfer |
| Backends | Two cached Qwen checkpoints and configured mock; `configs/default.yaml`, scale roster | None | Broad real API catalog or online serving behavior |
| Sellers / strategies | Fixed main roster, resampled T4 roster; swap/theft/downgrade strategies; scale config and `strategic.py` | None | Measured seller populations or distributions of dishonest intent |
| Jurisdictions / corridors | CN/SG/BR tags, synthetic rules/flags/fees; inherited configs and `compliance.py` | None | Country fraud rates, actual legal compliance or measured trade corridors |
| Fraud types | Model swap, token theft, selective downgrade and supported combinations | None | Exhaustive marketplace fraud coverage or prevalence |
| Feedback | Reveal probability and delay knobs; main T2 delay fixed; `feedback.py` and run metadata | None | Real label acquisition or buyer-feedback rates |
| Audits | Simulated identity/length checks, fixed/random/risk-adaptive rates, penalties | None | Measured detector reliability, audit costs or operational deterrence |
| Latency | Configured seller/corridor latency plus simulated variation; cached generation timing separate | None | Measured marketplace latency or throughput |
| Volume / executed trades | Configured rounds/task instances and simulated allowed/blocked/unfilled purchases | None | Real transaction volume, demand distribution or market execution quality |

## Table 10 audit trail

Raw SKU rows, access date, input/output prices and missing entries: `configs/v1.0/frozen/prices.yaml` (also `configs/v1.0/prices.yaml`). Raw simulator ranges: `configs/v1.0/frozen/scale.yaml` / `configs/v1.0/scale.yaml`. The adopted comparison, exact mappings and exclusions are inspectable at:

- `results/v1.1/v1.2_price_representativeness/ratios.csv`
- `results/v1.1/v1.2_price_representativeness/MAPPING_RULE.md`
- `results/v1.1/v1.2_price_representativeness/compute_ratios.py`
- `results/v1.1/v1.2_price_representativeness/FINDINGS.md`

The snapshot records access on 2026-11-10. Both input and output prices must be filled. Google has only two filled models; unverified/null `gemini-3.1-flash-lite` is excluded. DeepSeek/Alibaba entries are empty. The 2026-12-01 `gemini-4-argon` schedule is footnote-only and excluded from primary max/min. The Qwen, mock and strategic simulator sellers are not mapped to public named SKUs. Roster ratios use range midpoints, with range-low and range-high sensitivity already in the frozen readout. Public output/input ratios have no simulator counterpart. No new price lookup or updated price value is substituted here.

`SHA256SUMS` and [ARTIFACT_MAP](ARTIFACT_MAP.md) pin these repository files. Table 10 remains a descriptive comparison only, without real-market transaction evidence.
