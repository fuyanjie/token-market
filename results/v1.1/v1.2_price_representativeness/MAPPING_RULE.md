# Frozen comparison rule (written before ratios were computed)

Date: 2026-11-15 Asia/Shanghai (UTC+8)
Repo: `/workspace/token-market`, branch `v1.1`
Inputs:
- `configs/v1.0/frozen/prices.yaml` (public list snapshot, access_date 2026-11-10)
- `configs/v1.0/frozen/scale.yaml` (simulator roster; `price_per_1k` ranges are synthetic market units)

This is a descriptive ratio comparison, not a calibration. Simulator prices are not rescaled. The text must not say “calibrated” or “已校准”. Simulator models are not paired to named public SKUs (Qwen 0.5B/1.5B are not GPT/Claude/Gemini). Simulator `price_per_1k` is a single synthetic unit with no input/output split, so input/output mix cannot be compared to the public lists.

1. Public snapshot: include a model row only if both `input` and `output` are non-null numbers. Exclude TODO/null/empty providers (DeepSeek, Alibaba) and unverified null rows (`gemini-3.1-flash-lite`). For `gemini-4-argon`, the primary table uses the access-date price (the through-2026-11-30 values). The `from_2026_12_01` schedule is reported only as a clearly labeled footnote/sensitivity row and is not mixed into primary max/min ratios.
2. For each filled provider, and for the pool of all filled primary rows across OpenAI+Anthropic+Google: report `output_max/output_min` and `input_max/input_min`. Also, for each included model, `output/input`, then min/median/max of those ratios within each provider and in the pool. Median is the ordinary mid-value of the sorted list (average of the two central values if even count).
3. Simulator roster bands are summarized by the midpoint of the configured range, midpoint = (lo+hi)/2, fixed a priori:
   - honest 1.5B: (0.17+0.24)/2
   - honest 0.5B: (0.08+0.12)/2
   - honest mock: (0.05+0.08)/2
   - strategic: (0.15+0.21)/2
   Primary roster ratios (midpoint): 1.5B/0.5B, 1.5B/mock, 0.5B/mock. Also report strategic mid / 1.5B mid as an overlap note, not as a representativeness claim. Sensitivity (clearly labeled, not primary): the same three honest ratios using range lows and using range highs.
4. Do not invent missing market evidence. There are no real marketplace transaction logs, and therefore no quantitative comparison of latency, volume, jurisdictions, or executed trades. Incomplete providers stay incomplete.
5. Record source paths, access date, URLs as written in prices.yaml, and sha256 of both yaml files. If a hash differs from the expected values, stop.
