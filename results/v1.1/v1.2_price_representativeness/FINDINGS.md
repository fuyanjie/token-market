# Findings (descriptive only; not a calibration)

Computed 2026-11-15 Asia/Shanghai from frozen inputs. See `MAPPING_RULE.md` and `ratios.md`.

## Simulator roster (synthetic units, midpoint of configured range)

- honest 1.5B mid = (0.17+0.24)/2 = 0.205
- honest 0.5B mid = (0.08+0.12)/2 = 0.1
- honest mock mid = (0.05+0.08)/2 = 0.065
- strategic mid = (0.15+0.21)/2 = 0.18
- primary ratios: 1.5B/0.5B = 2.05; 1.5B/mock = 3.153846154; 0.5B/mock = 1.538461538
- overlap note (not a representativeness claim): strategic/1.5B = 0.8780487805
- sensitivity using range lows: 1.5B/0.5B = 2.125; 1.5B/mock = 3.4; 0.5B/mock = 1.6
- sensitivity using range highs: 1.5B/0.5B = 2; 1.5B/mock = 3; 0.5B/mock = 1.5

The primary honest max/min midpoint ratio is 1.5B/mock = 3.153846154.

## Public list snapshot (USD per 1K tokens, access_date 2026-11-10)

Primary filled rows: n=10 (openai 4, anthropic 4, google 2).

- OpenAI output_max/output_min = 40; input_max/input_min = 50
- Anthropic output_max/output_min = 80; input_max/input_min = 80
- Google output_max/output_min = 1.2; input_max/input_min = 1
- Pool (OpenAI+Anthropic+Google) output_max/output_min = 100; input_max/input_min = 100
- Pool output/input min/median/max = 5 / 5 / 6.25

Compared with each provider's primary output_max/output_min, the roster 1.5B/mock midpoint ratio (3.153846154) is smaller than OpenAI (40), Anthropic (80), and the three-provider pool (100), and larger than Google (1.2). The Google primary set has only two filled models; gemini-3.1-flash-lite is excluded as unverified, so 1.2 is not a full-catalog spread. These are internal spreads in different units; they do not say the simulator is cheaper or more expensive in USD.

## What this is not

- Not a calibration, and not a claim that prices are 已校准. The snapshot was not applied to `scale.yaml`.
- Not evidence that the simulator represents real API-market transactions. There are no real marketplace transaction logs, so latency, volume, jurisdictions, and executed trades cannot be compared quantitatively.
- Simulator `price_per_1k` has no input/output split, so public output/input ratios have no roster counterpart.
- DeepSeek and Alibaba Model Studio were empty TODOs on 2026-11-10; `gemini-3.1-flash-lite` was unverified/null and is excluded. `gemini-4-argon`'s 2026-12-01 schedule is a footnote only and is not in the primary ratios.
- Qwen 0.5B/1.5B are not mapped to named GPT/Claude/Gemini SKUs.

## Later protocol §7 robustness (not done here)

A calibrated robustness rerun still requires a mapping that rescales synthetic units, written down before any rerun, then a separate results table. That table must not be mixed with Decision A / Result 1. This file is only the descriptive ratio comparison.
