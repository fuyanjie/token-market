# A2 compliance — filter OFF control (§6), **v0.1-scale**

Setting: T2 v0.1 config at π=1.0 (immediate feedback), seeds 0–19, n_tasks=480. Filter ON = `*_compliant` policies (hard pre-filter + gateway `enforce`). Filter OFF = the same router without the filter (`stageroute`, `pilot`, `compliance_unaware_cheapest`), gateway in `audit_only` mode: violating flows go through and are counted. These policy ids already exist in `portfolio.py`; no core code changed. Runner: `scripts/v1/run_v1_t2_a2.py`.

Columns: violation rate = served purchases breaching a rule / tasks; fill rate = tasks with ≥1 served purchase / tasks; blocked/filtered per task = (candidates removed by the hard filter + gateway blocks) / tasks. Mean [95% bootstrap CI] over 20 seeds.

| policy | filter | violation rate | fill rate | blocked/filtered per task | accuracy | E (fraud_share) | J |
|---|---|---|---|---|---|---|---|
| stageroute_compliant | ON | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.510 [0.499, 0.521] | 0.827 [0.819, 0.834] | 0.014 [0.008, 0.020] | 0.820 [0.811, 0.829] |
| pilot_compliant | ON | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.510 [0.499, 0.521] | 0.814 [0.806, 0.822] | 0.046 [0.038, 0.054] | 0.791 [0.780, 0.801] |
| single_cheapest_compliant | ON | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.510 [0.499, 0.521] | 0.623 [0.612, 0.634] | 0.083 [0.077, 0.089] | 0.582 [0.570, 0.595] |
| stageroute | OFF | 0.129 [0.125, 0.134] | 0.992 [0.982, 1.000] | 0.000 [0.000, 0.000] | 0.856 [0.844, 0.865] | 0.019 [0.009, 0.031] | 0.717 [0.700, 0.731] |
| pilot | OFF | 0.134 [0.129, 0.140] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 0.849 [0.844, 0.855] | 0.036 [0.032, 0.040] | 0.697 [0.691, 0.704] |
| compliance_unaware_cheapest | OFF | 0.217 [0.210, 0.222] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 0.627 [0.617, 0.637] | 0.000 [0.000, 0.000] | 0.410 [0.399, 0.420] |
| audited_compliance_cascade | ON | 0.000 [0.000, 0.000] | 0.943 [0.936, 0.951] | 0.510 [0.499, 0.521] | 0.807 [0.795, 0.818] | 0.106 [0.085, 0.130] | 0.754 [0.730, 0.773] |

Paired OFF − ON (same seed):

| pair | metric | diff [95% CI] |
|---|---|---|
| stageroute − stageroute_compliant | violation_rate | +0.1295 [+0.1250, +0.1341] |
| stageroute − stageroute_compliant | fill_rate | -0.0077 [-0.0180, +0.0000] |
| stageroute − stageroute_compliant | blocked_or_filtered_per_task | -0.5103 [-0.5209, -0.4991] |
| pilot − pilot_compliant | violation_rate | +0.1340 [+0.1286, +0.1396] |
| pilot − pilot_compliant | fill_rate | +0.0000 [+0.0000, +0.0000] |
| pilot − pilot_compliant | blocked_or_filtered_per_task | -0.5103 [-0.5209, -0.4994] |
| compliance_unaware_cheapest − single_cheapest_compliant | violation_rate | +0.2166 [+0.2104, +0.2225] |
| compliance_unaware_cheapest − single_cheapest_compliant | fill_rate | +0.0000 [+0.0000, +0.0000] |
| compliance_unaware_cheapest − single_cheapest_compliant | blocked_or_filtered_per_task | -0.5103 [-0.5209, -0.4992] |

Reading (plain): with the filter on, violations are 0 in all runs; removing it from the same router yields violation rates of ≈0.13 (StageRoute, PILOT) and ≈0.22 (cheapest), with fill rate essentially unchanged (≤0.8 pp drop for StageRoute OFF, CI touches 0). So the zero in the ON rows is produced by the filter, not by an absence of violating buyer–seller pairs in this market. Violations by rule are in `A2_compliance_control.json` / `raw/A2_episodes.jsonl` (mainly SG-PDPA-26 and BR-LGPD-33-VIII).

**Not covered:** D3 (`audited_compliance_cascade`) has no filter-OFF variant — `is_hard()` keys on the policy id, and there is no non-hard audited policy id. Minimal change needed (not made): add an `audited_cascade` id to `BASELINE_POLICIES` in `tokenmarket/portfolio.py` and to `AUDITED_POLICIES`, dispatched to the same code path as `audited_compliance_cascade` (≈3 lines, Coding's area). D3 ON row is reported for reference.

Caveat: v0.1-scale has 3 sellers / 6 buyers and a basic rule set; violation rates will change at §2 scale.