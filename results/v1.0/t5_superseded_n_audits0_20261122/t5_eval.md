# Official T5 Readout (docs/PROTOCOL_T5.md, frozen 2026-11-22)

- Protocol sha256: `4301f4b281e90b1b835d1e7868e3b00c98bc8eaee382cf29f8646c6fa7272542`
- `configs/v1.0/scale.yaml` sha256: `780e9b961d89bad6fd520c9cbfd5710055ff2d5d3e0ff3bcfbd745709eb0da6c`
- Train seeds: `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]` (inner fit `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]`, inner val `[10, 11, 12, 13]`); Test seeds: `[14, 15, 16, 17, 18, 19]` (**n = 6 test runs**, NOT 20).
- Bootstrap: B = 10000, 95% percentile CIs, paired two-sided bootstrap p-values, Holm within each (pi, metric) over all 21 pairs of the 7 official methods (alpha = 0.05).
- Leakage check passed: `True` (5018 train rows, 0 offenders).
- Hold-out prompts: 15 unique prompt hashes drawn via `random.Random('t5-prompt-holdout-20261122')` (excluded from training and tau selection).

## Frozen tau selection (inner val seeds [10, 11, 12, 13], non-holdout tasks only)

| learner | selected tau | floor_rule_triggered | strongest val acc | chosen val acc | chosen val cost/task |
|---|---:|---|---:|---:|---:|
| Two-stage LOGREG | 0.50 | False | 0.5282 | 0.6372 | 0.01198 |
| Two-stage GBDT | 0.50 | False | 0.5282 | 0.6115 | 0.00936 |

## Main & pi side tables (ALL test tasks, seeds [14, 15, 16, 17, 18, 19], n=6)

### pi = 1 (Main table)

| Method | Family | Accuracy | Cost/task | Violation | E (fraud_share) | Fill rate | Oracle acc regret (side) | Oracle cost regret (side) |
|---|---|---|---|---|---|---|---|---|
| Two-stage LR (trained on logs) | trained_recommender | 0.6351 [0.6156, 0.6517] | 0.01261 [0.01185, 0.01356] | 0.0000 [0.0000, 0.0000] | 0.0387 [0.0231, 0.0565] | 0.9840 [0.9740, 0.9931] | 0.3274 [0.3104, 0.3469] | -0.00925 [-0.01092, -0.00729] |
| Two-stage GBDT (trained on logs) | trained_recommender | 0.6920 [0.6757, 0.7083] | 0.01251 [0.01194, 0.01303] | 0.0000 [0.0000, 0.0000] | 0.0466 [0.0202, 0.0723] | 0.9934 [0.9858, 0.9993] | 0.2705 [0.2535, 0.2868] | -0.00889 [-0.00988, -0.00802] |
| Cheapest eligible | untrained_baseline | 0.6229 [0.6062, 0.6361] | 0.00811 [0.00762, 0.00857] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 0.3396 [0.3264, 0.3559] | -0.00893 [-0.00974, -0.00814] |
| Strongest eligible | untrained_baseline | 0.6087 [0.5226, 0.6785] | 0.02268 [0.02194, 0.02351] | 0.0000 [0.0000, 0.0000] | 0.5383 [0.4286, 0.6600] | 0.9174 [0.9135, 0.9222] | 0.3538 [0.2837, 0.4382] | 0.00515 [0.00445, 0.00584] |
| Random eligible | untrained_baseline | 0.6948 [0.6858, 0.7049] | 0.02125 [0.02083, 0.02169] | 0.0000 [0.0000, 0.0000] | 0.1356 [0.1198, 0.1511] | 0.9295 [0.9240, 0.9354] | 0.2677 [0.2573, 0.2767] | 0.00443 [0.00394, 0.00480] |
| Market-adapted PILOT (pilot_v1) | untrained_baseline | 0.7774 [0.7687, 0.7892] | 0.02433 [0.02420, 0.02446] | 0.0000 [0.0000, 0.0000] | 0.1565 [0.1478, 0.1654] | 0.9917 [0.9892, 0.9944] | 0.1851 [0.1739, 0.1938] | 0.00787 [0.00721, 0.00852] |
| Market-adapted StageRoute (stageroute_v1) | untrained_baseline | 0.7490 [0.7170, 0.7802] | 0.02386 [0.02251, 0.02514] | 0.0000 [0.0000, 0.0000] | 0.0789 [0.0370, 0.1201] | 0.9156 [0.9083, 0.9212] | 0.2135 [0.1819, 0.2455] | 0.00671 [0.00499, 0.00837] |

Significant Holm-adjusted primary-metric pairs at pi=1 (p_Holm < 0.05, family size 21): **66**.

| Metric | Method A | Method B | Delta (A - B) [95% CI] | p_raw | p_Holm |
|---|---|---|---|---:|---:|
| accuracy | t5_logreg | t5_gbdt | -0.05694 [-0.09030, -0.02917] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | random_eligible | -0.05972 [-0.07951, -0.03785] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | pilot | -0.14236 [-0.15868, -0.12708] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | stageroute | -0.11389 [-0.14861, -0.07847] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | cheapest_eligible | +0.06910 [+0.04896, +0.09097] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | pilot | -0.08542 [-0.10174, -0.06562] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | stageroute | -0.05694 [-0.08958, -0.02639] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | random_eligible | -0.07188 [-0.09306, -0.05486] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | pilot | -0.15451 [-0.17083, -0.13924] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | stageroute | -0.12604 [-0.16910, -0.09167] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | pilot | -0.16875 [-0.25174, -0.09235] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | stageroute | -0.14028 [-0.21319, -0.09028] | 0.0000 | 0.0000 |
| accuracy | random_eligible | pilot | -0.08264 [-0.09965, -0.06667] | 0.0000 | 0.0000 |
| accuracy | random_eligible | stageroute | -0.05417 [-0.08611, -0.02118] | 0.0004 | 0.0032 |
| cost_per_task | t5_logreg | cheapest_eligible | +0.00450 [+0.00389, +0.00515] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | strongest_eligible | -0.01007 [-0.01141, -0.00897] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | random_eligible | -0.00864 [-0.00947, -0.00791] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | pilot | -0.01171 [-0.01255, -0.01072] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | stageroute | -0.01124 [-0.01291, -0.00972] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | cheapest_eligible | +0.00440 [+0.00419, +0.00462] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | strongest_eligible | -0.01017 [-0.01116, -0.00922] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | random_eligible | -0.00874 [-0.00918, -0.00828] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | pilot | -0.01182 [-0.01247, -0.01120] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | stageroute | -0.01135 [-0.01237, -0.01044] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | strongest_eligible | -0.01457 [-0.01548, -0.01374] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | random_eligible | -0.01314 [-0.01349, -0.01277] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | pilot | -0.01621 [-0.01676, -0.01567] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | stageroute | -0.01575 [-0.01682, -0.01476] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | random_eligible | +0.00143 [+0.00079, +0.00207] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | pilot | -0.00164 [-0.00231, -0.00089] | 0.0000 | 0.0000 |
| cost_per_task | random_eligible | pilot | -0.00308 [-0.00354, -0.00264] | 0.0000 | 0.0000 |
| cost_per_task | random_eligible | stageroute | -0.00261 [-0.00365, -0.00160] | 0.0000 | 0.0000 |
| E | t5_logreg | cheapest_eligible | +0.03869 [+0.02313, +0.05650] | 0.0000 | 0.0000 |
| E | t5_logreg | strongest_eligible | -0.49957 [-0.62603, -0.39506] | 0.0000 | 0.0000 |
| E | t5_logreg | random_eligible | -0.09692 [-0.12109, -0.07803] | 0.0000 | 0.0000 |
| E | t5_logreg | pilot | -0.11781 [-0.13848, -0.09715] | 0.0000 | 0.0000 |
| E | t5_gbdt | cheapest_eligible | +0.04663 [+0.02018, +0.07224] | 0.0000 | 0.0000 |
| E | t5_gbdt | strongest_eligible | -0.49164 [-0.61210, -0.36540] | 0.0000 | 0.0000 |
| E | t5_gbdt | random_eligible | -0.08899 [-0.11981, -0.05500] | 0.0000 | 0.0000 |
| E | t5_gbdt | pilot | -0.10988 [-0.13538, -0.08174] | 0.0000 | 0.0000 |
| E | cheapest_eligible | strongest_eligible | -0.53826 [-0.66516, -0.42738] | 0.0000 | 0.0000 |
| E | cheapest_eligible | random_eligible | -0.13561 [-0.15111, -0.11992] | 0.0000 | 0.0000 |
| E | cheapest_eligible | pilot | -0.15651 [-0.16564, -0.14774] | 0.0000 | 0.0000 |
| E | cheapest_eligible | stageroute | -0.07887 [-0.12063, -0.03695] | 0.0034 | 0.0170 |
| E | strongest_eligible | random_eligible | +0.40265 [+0.27981, +0.53792] | 0.0000 | 0.0000 |
| E | strongest_eligible | pilot | +0.38176 [+0.26675, +0.51032] | 0.0000 | 0.0000 |
| E | strongest_eligible | stageroute | +0.45939 [+0.37736, +0.56158] | 0.0000 | 0.0000 |
| E | random_eligible | pilot | -0.02089 [-0.03442, -0.00810] | 0.0000 | 0.0000 |
| E | pilot | stageroute | +0.07763 [+0.02765, +0.12779] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | t5_gbdt | -0.00938 [-0.01250, -0.00521] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | cheapest_eligible | -0.01597 [-0.02639, -0.00694] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | strongest_eligible | +0.06667 [+0.05903, +0.07326] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | random_eligible | +0.05451 [+0.04688, +0.06215] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | stageroute | +0.06840 [+0.05660, +0.07708] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | strongest_eligible | +0.07604 [+0.07014, +0.08090] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | random_eligible | +0.06389 [+0.05833, +0.06944] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | stageroute | +0.07778 [+0.06771, +0.08542] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | strongest_eligible | +0.08264 [+0.07778, +0.08646] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | random_eligible | +0.07049 [+0.06493, +0.07604] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | pilot | +0.00833 [+0.00556, +0.01076] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | stageroute | +0.08438 [+0.07882, +0.09132] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | random_eligible | -0.01215 [-0.01840, -0.00868] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | pilot | -0.07431 [-0.07986, -0.06875] | 0.0000 | 0.0000 |
| fill_rate | random_eligible | pilot | -0.06215 [-0.06979, -0.05451] | 0.0000 | 0.0000 |
| fill_rate | random_eligible | stageroute | +0.01389 [+0.00590, +0.02188] | 0.0000 | 0.0000 |
| fill_rate | pilot | stageroute | +0.07604 [+0.07014, +0.08264] | 0.0000 | 0.0000 |

### pi = 0.1 (Required side table)

| Method | Family | Accuracy | Cost/task | Violation | E (fraud_share) | Fill rate | Oracle acc regret (side) | Oracle cost regret (side) |
|---|---|---|---|---|---|---|---|---|
| Two-stage LR (trained on logs) | trained_recommender | 0.6347 [0.6149, 0.6514] | 0.01261 [0.01186, 0.01356] | 0.0000 [0.0000, 0.0000] | 0.0380 [0.0211, 0.0550] | 0.9840 [0.9740, 0.9931] | 0.3278 [0.3115, 0.3476] | -0.00924 [-0.01091, -0.00737] |
| Two-stage GBDT (trained on logs) | trained_recommender | 0.6920 [0.6753, 0.7090] | 0.01251 [0.01194, 0.01303] | 0.0000 [0.0000, 0.0000] | 0.0466 [0.0202, 0.0723] | 0.9934 [0.9858, 0.9993] | 0.2705 [0.2542, 0.2868] | -0.00889 [-0.00988, -0.00803] |
| Cheapest eligible | untrained_baseline | 0.6229 [0.6066, 0.6361] | 0.00811 [0.00764, 0.00857] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 0.3396 [0.3264, 0.3559] | -0.00893 [-0.00974, -0.00814] |
| Strongest eligible | untrained_baseline | 0.6073 [0.5260, 0.6806] | 0.02268 [0.02193, 0.02349] | 0.0000 [0.0000, 0.0000] | 0.5405 [0.4278, 0.6697] | 0.9174 [0.9135, 0.9222] | 0.3552 [0.2861, 0.4365] | 0.00515 [0.00452, 0.00586] |
| Random eligible | untrained_baseline | 0.6865 [0.6757, 0.6972] | 0.02073 [0.01999, 0.02137] | 0.0000 [0.0000, 0.0000] | 0.1355 [0.1237, 0.1478] | 0.9281 [0.9205, 0.9351] | 0.2760 [0.2653, 0.2868] | 0.00374 [0.00292, 0.00459] |
| Market-adapted PILOT (pilot_v1) | untrained_baseline | 0.7226 [0.7017, 0.7417] | 0.02460 [0.02421, 0.02497] | 0.0000 [0.0000, 0.0000] | 0.2588 [0.2214, 0.2981] | 0.9840 [0.9795, 0.9885] | 0.2399 [0.2208, 0.2604] | 0.00642 [0.00559, 0.00719] |
| Market-adapted StageRoute (stageroute_v1) | untrained_baseline | 0.7295 [0.6903, 0.7611] | 0.02173 [0.02077, 0.02259] | 0.0000 [0.0000, 0.0000] | 0.1165 [0.0499, 0.1850] | 0.9271 [0.9191, 0.9333] | 0.2330 [0.2014, 0.2722] | 0.00469 [0.00349, 0.00592] |

Significant Holm-adjusted primary-metric pairs at pi=0.1 (p_Holm < 0.05, family size 21): **64**.

| Metric | Method A | Method B | Delta (A - B) [95% CI] | p_raw | p_Holm |
|---|---|---|---|---:|---:|
| accuracy | t5_logreg | t5_gbdt | -0.05729 [-0.09062, -0.02917] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | random_eligible | -0.05174 [-0.06944, -0.03924] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | pilot | -0.08785 [-0.10312, -0.07049] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | stageroute | -0.09479 [-0.13021, -0.05069] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | cheapest_eligible | +0.06910 [+0.04896, +0.09097] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | random_eligible | -0.06354 [-0.08472, -0.04306] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | pilot | -0.09965 [-0.12535, -0.07292] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | stageroute | -0.10660 [-0.14861, -0.06042] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | pilot | -0.11528 [-0.18576, -0.04479] | 0.0002 | 0.0022 |
| accuracy | strongest_eligible | stageroute | -0.12222 [-0.18993, -0.06667] | 0.0000 | 0.0000 |
| accuracy | random_eligible | pilot | -0.03611 [-0.05347, -0.02049] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | cheapest_eligible | +0.00450 [+0.00390, +0.00515] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | strongest_eligible | -0.01007 [-0.01141, -0.00896] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | random_eligible | -0.00811 [-0.00869, -0.00751] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | pilot | -0.01199 [-0.01282, -0.01108] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | stageroute | -0.00911 [-0.01046, -0.00729] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | cheapest_eligible | +0.00440 [+0.00419, +0.00462] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | strongest_eligible | -0.01017 [-0.01115, -0.00926] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | random_eligible | -0.00822 [-0.00878, -0.00768] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | pilot | -0.01209 [-0.01273, -0.01142] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | stageroute | -0.00922 [-0.01013, -0.00808] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | strongest_eligible | -0.01457 [-0.01548, -0.01374] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | random_eligible | -0.01261 [-0.01301, -0.01217] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | pilot | -0.01649 [-0.01706, -0.01579] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | stageroute | -0.01361 [-0.01445, -0.01240] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | random_eligible | +0.00195 [+0.00108, +0.00296] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | pilot | -0.00192 [-0.00267, -0.00097] | 0.0000 | 0.0000 |
| cost_per_task | random_eligible | pilot | -0.00387 [-0.00471, -0.00314] | 0.0000 | 0.0000 |
| cost_per_task | pilot | stageroute | +0.00288 [+0.00173, +0.00409] | 0.0000 | 0.0000 |
| E | t5_logreg | cheapest_eligible | +0.03799 [+0.02108, +0.05573] | 0.0000 | 0.0000 |
| E | t5_logreg | strongest_eligible | -0.50254 [-0.62630, -0.40181] | 0.0000 | 0.0000 |
| E | t5_logreg | random_eligible | -0.09749 [-0.11771, -0.08041] | 0.0000 | 0.0000 |
| E | t5_logreg | pilot | -0.22078 [-0.26546, -0.17407] | 0.0000 | 0.0000 |
| E | t5_logreg | stageroute | -0.07848 [-0.13772, -0.02200] | 0.0000 | 0.0000 |
| E | t5_gbdt | cheapest_eligible | +0.04663 [+0.02031, +0.07224] | 0.0000 | 0.0000 |
| E | t5_gbdt | strongest_eligible | -0.49390 [-0.61471, -0.37325] | 0.0000 | 0.0000 |
| E | t5_gbdt | random_eligible | -0.08886 [-0.12240, -0.05720] | 0.0000 | 0.0000 |
| E | t5_gbdt | pilot | -0.21215 [-0.25844, -0.16426] | 0.0000 | 0.0000 |
| E | cheapest_eligible | strongest_eligible | -0.54053 [-0.67050, -0.42738] | 0.0000 | 0.0000 |
| E | cheapest_eligible | random_eligible | -0.13548 [-0.14751, -0.12373] | 0.0000 | 0.0000 |
| E | cheapest_eligible | pilot | -0.25878 [-0.29815, -0.21994] | 0.0000 | 0.0000 |
| E | cheapest_eligible | stageroute | -0.11647 [-0.18768, -0.04986] | 0.0000 | 0.0000 |
| E | strongest_eligible | random_eligible | +0.40505 [+0.28537, +0.53780] | 0.0000 | 0.0000 |
| E | strongest_eligible | pilot | +0.28175 [+0.18432, +0.37918] | 0.0000 | 0.0000 |
| E | strongest_eligible | stageroute | +0.42406 [+0.35444, +0.49907] | 0.0000 | 0.0000 |
| E | random_eligible | pilot | -0.12329 [-0.17058, -0.07727] | 0.0000 | 0.0000 |
| E | pilot | stageroute | +0.14231 [+0.07794, +0.20594] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | t5_gbdt | -0.00938 [-0.01250, -0.00521] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | cheapest_eligible | -0.01597 [-0.02639, -0.00694] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | strongest_eligible | +0.06667 [+0.05903, +0.07326] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | random_eligible | +0.05590 [+0.05000, +0.06111] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | stageroute | +0.05694 [+0.04444, +0.06771] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | strongest_eligible | +0.07604 [+0.06979, +0.08090] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | random_eligible | +0.06528 [+0.06042, +0.07049] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | pilot | +0.00938 [+0.00278, +0.01597] | 0.0028 | 0.0140 |
| fill_rate | t5_gbdt | stageroute | +0.06632 [+0.05625, +0.07569] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | strongest_eligible | +0.08264 [+0.07778, +0.08646] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | random_eligible | +0.07188 [+0.06493, +0.07951] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | pilot | +0.01597 [+0.01146, +0.02049] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | stageroute | +0.07292 [+0.06667, +0.08090] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | random_eligible | -0.01076 [-0.01528, -0.00625] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | pilot | -0.06667 [-0.07257, -0.06146] | 0.0000 | 0.0000 |
| fill_rate | random_eligible | pilot | -0.05590 [-0.06597, -0.04722] | 0.0000 | 0.0000 |
| fill_rate | pilot | stageroute | +0.05694 [+0.04722, +0.06875] | 0.0000 | 0.0000 |

### pi = 0 (Required side table)

| Method | Family | Accuracy | Cost/task | Violation | E (fraud_share) | Fill rate | Oracle acc regret (side) | Oracle cost regret (side) |
|---|---|---|---|---|---|---|---|---|
| Two-stage LR (trained on logs) | trained_recommender | 0.6351 [0.6156, 0.6517] | 0.01261 [0.01185, 0.01356] | 0.0000 [0.0000, 0.0000] | 0.0387 [0.0225, 0.0565] | 0.9840 [0.9740, 0.9931] | 0.3274 [0.3108, 0.3469] | -0.00925 [-0.01089, -0.00738] |
| Two-stage GBDT (trained on logs) | trained_recommender | 0.6920 [0.6757, 0.7083] | 0.01251 [0.01195, 0.01303] | 0.0000 [0.0000, 0.0000] | 0.0466 [0.0209, 0.0723] | 0.9934 [0.9858, 0.9993] | 0.2705 [0.2542, 0.2868] | -0.00889 [-0.00988, -0.00805] |
| Cheapest eligible | untrained_baseline | 0.6229 [0.6066, 0.6361] | 0.00811 [0.00763, 0.00857] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 0.3396 [0.3264, 0.3559] | -0.00893 [-0.00974, -0.00814] |
| Strongest eligible | untrained_baseline | 0.6087 [0.5243, 0.6788] | 0.02268 [0.02194, 0.02349] | 0.0000 [0.0000, 0.0000] | 0.5383 [0.4278, 0.6600] | 0.9174 [0.9135, 0.9222] | 0.3538 [0.2819, 0.4361] | 0.00515 [0.00445, 0.00588] |
| Random eligible | untrained_baseline | 0.6823 [0.6691, 0.6951] | 0.02106 [0.02053, 0.02156] | 0.0000 [0.0000, 0.0000] | 0.1361 [0.1232, 0.1517] | 0.9323 [0.9243, 0.9406] | 0.2802 [0.2674, 0.2934] | 0.00402 [0.00348, 0.00454] |
| Market-adapted PILOT (pilot_v1) | untrained_baseline | 0.6528 [0.5726, 0.7233] | 0.02228 [0.02181, 0.02278] | 0.0000 [0.0000, 0.0000] | 0.4663 [0.3596, 0.5914] | 0.9903 [0.9854, 0.9938] | 0.3097 [0.2410, 0.3899] | 0.00445 [0.00362, 0.00500] |
| Market-adapted StageRoute (stageroute_v1) | untrained_baseline | 0.6983 [0.6483, 0.7472] | 0.02050 [0.01920, 0.02179] | 0.0000 [0.0000, 0.0000] | 0.1284 [0.0505, 0.2002] | 0.9292 [0.9187, 0.9389] | 0.2642 [0.2153, 0.3135] | 0.00354 [0.00204, 0.00508] |

Significant Holm-adjusted primary-metric pairs at pi=0 (p_Holm < 0.05, family size 21): **60**.

| Metric | Method A | Method B | Delta (A - B) [95% CI] | p_raw | p_Holm |
|---|---|---|---|---:|---:|
| accuracy | t5_logreg | t5_gbdt | -0.05694 [-0.09028, -0.02847] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | random_eligible | -0.04722 [-0.07431, -0.02222] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | cheapest_eligible | +0.06910 [+0.04861, +0.09097] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | random_eligible | -0.05938 [-0.08125, -0.03889] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | stageroute | -0.07535 [-0.13090, -0.02292] | 0.0016 | 0.0240 |
| accuracy | strongest_eligible | pilot | -0.04410 [-0.05382, -0.03403] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | stageroute | -0.08958 [-0.16181, -0.03299] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | cheapest_eligible | +0.00450 [+0.00390, +0.00516] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | strongest_eligible | -0.01007 [-0.01141, -0.00897] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | random_eligible | -0.00844 [-0.00899, -0.00788] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | pilot | -0.00966 [-0.01063, -0.00870] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | stageroute | -0.00788 [-0.00967, -0.00617] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | cheapest_eligible | +0.00440 [+0.00419, +0.00462] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | strongest_eligible | -0.01017 [-0.01116, -0.00926] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | random_eligible | -0.00855 [-0.00907, -0.00808] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | pilot | -0.00977 [-0.01056, -0.00895] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | stageroute | -0.00799 [-0.00917, -0.00704] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | strongest_eligible | -0.01457 [-0.01548, -0.01374] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | random_eligible | -0.01294 [-0.01328, -0.01264] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | pilot | -0.01416 [-0.01483, -0.01344] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | stageroute | -0.01239 [-0.01362, -0.01132] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | random_eligible | +0.00163 [+0.00098, +0.00249] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | stageroute | +0.00218 [+0.00102, +0.00325] | 0.0000 | 0.0000 |
| cost_per_task | random_eligible | pilot | -0.00122 [-0.00181, -0.00064] | 0.0000 | 0.0000 |
| cost_per_task | pilot | stageroute | +0.00178 [+0.00053, +0.00297] | 0.0038 | 0.0152 |
| E | t5_logreg | cheapest_eligible | +0.03869 [+0.02313, +0.05650] | 0.0000 | 0.0000 |
| E | t5_logreg | strongest_eligible | -0.49957 [-0.62603, -0.39704] | 0.0000 | 0.0000 |
| E | t5_logreg | random_eligible | -0.09740 [-0.10448, -0.08865] | 0.0000 | 0.0000 |
| E | t5_logreg | pilot | -0.42764 [-0.54891, -0.32197] | 0.0000 | 0.0000 |
| E | t5_logreg | stageroute | -0.08968 [-0.15476, -0.02459] | 0.0062 | 0.0248 |
| E | t5_gbdt | cheapest_eligible | +0.04663 [+0.02018, +0.07230] | 0.0000 | 0.0000 |
| E | t5_gbdt | strongest_eligible | -0.49164 [-0.61787, -0.36407] | 0.0000 | 0.0000 |
| E | t5_gbdt | random_eligible | -0.08947 [-0.12652, -0.04943] | 0.0000 | 0.0000 |
| E | t5_gbdt | pilot | -0.41971 [-0.54208, -0.30133] | 0.0000 | 0.0000 |
| E | cheapest_eligible | strongest_eligible | -0.53826 [-0.66001, -0.42700] | 0.0000 | 0.0000 |
| E | cheapest_eligible | random_eligible | -0.13610 [-0.15222, -0.12250] | 0.0000 | 0.0000 |
| E | cheapest_eligible | pilot | -0.46634 [-0.59052, -0.35392] | 0.0000 | 0.0000 |
| E | cheapest_eligible | stageroute | -0.12837 [-0.20015, -0.05115] | 0.0000 | 0.0000 |
| E | strongest_eligible | random_eligible | +0.40216 [+0.29805, +0.53032] | 0.0000 | 0.0000 |
| E | strongest_eligible | pilot | +0.07193 [+0.05279, +0.09173] | 0.0000 | 0.0000 |
| E | strongest_eligible | stageroute | +0.40989 [+0.31949, +0.53865] | 0.0000 | 0.0000 |
| E | random_eligible | pilot | -0.33024 [-0.45122, -0.22217] | 0.0000 | 0.0000 |
| E | pilot | stageroute | +0.33796 [+0.26013, +0.46464] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | t5_gbdt | -0.00938 [-0.01250, -0.00521] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | cheapest_eligible | -0.01597 [-0.02604, -0.00694] | 0.0002 | 0.0012 |
| fill_rate | t5_logreg | strongest_eligible | +0.06667 [+0.05868, +0.07326] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | random_eligible | +0.05174 [+0.04792, +0.05590] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | stageroute | +0.05486 [+0.04686, +0.06285] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | strongest_eligible | +0.07604 [+0.07014, +0.08090] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | random_eligible | +0.06111 [+0.05556, +0.06528] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | stageroute | +0.06424 [+0.05556, +0.07326] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | strongest_eligible | +0.08264 [+0.07778, +0.08646] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | random_eligible | +0.06771 [+0.05903, +0.07569] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | pilot | +0.00972 [+0.00625, +0.01458] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | stageroute | +0.07083 [+0.06111, +0.08160] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | random_eligible | -0.01493 [-0.02153, -0.00868] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | pilot | -0.07292 [-0.07813, -0.06701] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | stageroute | -0.01181 [-0.01944, -0.00347] | 0.0044 | 0.0220 |
| fill_rate | random_eligible | pilot | -0.05799 [-0.06528, -0.05069] | 0.0000 | 0.0000 |
| fill_rate | pilot | stageroute | +0.06111 [+0.05174, +0.07188] | 0.0000 | 0.0000 |


## Unique-prompt hold-out side tables (15 hold-out prompt hashes, seeds [14, 15, 16, 17, 18, 19], n=6)

### pi = 1 (Required side table)

| Method | Family | Accuracy | Cost/task | Violation | E (fraud_share) | Fill rate | Oracle acc regret (side) | Oracle cost regret (side) |
|---|---|---|---|---|---|---|---|---|
| Two-stage LR (trained on logs) | trained_recommender | 0.5574 [0.5222, 0.6000] | 0.01144 [0.01073, 0.01234] | 0.0000 [0.0000, 0.0000] | 0.0303 [0.0169, 0.0438] | 0.9815 [0.9685, 0.9944] | 0.3759 [0.3333, 0.4111] | -0.01174 [-0.01331, -0.00985] |
| Two-stage GBDT (trained on logs) | trained_recommender | 0.6370 [0.5907, 0.6852] | 0.01441 [0.01390, 0.01489] | 0.0000 [0.0000, 0.0000] | 0.1022 [0.0469, 0.1520] | 0.9889 [0.9778, 0.9981] | 0.2963 [0.2481, 0.3407] | -0.00820 [-0.00898, -0.00749] |
| Cheapest eligible | untrained_baseline | 0.6093 [0.5852, 0.6334] | 0.00787 [0.00759, 0.00816] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 0.3241 [0.3000, 0.3481] | -0.00999 [-0.01063, -0.00935] |
| Strongest eligible | untrained_baseline | 0.5241 [0.4704, 0.5778] | 0.02031 [0.01956, 0.02101] | 0.0000 [0.0000, 0.0000] | 0.5486 [0.4512, 0.6497] | 0.9111 [0.9056, 0.9167] | 0.4093 [0.3556, 0.4648] | 0.00203 [0.00140, 0.00262] |
| Random eligible | untrained_baseline | 0.6259 [0.6056, 0.6463] | 0.01900 [0.01838, 0.01968] | 0.0000 [0.0000, 0.0000] | 0.1367 [0.0944, 0.1787] | 0.9204 [0.9148, 0.9259] | 0.3074 [0.2870, 0.3278] | 0.00140 [0.00069, 0.00217] |
| Market-adapted PILOT (pilot_v1) | untrained_baseline | 0.7426 [0.7130, 0.7778] | 0.02193 [0.02152, 0.02254] | 0.0000 [0.0000, 0.0000] | 0.1515 [0.1271, 0.1739] | 0.9907 [0.9796, 0.9981] | 0.1907 [0.1556, 0.2185] | 0.00463 [0.00375, 0.00548] |
| Market-adapted StageRoute (stageroute_v1) | untrained_baseline | 0.6611 [0.6204, 0.7019] | 0.02126 [0.02005, 0.02243] | 0.0000 [0.0000, 0.0000] | 0.0918 [0.0424, 0.1400] | 0.9056 [0.8963, 0.9148] | 0.2722 [0.2315, 0.3130] | 0.00337 [0.00176, 0.00491] |

Significant Holm-adjusted primary-metric pairs at pi=1 (p_Holm < 0.05, family size 21): **58**.

| Metric | Method A | Method B | Delta (A - B) [95% CI] | p_raw | p_Holm |
|---|---|---|---|---:|---:|
| accuracy | t5_logreg | t5_gbdt | -0.07963 [-0.14815, -0.02037] | 0.0044 | 0.0440 |
| accuracy | t5_logreg | random_eligible | -0.06852 [-0.09630, -0.03329] | 0.0004 | 0.0048 |
| accuracy | t5_logreg | pilot | -0.18519 [-0.20926, -0.15741] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | stageroute | -0.10370 [-0.16111, -0.04074] | 0.0018 | 0.0198 |
| accuracy | t5_gbdt | strongest_eligible | +0.11296 [+0.04625, +0.18519] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | pilot | -0.10556 [-0.15190, -0.05000] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | pilot | -0.13333 [-0.17963, -0.08333] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | random_eligible | -0.10185 [-0.16481, -0.04444] | 0.0002 | 0.0026 |
| accuracy | strongest_eligible | pilot | -0.21852 [-0.27222, -0.16481] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | stageroute | -0.13704 [-0.15741, -0.11667] | 0.0000 | 0.0000 |
| accuracy | random_eligible | pilot | -0.11667 [-0.15556, -0.07778] | 0.0000 | 0.0000 |
| accuracy | pilot | stageroute | +0.08148 [+0.03704, +0.13704] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | t5_gbdt | -0.00296 [-0.00395, -0.00199] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | cheapest_eligible | +0.00357 [+0.00282, +0.00431] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | strongest_eligible | -0.00887 [-0.00991, -0.00784] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | random_eligible | -0.00756 [-0.00865, -0.00663] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | pilot | -0.01048 [-0.01140, -0.00935] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | stageroute | -0.00982 [-0.01135, -0.00838] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | cheapest_eligible | +0.00654 [+0.00623, +0.00682] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | strongest_eligible | -0.00591 [-0.00671, -0.00490] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | random_eligible | -0.00460 [-0.00542, -0.00392] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | pilot | -0.00752 [-0.00859, -0.00669] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | stageroute | -0.00686 [-0.00760, -0.00604] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | strongest_eligible | -0.01244 [-0.01310, -0.01160] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | random_eligible | -0.01113 [-0.01188, -0.01054] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | pilot | -0.01406 [-0.01486, -0.01338] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | stageroute | -0.01339 [-0.01433, -0.01238] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | pilot | -0.00161 [-0.00250, -0.00073] | 0.0000 | 0.0000 |
| cost_per_task | random_eligible | pilot | -0.00292 [-0.00411, -0.00196] | 0.0000 | 0.0000 |
| cost_per_task | random_eligible | stageroute | -0.00226 [-0.00364, -0.00065] | 0.0040 | 0.0160 |
| E | t5_logreg | cheapest_eligible | +0.03033 [+0.01692, +0.04378] | 0.0000 | 0.0000 |
| E | t5_logreg | strongest_eligible | -0.51826 [-0.60800, -0.43009] | 0.0000 | 0.0000 |
| E | t5_logreg | random_eligible | -0.10634 [-0.13514, -0.07373] | 0.0000 | 0.0000 |
| E | t5_logreg | pilot | -0.12119 [-0.14161, -0.10027] | 0.0000 | 0.0000 |
| E | t5_gbdt | cheapest_eligible | +0.10221 [+0.04851, +0.15387] | 0.0000 | 0.0000 |
| E | t5_gbdt | strongest_eligible | -0.44638 [-0.57396, -0.30438] | 0.0000 | 0.0000 |
| E | cheapest_eligible | strongest_eligible | -0.54859 [-0.64913, -0.44715] | 0.0000 | 0.0000 |
| E | cheapest_eligible | random_eligible | -0.13668 [-0.17819, -0.09243] | 0.0000 | 0.0000 |
| E | cheapest_eligible | pilot | -0.15152 [-0.17443, -0.12676] | 0.0000 | 0.0000 |
| E | cheapest_eligible | stageroute | -0.09180 [-0.14058, -0.04241] | 0.0022 | 0.0198 |
| E | strongest_eligible | random_eligible | +0.41191 [+0.33142, +0.50172] | 0.0000 | 0.0000 |
| E | strongest_eligible | pilot | +0.39707 [+0.30647, +0.47805] | 0.0000 | 0.0000 |
| E | strongest_eligible | stageroute | +0.45678 [+0.38253, +0.53103] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | cheapest_eligible | -0.01852 [-0.03148, -0.00556] | 0.0026 | 0.0234 |
| fill_rate | t5_logreg | strongest_eligible | +0.07037 [+0.05926, +0.08148] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | random_eligible | +0.06111 [+0.04815, +0.07407] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | stageroute | +0.07593 [+0.06296, +0.08704] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | strongest_eligible | +0.07778 [+0.06667, +0.08889] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | random_eligible | +0.06852 [+0.05556, +0.07963] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | stageroute | +0.08333 [+0.06667, +0.09444] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | strongest_eligible | +0.08889 [+0.08333, +0.09444] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | random_eligible | +0.07963 [+0.07407, +0.08519] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | stageroute | +0.09444 [+0.08519, +0.10370] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | random_eligible | -0.00926 [-0.01481, -0.00370] | 0.0026 | 0.0234 |
| fill_rate | strongest_eligible | pilot | -0.07963 [-0.08704, -0.07222] | 0.0000 | 0.0000 |
| fill_rate | random_eligible | pilot | -0.07037 [-0.07963, -0.06111] | 0.0000 | 0.0000 |
| fill_rate | random_eligible | stageroute | +0.01481 [+0.00556, +0.02407] | 0.0030 | 0.0234 |
| fill_rate | pilot | stageroute | +0.08519 [+0.07963, +0.09259] | 0.0000 | 0.0000 |

### pi = 0.1 (Required side table)

| Method | Family | Accuracy | Cost/task | Violation | E (fraud_share) | Fill rate | Oracle acc regret (side) | Oracle cost regret (side) |
|---|---|---|---|---|---|---|---|---|
| Two-stage LR (trained on logs) | trained_recommender | 0.5574 [0.5222, 0.6000] | 0.01144 [0.01073, 0.01233] | 0.0000 [0.0000, 0.0000] | 0.0303 [0.0169, 0.0438] | 0.9815 [0.9685, 0.9944] | 0.3759 [0.3333, 0.4111] | -0.01172 [-0.01331, -0.00985] |
| Two-stage GBDT (trained on logs) | trained_recommender | 0.6370 [0.5926, 0.6833] | 0.01441 [0.01392, 0.01489] | 0.0000 [0.0000, 0.0000] | 0.1022 [0.0485, 0.1539] | 0.9889 [0.9778, 0.9981] | 0.2963 [0.2481, 0.3407] | -0.00820 [-0.00898, -0.00748] |
| Cheapest eligible | untrained_baseline | 0.6093 [0.5852, 0.6352] | 0.00787 [0.00759, 0.00816] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 0.3241 [0.2981, 0.3481] | -0.00999 [-0.01063, -0.00935] |
| Strongest eligible | untrained_baseline | 0.5222 [0.4704, 0.5778] | 0.02031 [0.01955, 0.02102] | 0.0000 [0.0000, 0.0000] | 0.5506 [0.4513, 0.6497] | 0.9111 [0.9056, 0.9167] | 0.4111 [0.3556, 0.4630] | 0.00203 [0.00142, 0.00262] |
| Random eligible | untrained_baseline | 0.6259 [0.5944, 0.6500] | 0.01916 [0.01799, 0.02026] | 0.0000 [0.0000, 0.0000] | 0.1387 [0.1211, 0.1556] | 0.9222 [0.9111, 0.9333] | 0.3074 [0.2833, 0.3389] | 0.00143 [0.00012, 0.00273] |
| Market-adapted PILOT (pilot_v1) | untrained_baseline | 0.6630 [0.6278, 0.6963] | 0.02175 [0.02117, 0.02221] | 0.0000 [0.0000, 0.0000] | 0.2835 [0.2432, 0.3295] | 0.9796 [0.9685, 0.9889] | 0.2704 [0.2370, 0.3056] | 0.00290 [0.00168, 0.00413] |
| Market-adapted StageRoute (stageroute_v1) | untrained_baseline | 0.6648 [0.6222, 0.6981] | 0.01928 [0.01881, 0.01988] | 0.0000 [0.0000, 0.0000] | 0.1030 [0.0441, 0.1652] | 0.9167 [0.9074, 0.9241] | 0.2685 [0.2370, 0.3111] | 0.00146 [0.00054, 0.00241] |

Significant Holm-adjusted primary-metric pairs at pi=0.1 (p_Holm < 0.05, family size 21): **53**.

| Metric | Method A | Method B | Delta (A - B) [95% CI] | p_raw | p_Holm |
|---|---|---|---|---:|---:|
| accuracy | t5_logreg | random_eligible | -0.06852 [-0.10556, -0.02593] | 0.0002 | 0.0034 |
| accuracy | t5_logreg | pilot | -0.10556 [-0.15185, -0.05926] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | strongest_eligible | +0.11481 [+0.04815, +0.18519] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | pilot | -0.14074 [-0.19259, -0.08333] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | stageroute | -0.14259 [-0.19630, -0.09630] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | t5_gbdt | -0.00296 [-0.00397, -0.00197] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | cheapest_eligible | +0.00357 [+0.00283, +0.00432] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | strongest_eligible | -0.00887 [-0.00996, -0.00786] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | random_eligible | -0.00772 [-0.00846, -0.00692] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | pilot | -0.01031 [-0.01096, -0.00949] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | stageroute | -0.00783 [-0.00908, -0.00664] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | cheapest_eligible | +0.00654 [+0.00623, +0.00682] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | strongest_eligible | -0.00591 [-0.00671, -0.00490] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | random_eligible | -0.00476 [-0.00594, -0.00343] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | pilot | -0.00734 [-0.00795, -0.00646] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | stageroute | -0.00487 [-0.00521, -0.00455] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | strongest_eligible | -0.01244 [-0.01310, -0.01158] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | random_eligible | -0.01129 [-0.01229, -0.01013] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | pilot | -0.01388 [-0.01440, -0.01320] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | stageroute | -0.01141 [-0.01191, -0.01097] | 0.0000 | 0.0000 |
| cost_per_task | random_eligible | pilot | -0.00259 [-0.00351, -0.00173] | 0.0000 | 0.0000 |
| cost_per_task | pilot | stageroute | +0.00247 [+0.00135, +0.00318] | 0.0002 | 0.0010 |
| E | t5_logreg | cheapest_eligible | +0.03033 [+0.01692, +0.04376] | 0.0000 | 0.0000 |
| E | t5_logreg | strongest_eligible | -0.52029 [-0.61003, -0.43037] | 0.0000 | 0.0000 |
| E | t5_logreg | random_eligible | -0.10838 [-0.12565, -0.09093] | 0.0000 | 0.0000 |
| E | t5_logreg | pilot | -0.25322 [-0.30139, -0.20524] | 0.0000 | 0.0000 |
| E | t5_logreg | stageroute | -0.07266 [-0.12361, -0.02314] | 0.0000 | 0.0000 |
| E | t5_gbdt | cheapest_eligible | +0.10221 [+0.04720, +0.15202] | 0.0000 | 0.0000 |
| E | t5_gbdt | strongest_eligible | -0.44841 [-0.57396, -0.31451] | 0.0000 | 0.0000 |
| E | t5_gbdt | pilot | -0.18134 [-0.23152, -0.12628] | 0.0000 | 0.0000 |
| E | cheapest_eligible | strongest_eligible | -0.55062 [-0.64507, -0.45134] | 0.0000 | 0.0000 |
| E | cheapest_eligible | random_eligible | -0.13871 [-0.15562, -0.12115] | 0.0000 | 0.0000 |
| E | cheapest_eligible | pilot | -0.28355 [-0.33146, -0.24319] | 0.0000 | 0.0000 |
| E | cheapest_eligible | stageroute | -0.10299 [-0.16895, -0.04607] | 0.0000 | 0.0000 |
| E | strongest_eligible | random_eligible | +0.41191 [+0.31411, +0.51799] | 0.0000 | 0.0000 |
| E | strongest_eligible | pilot | +0.26707 [+0.17903, +0.34446] | 0.0000 | 0.0000 |
| E | strongest_eligible | stageroute | +0.44763 [+0.38638, +0.50653] | 0.0000 | 0.0000 |
| E | random_eligible | pilot | -0.14484 [-0.20440, -0.09317] | 0.0000 | 0.0000 |
| E | pilot | stageroute | +0.18056 [+0.10487, +0.25375] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | cheapest_eligible | -0.01852 [-0.03148, -0.00556] | 0.0010 | 0.0080 |
| fill_rate | t5_logreg | strongest_eligible | +0.07037 [+0.05926, +0.08333] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | random_eligible | +0.05926 [+0.04815, +0.07222] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | stageroute | +0.06481 [+0.04815, +0.08148] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | strongest_eligible | +0.07778 [+0.06667, +0.08889] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | random_eligible | +0.06667 [+0.05370, +0.07963] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | stageroute | +0.07222 [+0.05370, +0.08889] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | strongest_eligible | +0.08889 [+0.08333, +0.09444] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | random_eligible | +0.07778 [+0.06667, +0.08889] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | pilot | +0.02037 [+0.01111, +0.03148] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | stageroute | +0.08333 [+0.07407, +0.09259] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | pilot | -0.06852 [-0.07593, -0.06111] | 0.0000 | 0.0000 |
| fill_rate | random_eligible | pilot | -0.05741 [-0.06667, -0.04815] | 0.0000 | 0.0000 |
| fill_rate | pilot | stageroute | +0.06296 [+0.04815, +0.07778] | 0.0000 | 0.0000 |

### pi = 0 (Required side table)

| Method | Family | Accuracy | Cost/task | Violation | E (fraud_share) | Fill rate | Oracle acc regret (side) | Oracle cost regret (side) |
|---|---|---|---|---|---|---|---|---|
| Two-stage LR (trained on logs) | trained_recommender | 0.5574 [0.5222, 0.6000] | 0.01144 [0.01069, 0.01234] | 0.0000 [0.0000, 0.0000] | 0.0303 [0.0169, 0.0438] | 0.9815 [0.9685, 0.9944] | 0.3759 [0.3333, 0.4111] | -0.01174 [-0.01335, -0.00985] |
| Two-stage GBDT (trained on logs) | trained_recommender | 0.6370 [0.5926, 0.6852] | 0.01441 [0.01391, 0.01489] | 0.0000 [0.0000, 0.0000] | 0.1022 [0.0485, 0.1537] | 0.9889 [0.9778, 0.9981] | 0.2963 [0.2481, 0.3407] | -0.00820 [-0.00898, -0.00748] |
| Cheapest eligible | untrained_baseline | 0.6093 [0.5852, 0.6333] | 0.00787 [0.00759, 0.00816] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 0.3241 [0.3000, 0.3481] | -0.00999 [-0.01064, -0.00936] |
| Strongest eligible | untrained_baseline | 0.5241 [0.4704, 0.5778] | 0.02031 [0.01960, 0.02101] | 0.0000 [0.0000, 0.0000] | 0.5486 [0.4512, 0.6465] | 0.9111 [0.9056, 0.9167] | 0.4093 [0.3556, 0.4630] | 0.00203 [0.00140, 0.00262] |
| Random eligible | untrained_baseline | 0.6148 [0.5907, 0.6407] | 0.01903 [0.01820, 0.01984] | 0.0000 [0.0000, 0.0000] | 0.1507 [0.1209, 0.1865] | 0.9222 [0.9111, 0.9333] | 0.3185 [0.2907, 0.3426] | 0.00126 [0.00024, 0.00225] |
| Market-adapted PILOT (pilot_v1) | untrained_baseline | 0.5593 [0.4889, 0.6204] | 0.01977 [0.01919, 0.02039] | 0.0000 [0.0000, 0.0000] | 0.4630 [0.3610, 0.5726] | 0.9870 [0.9778, 0.9963] | 0.3741 [0.3167, 0.4444] | 0.00119 [0.00018, 0.00221] |
| Market-adapted StageRoute (stageroute_v1) | untrained_baseline | 0.6278 [0.5667, 0.6963] | 0.01824 [0.01649, 0.01988] | 0.0000 [0.0000, 0.0000] | 0.1148 [0.0446, 0.1850] | 0.9222 [0.9111, 0.9370] | 0.3056 [0.2370, 0.3667] | 0.00047 [-0.00143, 0.00223] |

Significant Holm-adjusted primary-metric pairs at pi=0 (p_Holm < 0.05, family size 21): **51**.

| Metric | Method A | Method B | Delta (A - B) [95% CI] | p_raw | p_Holm |
|---|---|---|---|---:|---:|
| accuracy | t5_gbdt | strongest_eligible | +0.11296 [+0.04630, +0.18519] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | random_eligible | -0.09074 [-0.14630, -0.03704] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | pilot | -0.03519 [-0.05000, -0.01852] | 0.0002 | 0.0036 |
| accuracy | strongest_eligible | stageroute | -0.10370 [-0.16481, -0.04630] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | t5_gbdt | -0.00296 [-0.00395, -0.00200] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | cheapest_eligible | +0.00357 [+0.00283, +0.00433] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | strongest_eligible | -0.00887 [-0.00997, -0.00785] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | random_eligible | -0.00758 [-0.00804, -0.00705] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | pilot | -0.00833 [-0.00898, -0.00764] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | stageroute | -0.00679 [-0.00885, -0.00489] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | cheapest_eligible | +0.00654 [+0.00625, +0.00682] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | strongest_eligible | -0.00591 [-0.00671, -0.00489] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | random_eligible | -0.00462 [-0.00557, -0.00367] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | pilot | -0.00537 [-0.00627, -0.00439] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | stageroute | -0.00383 [-0.00512, -0.00243] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | strongest_eligible | -0.01244 [-0.01308, -0.01160] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | random_eligible | -0.01116 [-0.01184, -0.01044] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | pilot | -0.01190 [-0.01261, -0.01113] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | stageroute | -0.01037 [-0.01190, -0.00875] | 0.0000 | 0.0000 |
| E | t5_logreg | cheapest_eligible | +0.03033 [+0.01690, +0.04378] | 0.0000 | 0.0000 |
| E | t5_logreg | strongest_eligible | -0.51826 [-0.60824, -0.42947] | 0.0000 | 0.0000 |
| E | t5_logreg | random_eligible | -0.12040 [-0.15224, -0.08793] | 0.0000 | 0.0000 |
| E | t5_logreg | pilot | -0.43264 [-0.53185, -0.34032] | 0.0000 | 0.0000 |
| E | t5_logreg | stageroute | -0.08450 [-0.14327, -0.02363] | 0.0028 | 0.0140 |
| E | t5_gbdt | cheapest_eligible | +0.10221 [+0.04687, +0.15202] | 0.0000 | 0.0000 |
| E | t5_gbdt | strongest_eligible | -0.44638 [-0.57038, -0.31237] | 0.0000 | 0.0000 |
| E | t5_gbdt | pilot | -0.36076 [-0.48574, -0.23038] | 0.0000 | 0.0000 |
| E | cheapest_eligible | strongest_eligible | -0.54859 [-0.64647, -0.44823] | 0.0000 | 0.0000 |
| E | cheapest_eligible | random_eligible | -0.15073 [-0.18682, -0.12092] | 0.0000 | 0.0000 |
| E | cheapest_eligible | pilot | -0.46297 [-0.56677, -0.36100] | 0.0000 | 0.0000 |
| E | cheapest_eligible | stageroute | -0.11483 [-0.18501, -0.04472] | 0.0000 | 0.0000 |
| E | strongest_eligible | random_eligible | +0.39786 [+0.30961, +0.48697] | 0.0000 | 0.0000 |
| E | strongest_eligible | pilot | +0.08562 [+0.06737, +0.10569] | 0.0000 | 0.0000 |
| E | strongest_eligible | stageroute | +0.43376 [+0.35209, +0.53651] | 0.0000 | 0.0000 |
| E | random_eligible | pilot | -0.31224 [-0.41069, -0.22831] | 0.0000 | 0.0000 |
| E | pilot | stageroute | +0.34814 [+0.27319, +0.45551] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | cheapest_eligible | -0.01852 [-0.03148, -0.00556] | 0.0034 | 0.0272 |
| fill_rate | t5_logreg | strongest_eligible | +0.07037 [+0.05926, +0.08333] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | random_eligible | +0.05926 [+0.04815, +0.07222] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | stageroute | +0.05926 [+0.04815, +0.07222] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | strongest_eligible | +0.07778 [+0.06667, +0.08889] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | random_eligible | +0.06667 [+0.05185, +0.08148] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | stageroute | +0.06667 [+0.05185, +0.08148] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | strongest_eligible | +0.08889 [+0.08333, +0.09444] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | random_eligible | +0.07778 [+0.06667, +0.08889] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | pilot | +0.01296 [+0.00370, +0.02222] | 0.0028 | 0.0252 |
| fill_rate | cheapest_eligible | stageroute | +0.07778 [+0.06296, +0.09074] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | random_eligible | -0.01111 [-0.02037, -0.00370] | 0.0038 | 0.0272 |
| fill_rate | strongest_eligible | pilot | -0.07593 [-0.08333, -0.06852] | 0.0000 | 0.0000 |
| fill_rate | random_eligible | pilot | -0.06481 [-0.07037, -0.05926] | 0.0000 | 0.0000 |
| fill_rate | pilot | stageroute | +0.06481 [+0.05556, +0.07222] | 0.0000 | 0.0000 |

