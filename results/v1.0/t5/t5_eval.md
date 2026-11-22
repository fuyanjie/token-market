# Official T5 Readout (docs/PROTOCOL_T5.md, frozen 2026-11-22)

- Protocol sha256: `4301f4b281e90b1b835d1e7868e3b00c98bc8eaee382cf29f8646c6fa7272542`
- `configs/v1.0/scale.yaml` sha256: `780e9b961d89bad6fd520c9cbfd5710055ff2d5d3e0ff3bcfbd745709eb0da6c`
- Fixed audit (v1.0 default): `audit_rate=0.1`, `audit_rule=fixed`, `audit_checks=['identity', 'length']`, `trust_feedback=False`, `audit_v11=off`; train mean `n_audits=43.43` (realised rate `0.0982`); eval mean `n_audits=45.18` (min `35`, max `56`, realised rate `0.1003`).
- Train seeds: `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]` (inner fit `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]`, inner val `[10, 11, 12, 13]`); Test seeds: `[14, 15, 16, 17, 18, 19]` (**n = 6 test runs**, NOT 20).
- Bootstrap: B = 10000, 95% percentile CIs, paired two-sided bootstrap p-values, Holm within each (pi, metric) over all 21 pairs of the 7 official methods (alpha = 0.05).
- Leakage check passed: `True` (5017 train rows, 0 offenders).
- Hold-out prompts: 15 unique prompt hashes drawn via `random.Random('t5-prompt-holdout-20261122')` (excluded from training and tau selection).

## Frozen tau selection (inner val seeds [10, 11, 12, 13], non-holdout tasks only)

| learner | selected tau | floor_rule_triggered | strongest val acc | chosen val acc | chosen val cost/task |
|---|---:|---|---:|---:|---:|
| Two-stage LOGREG | 0.90 | True | 0.8006 | 0.7929 | 0.02498 |
| Two-stage GBDT | 0.90 | False | 0.8006 | 0.8231 | 0.02666 |

## Main & pi side tables (ALL test tasks, seeds [14, 15, 16, 17, 18, 19], n=6)

### pi = 1 (Main table)

| Method | Family | Accuracy | Cost/task | Violation | E (fraud_share) | Fill rate | Oracle acc regret (side) | Oracle cost regret (side) |
|---|---|---|---|---|---|---|---|---|
| Two-stage LR (trained on logs) | trained_recommender | 0.7920 [0.7771, 0.8062] | 0.02387 [0.02370, 0.02404] | 0.0000 [0.0000, 0.0000] | 0.0113 [0.0049, 0.0193] | 0.9163 [0.9108, 0.9215] | 0.1705 [0.1563, 0.1851] | 0.00898 [0.00861, 0.00932] |
| Two-stage GBDT (trained on logs) | trained_recommender | 0.8118 [0.8000, 0.8229] | 0.02800 [0.02749, 0.02854] | 0.0000 [0.0000, 0.0000] | 0.0319 [0.0192, 0.0458] | 0.9028 [0.8986, 0.9066] | 0.1507 [0.1396, 0.1625] | 0.01210 [0.01070, 0.01352] |
| Cheapest eligible | untrained_baseline | 0.6229 [0.6062, 0.6361] | 0.00851 [0.00799, 0.00901] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 0.3396 [0.3264, 0.3559] | -0.00846 [-0.00930, -0.00764] |
| Strongest eligible | untrained_baseline | 0.8035 [0.7872, 0.8194] | 0.02286 [0.02219, 0.02351] | 0.0000 [0.0000, 0.0000] | 0.1048 [0.0653, 0.1423] | 0.9174 [0.9149, 0.9201] | 0.1590 [0.1431, 0.1757] | 0.00541 [0.00475, 0.00602] |
| Random eligible | untrained_baseline | 0.7198 [0.7083, 0.7312] | 0.02160 [0.02113, 0.02204] | 0.0000 [0.0000, 0.0000] | 0.0916 [0.0822, 0.1020] | 0.9292 [0.9236, 0.9344] | 0.2427 [0.2306, 0.2542] | 0.00478 [0.00426, 0.00514] |
| Market-adapted PILOT (pilot_v1) | untrained_baseline | 0.7896 [0.7802, 0.8000] | 0.02468 [0.02458, 0.02479] | 0.0000 [0.0000, 0.0000] | 0.1212 [0.1098, 0.1325] | 0.9830 [0.9760, 0.9899] | 0.1729 [0.1628, 0.1823] | 0.00818 [0.00763, 0.00885] |
| Market-adapted StageRoute (stageroute_v1) | untrained_baseline | 0.7681 [0.7490, 0.7889] | 0.02435 [0.02318, 0.02544] | 0.0000 [0.0000, 0.0000] | 0.0474 [0.0217, 0.0732] | 0.9149 [0.9076, 0.9215] | 0.1944 [0.1733, 0.2139] | 0.00727 [0.00557, 0.00871] |

Significant Holm-adjusted primary-metric pairs at pi=1 (p_Holm < 0.05, family size 21): **67**.

| Metric | Method A | Method B | Delta (A - B) [95% CI] | p_raw | p_Holm |
|---|---|---|---|---:|---:|
| accuracy | t5_logreg | cheapest_eligible | +0.16910 [+0.14896, +0.19097] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | random_eligible | +0.07222 [+0.05972, +0.08403] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | cheapest_eligible | +0.18889 [+0.17292, +0.20729] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | random_eligible | +0.09201 [+0.07500, +0.11076] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | pilot | +0.02222 [+0.01667, +0.02813] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | stageroute | +0.04375 [+0.01736, +0.07014] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | strongest_eligible | -0.18056 [-0.20972, -0.15729] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | random_eligible | -0.09687 [-0.11806, -0.07674] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | pilot | -0.16667 [-0.17986, -0.15451] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | stageroute | -0.14514 [-0.17986, -0.11875] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | random_eligible | +0.08368 [+0.06319, +0.10694] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | stageroute | +0.03542 [+0.01319, +0.05556] | 0.0024 | 0.0192 |
| accuracy | random_eligible | pilot | -0.06979 [-0.08472, -0.05590] | 0.0000 | 0.0000 |
| accuracy | random_eligible | stageroute | -0.04826 [-0.07049, -0.02535] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | t5_gbdt | -0.00413 [-0.00474, -0.00360] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | cheapest_eligible | +0.01536 [+0.01482, +0.01597] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | strongest_eligible | +0.00102 [+0.00027, +0.00173] | 0.0060 | 0.0180 |
| cost_per_task | t5_logreg | random_eligible | +0.00227 [+0.00171, +0.00287] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | pilot | -0.00081 [-0.00104, -0.00065] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | cheapest_eligible | +0.01949 [+0.01874, +0.02030] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | strongest_eligible | +0.00515 [+0.00475, +0.00556] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | random_eligible | +0.00640 [+0.00582, +0.00719] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | pilot | +0.00332 [+0.00285, +0.00377] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | stageroute | +0.00366 [+0.00262, +0.00482] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | strongest_eligible | -0.01434 [-0.01510, -0.01353] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | random_eligible | -0.01309 [-0.01346, -0.01273] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | pilot | -0.01617 [-0.01678, -0.01558] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | stageroute | -0.01583 [-0.01678, -0.01499] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | random_eligible | +0.00126 [+0.00060, +0.00184] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | pilot | -0.00183 [-0.00246, -0.00122] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | stageroute | -0.00149 [-0.00262, -0.00040] | 0.0026 | 0.0104 |
| cost_per_task | random_eligible | pilot | -0.00309 [-0.00359, -0.00263] | 0.0000 | 0.0000 |
| cost_per_task | random_eligible | stageroute | -0.00275 [-0.00357, -0.00184] | 0.0000 | 0.0000 |
| E | t5_logreg | cheapest_eligible | +0.01134 [+0.00494, +0.01926] | 0.0000 | 0.0000 |
| E | t5_logreg | strongest_eligible | -0.09343 [-0.13108, -0.05304] | 0.0000 | 0.0000 |
| E | t5_logreg | random_eligible | -0.08023 [-0.08966, -0.07153] | 0.0000 | 0.0000 |
| E | t5_logreg | pilot | -0.10982 [-0.12459, -0.09695] | 0.0000 | 0.0000 |
| E | t5_gbdt | cheapest_eligible | +0.03194 [+0.01924, +0.04622] | 0.0000 | 0.0000 |
| E | t5_gbdt | strongest_eligible | -0.07283 [-0.11531, -0.03047] | 0.0000 | 0.0000 |
| E | t5_gbdt | random_eligible | -0.05963 [-0.07726, -0.04068] | 0.0000 | 0.0000 |
| E | t5_gbdt | pilot | -0.08923 [-0.10388, -0.07469] | 0.0000 | 0.0000 |
| E | cheapest_eligible | strongest_eligible | -0.10478 [-0.14242, -0.06415] | 0.0000 | 0.0000 |
| E | cheapest_eligible | random_eligible | -0.09157 [-0.10170, -0.08253] | 0.0000 | 0.0000 |
| E | cheapest_eligible | pilot | -0.12117 [-0.13254, -0.10978] | 0.0000 | 0.0000 |
| E | cheapest_eligible | stageroute | -0.04742 [-0.07298, -0.02166] | 0.0034 | 0.0204 |
| E | strongest_eligible | stageroute | +0.05736 [+0.03600, +0.07600] | 0.0000 | 0.0000 |
| E | random_eligible | pilot | -0.02960 [-0.04667, -0.01532] | 0.0000 | 0.0000 |
| E | random_eligible | stageroute | +0.04415 [+0.01353, +0.07833] | 0.0000 | 0.0000 |
| E | pilot | stageroute | +0.07375 [+0.04468, +0.10373] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | t5_gbdt | +0.01354 [+0.00764, +0.01910] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | cheapest_eligible | -0.08368 [-0.08924, -0.07847] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | random_eligible | -0.01285 [-0.02014, -0.00556] | 0.0040 | 0.0200 |
| fill_rate | t5_logreg | pilot | -0.06667 [-0.07465, -0.05972] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | cheapest_eligible | -0.09722 [-0.10139, -0.09340] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | strongest_eligible | -0.01458 [-0.01840, -0.01111] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | random_eligible | -0.02639 [-0.03403, -0.01840] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | pilot | -0.08021 [-0.08507, -0.07465] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | stageroute | -0.01215 [-0.02222, -0.00382] | 0.0096 | 0.0384 |
| fill_rate | cheapest_eligible | strongest_eligible | +0.08264 [+0.07986, +0.08507] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | random_eligible | +0.07083 [+0.06562, +0.07639] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | pilot | +0.01701 [+0.01007, +0.02465] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | stageroute | +0.08507 [+0.07847, +0.09167] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | random_eligible | -0.01181 [-0.01736, -0.00625] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | pilot | -0.06563 [-0.07326, -0.05799] | 0.0000 | 0.0000 |
| fill_rate | random_eligible | pilot | -0.05382 [-0.06632, -0.04236] | 0.0000 | 0.0000 |
| fill_rate | random_eligible | stageroute | +0.01424 [+0.00694, +0.02188] | 0.0000 | 0.0000 |
| fill_rate | pilot | stageroute | +0.06806 [+0.05556, +0.07951] | 0.0000 | 0.0000 |

### pi = 0.1 (Required side table)

| Method | Family | Accuracy | Cost/task | Violation | E (fraud_share) | Fill rate | Oracle acc regret (side) | Oracle cost regret (side) |
|---|---|---|---|---|---|---|---|---|
| Two-stage LR (trained on logs) | trained_recommender | 0.7920 [0.7774, 0.8062] | 0.02387 [0.02370, 0.02404] | 0.0000 [0.0000, 0.0000] | 0.0113 [0.0049, 0.0193] | 0.9163 [0.9108, 0.9215] | 0.1705 [0.1566, 0.1854] | 0.00898 [0.00861, 0.00931] |
| Two-stage GBDT (trained on logs) | trained_recommender | 0.8118 [0.8000, 0.8233] | 0.02800 [0.02749, 0.02853] | 0.0000 [0.0000, 0.0000] | 0.0319 [0.0193, 0.0462] | 0.9028 [0.8986, 0.9066] | 0.1507 [0.1392, 0.1625] | 0.01210 [0.01070, 0.01352] |
| Cheapest eligible | untrained_baseline | 0.6229 [0.6066, 0.6361] | 0.00851 [0.00800, 0.00901] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 0.3396 [0.3264, 0.3559] | -0.00846 [-0.00931, -0.00764] |
| Strongest eligible | untrained_baseline | 0.8042 [0.7875, 0.8201] | 0.02284 [0.02216, 0.02349] | 0.0000 [0.0000, 0.0000] | 0.1040 [0.0650, 0.1415] | 0.9174 [0.9149, 0.9201] | 0.1583 [0.1424, 0.1750] | 0.00540 [0.00479, 0.00602] |
| Random eligible | untrained_baseline | 0.7038 [0.6917, 0.7139] | 0.02103 [0.02027, 0.02170] | 0.0000 [0.0000, 0.0000] | 0.1046 [0.0943, 0.1149] | 0.9260 [0.9188, 0.9323] | 0.2587 [0.2486, 0.2705] | 0.00406 [0.00321, 0.00493] |
| Market-adapted PILOT (pilot_v1) | untrained_baseline | 0.7830 [0.7684, 0.7965] | 0.02507 [0.02471, 0.02542] | 0.0000 [0.0000, 0.0000] | 0.1559 [0.1430, 0.1688] | 0.9799 [0.9747, 0.9851] | 0.1795 [0.1660, 0.1938] | 0.00689 [0.00603, 0.00768] |
| Market-adapted StageRoute (stageroute_v1) | untrained_baseline | 0.7434 [0.7139, 0.7712] | 0.02210 [0.02129, 0.02292] | 0.0000 [0.0000, 0.0000] | 0.0596 [0.0233, 0.1019] | 0.9271 [0.9198, 0.9323] | 0.2191 [0.1913, 0.2479] | 0.00510 [0.00397, 0.00624] |

Significant Holm-adjusted primary-metric pairs at pi=0.1 (p_Holm < 0.05, family size 21): **70**.

| Metric | Method A | Method B | Delta (A - B) [95% CI] | p_raw | p_Holm |
|---|---|---|---|---:|---:|
| accuracy | t5_logreg | cheapest_eligible | +0.16910 [+0.14896, +0.19097] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | random_eligible | +0.08819 [+0.06597, +0.11217] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | stageroute | +0.04861 [+0.01875, +0.08194] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | cheapest_eligible | +0.18889 [+0.17292, +0.20729] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | random_eligible | +0.10799 [+0.08958, +0.12257] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | pilot | +0.02882 [+0.00764, +0.05278] | 0.0054 | 0.0378 |
| accuracy | t5_gbdt | stageroute | +0.06840 [+0.03056, +0.10764] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | strongest_eligible | -0.18125 [-0.20972, -0.15729] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | random_eligible | -0.08090 [-0.10000, -0.06424] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | pilot | -0.16007 [-0.17431, -0.14375] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | stageroute | -0.12049 [-0.15833, -0.08056] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | random_eligible | +0.10035 [+0.07882, +0.12257] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | stageroute | +0.06076 [+0.03368, +0.08438] | 0.0000 | 0.0000 |
| accuracy | random_eligible | pilot | -0.07917 [-0.09688, -0.06146] | 0.0000 | 0.0000 |
| accuracy | pilot | stageroute | +0.03958 [+0.01250, +0.07292] | 0.0006 | 0.0048 |
| cost_per_task | t5_logreg | t5_gbdt | -0.00413 [-0.00471, -0.00360] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | cheapest_eligible | +0.01536 [+0.01484, +0.01597] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | strongest_eligible | +0.00103 [+0.00027, +0.00175] | 0.0060 | 0.0180 |
| cost_per_task | t5_logreg | random_eligible | +0.00285 [+0.00219, +0.00360] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | pilot | -0.00119 [-0.00155, -0.00083] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | stageroute | +0.00177 [+0.00084, +0.00264] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | cheapest_eligible | +0.01949 [+0.01873, +0.02032] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | strongest_eligible | +0.00516 [+0.00473, +0.00559] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | random_eligible | +0.00698 [+0.00618, +0.00775] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | pilot | +0.00294 [+0.00228, +0.00361] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | stageroute | +0.00590 [+0.00521, +0.00664] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | strongest_eligible | -0.01433 [-0.01505, -0.01353] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | random_eligible | -0.01252 [-0.01291, -0.01208] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | pilot | -0.01656 [-0.01715, -0.01587] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | stageroute | -0.01359 [-0.01447, -0.01254] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | random_eligible | +0.00181 [+0.00096, +0.00262] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | pilot | -0.00223 [-0.00283, -0.00151] | 0.0000 | 0.0000 |
| cost_per_task | random_eligible | pilot | -0.00404 [-0.00490, -0.00329] | 0.0000 | 0.0000 |
| cost_per_task | pilot | stageroute | +0.00297 [+0.00188, +0.00405] | 0.0000 | 0.0000 |
| E | t5_logreg | cheapest_eligible | +0.01134 [+0.00494, +0.01926] | 0.0000 | 0.0000 |
| E | t5_logreg | strongest_eligible | -0.09268 [-0.12982, -0.05248] | 0.0000 | 0.0000 |
| E | t5_logreg | random_eligible | -0.09330 [-0.10483, -0.08257] | 0.0000 | 0.0000 |
| E | t5_logreg | pilot | -0.14460 [-0.15732, -0.13188] | 0.0000 | 0.0000 |
| E | t5_logreg | stageroute | -0.04828 [-0.08959, -0.01313] | 0.0000 | 0.0000 |
| E | t5_gbdt | cheapest_eligible | +0.03194 [+0.01885, +0.04622] | 0.0000 | 0.0000 |
| E | t5_gbdt | strongest_eligible | -0.07208 [-0.11509, -0.02971] | 0.0000 | 0.0000 |
| E | t5_gbdt | random_eligible | -0.07270 [-0.08937, -0.05897] | 0.0000 | 0.0000 |
| E | t5_gbdt | pilot | -0.12400 [-0.14810, -0.09896] | 0.0000 | 0.0000 |
| E | cheapest_eligible | strongest_eligible | -0.10402 [-0.14150, -0.06372] | 0.0000 | 0.0000 |
| E | cheapest_eligible | random_eligible | -0.10464 [-0.11485, -0.09416] | 0.0000 | 0.0000 |
| E | cheapest_eligible | pilot | -0.15594 [-0.16841, -0.14261] | 0.0000 | 0.0000 |
| E | cheapest_eligible | stageroute | -0.05962 [-0.10186, -0.02331] | 0.0000 | 0.0000 |
| E | strongest_eligible | pilot | -0.05192 [-0.09170, -0.01496] | 0.0026 | 0.0130 |
| E | strongest_eligible | stageroute | +0.04440 [+0.02350, +0.06833] | 0.0000 | 0.0000 |
| E | random_eligible | pilot | -0.05130 [-0.07224, -0.03056] | 0.0000 | 0.0000 |
| E | pilot | stageroute | +0.09632 [+0.06159, +0.12864] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | t5_gbdt | +0.01354 [+0.00764, +0.01910] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | cheapest_eligible | -0.08368 [-0.08924, -0.07847] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | random_eligible | -0.00972 [-0.01667, -0.00382] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | pilot | -0.06354 [-0.07292, -0.05417] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | stageroute | -0.01076 [-0.01667, -0.00521] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | cheapest_eligible | -0.09722 [-0.10139, -0.09340] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | strongest_eligible | -0.01458 [-0.01840, -0.01111] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | random_eligible | -0.02326 [-0.03229, -0.01424] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | pilot | -0.07708 [-0.08264, -0.07049] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | stageroute | -0.02431 [-0.03229, -0.01562] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | strongest_eligible | +0.08264 [+0.08021, +0.08507] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | random_eligible | +0.07396 [+0.06771, +0.08090] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | pilot | +0.02014 [+0.01493, +0.02535] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | stageroute | +0.07292 [+0.06805, +0.08021] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | random_eligible | -0.00868 [-0.01458, -0.00243] | 0.0058 | 0.0232 |
| fill_rate | strongest_eligible | pilot | -0.06250 [-0.06701, -0.05799] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | stageroute | -0.00972 [-0.01667, -0.00208] | 0.0120 | 0.0360 |
| fill_rate | random_eligible | pilot | -0.05382 [-0.06354, -0.04583] | 0.0000 | 0.0000 |
| fill_rate | pilot | stageroute | +0.05278 [+0.04410, +0.06389] | 0.0000 | 0.0000 |

### pi = 0 (Required side table)

| Method | Family | Accuracy | Cost/task | Violation | E (fraud_share) | Fill rate | Oracle acc regret (side) | Oracle cost regret (side) |
|---|---|---|---|---|---|---|---|---|
| Two-stage LR (trained on logs) | trained_recommender | 0.7920 [0.7778, 0.8056] | 0.02387 [0.02370, 0.02404] | 0.0000 [0.0000, 0.0000] | 0.0113 [0.0049, 0.0193] | 0.9163 [0.9108, 0.9215] | 0.1705 [0.1566, 0.1851] | 0.00898 [0.00861, 0.00932] |
| Two-stage GBDT (trained on logs) | trained_recommender | 0.8118 [0.8000, 0.8233] | 0.02800 [0.02748, 0.02854] | 0.0000 [0.0000, 0.0000] | 0.0319 [0.0189, 0.0462] | 0.9028 [0.8986, 0.9066] | 0.1507 [0.1392, 0.1625] | 0.01210 [0.01070, 0.01354] |
| Cheapest eligible | untrained_baseline | 0.6229 [0.6066, 0.6361] | 0.00851 [0.00800, 0.00901] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 0.3396 [0.3264, 0.3559] | -0.00846 [-0.00929, -0.00764] |
| Strongest eligible | untrained_baseline | 0.8035 [0.7868, 0.8194] | 0.02286 [0.02220, 0.02350] | 0.0000 [0.0000, 0.0000] | 0.1048 [0.0657, 0.1423] | 0.9174 [0.9149, 0.9198] | 0.1590 [0.1427, 0.1750] | 0.00541 [0.00476, 0.00605] |
| Random eligible | untrained_baseline | 0.7073 [0.6958, 0.7174] | 0.02141 [0.02090, 0.02190] | 0.0000 [0.0000, 0.0000] | 0.0959 [0.0890, 0.1038] | 0.9316 [0.9236, 0.9406] | 0.2552 [0.2451, 0.2667] | 0.00437 [0.00384, 0.00490] |
| Market-adapted PILOT (pilot_v1) | untrained_baseline | 0.8403 [0.8184, 0.8608] | 0.02217 [0.02168, 0.02265] | 0.0000 [0.0000, 0.0000] | 0.0987 [0.0586, 0.1389] | 0.9844 [0.9809, 0.9875] | 0.1222 [0.1017, 0.1451] | 0.00448 [0.00353, 0.00510] |
| Market-adapted StageRoute (stageroute_v1) | untrained_baseline | 0.7333 [0.7101, 0.7573] | 0.02086 [0.01955, 0.02219] | 0.0000 [0.0000, 0.0000] | 0.0446 [0.0207, 0.0665] | 0.9292 [0.9177, 0.9385] | 0.2292 [0.2049, 0.2524] | 0.00390 [0.00237, 0.00547] |

Significant Holm-adjusted primary-metric pairs at pi=0 (p_Holm < 0.05, family size 21): **70**.

| Metric | Method A | Method B | Delta (A - B) [95% CI] | p_raw | p_Holm |
|---|---|---|---|---:|---:|
| accuracy | t5_logreg | t5_gbdt | -0.01979 [-0.04063, -0.00417] | 0.0066 | 0.0330 |
| accuracy | t5_logreg | cheapest_eligible | +0.16910 [+0.14896, +0.19097] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | random_eligible | +0.08472 [+0.07014, +0.09583] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | pilot | -0.04826 [-0.06944, -0.02290] | 0.0002 | 0.0012 |
| accuracy | t5_logreg | stageroute | +0.05868 [+0.02986, +0.08819] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | cheapest_eligible | +0.18889 [+0.17292, +0.20729] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | random_eligible | +0.10451 [+0.08264, +0.12639] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | stageroute | +0.07847 [+0.04931, +0.10903] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | strongest_eligible | -0.18056 [-0.20972, -0.15729] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | random_eligible | -0.08437 [-0.10451, -0.06528] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | pilot | -0.21736 [-0.24653, -0.18889] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | stageroute | -0.11042 [-0.14340, -0.08264] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | random_eligible | +0.09618 [+0.07674, +0.11389] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | pilot | -0.03681 [-0.05417, -0.02292] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | stageroute | +0.07014 [+0.04722, +0.09410] | 0.0000 | 0.0000 |
| accuracy | random_eligible | pilot | -0.13299 [-0.15208, -0.11493] | 0.0000 | 0.0000 |
| accuracy | pilot | stageroute | +0.10694 [+0.09618, +0.12292] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | t5_gbdt | -0.00413 [-0.00471, -0.00361] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | cheapest_eligible | +0.01536 [+0.01482, +0.01593] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | strongest_eligible | +0.00102 [+0.00027, +0.00173] | 0.0068 | 0.0272 |
| cost_per_task | t5_logreg | random_eligible | +0.00246 [+0.00199, +0.00298] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | pilot | +0.00170 [+0.00114, +0.00225] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | stageroute | +0.00301 [+0.00157, +0.00440] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | cheapest_eligible | +0.01949 [+0.01872, +0.02028] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | strongest_eligible | +0.00515 [+0.00474, +0.00556] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | random_eligible | +0.00659 [+0.00591, +0.00728] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | pilot | +0.00583 [+0.00543, +0.00620] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | stageroute | +0.00714 [+0.00594, +0.00848] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | strongest_eligible | -0.01434 [-0.01510, -0.01353] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | random_eligible | -0.01290 [-0.01317, -0.01266] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | pilot | -0.01366 [-0.01425, -0.01299] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | stageroute | -0.01235 [-0.01358, -0.01126] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | random_eligible | +0.00145 [+0.00075, +0.00210] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | pilot | +0.00068 [+0.00050, +0.00088] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | stageroute | +0.00199 [+0.00065, +0.00321] | 0.0012 | 0.0060 |
| cost_per_task | random_eligible | pilot | -0.00076 [-0.00125, -0.00021] | 0.0080 | 0.0272 |
| E | t5_logreg | cheapest_eligible | +0.01134 [+0.00495, +0.01961] | 0.0000 | 0.0000 |
| E | t5_logreg | strongest_eligible | -0.09343 [-0.13108, -0.05387] | 0.0000 | 0.0000 |
| E | t5_logreg | random_eligible | -0.08454 [-0.08917, -0.07813] | 0.0000 | 0.0000 |
| E | t5_logreg | pilot | -0.08737 [-0.12606, -0.04806] | 0.0000 | 0.0000 |
| E | t5_logreg | stageroute | -0.03330 [-0.05407, -0.01034] | 0.0066 | 0.0396 |
| E | t5_gbdt | cheapest_eligible | +0.03194 [+0.01924, +0.04626] | 0.0000 | 0.0000 |
| E | t5_gbdt | strongest_eligible | -0.07283 [-0.11520, -0.03047] | 0.0000 | 0.0000 |
| E | t5_gbdt | random_eligible | -0.06394 [-0.08316, -0.04698] | 0.0000 | 0.0000 |
| E | t5_gbdt | pilot | -0.06677 [-0.11580, -0.02153] | 0.0000 | 0.0000 |
| E | cheapest_eligible | strongest_eligible | -0.10478 [-0.14225, -0.06372] | 0.0000 | 0.0000 |
| E | cheapest_eligible | random_eligible | -0.09588 [-0.10380, -0.08904] | 0.0000 | 0.0000 |
| E | cheapest_eligible | pilot | -0.09871 [-0.13890, -0.05863] | 0.0000 | 0.0000 |
| E | cheapest_eligible | stageroute | -0.04464 [-0.06654, -0.02073] | 0.0000 | 0.0000 |
| E | strongest_eligible | stageroute | +0.06013 [+0.03704, +0.08355] | 0.0000 | 0.0000 |
| E | random_eligible | stageroute | +0.05124 [+0.03334, +0.06951] | 0.0000 | 0.0000 |
| E | pilot | stageroute | +0.05407 [+0.03242, +0.07592] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | t5_gbdt | +0.01354 [+0.00764, +0.01944] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | cheapest_eligible | -0.08368 [-0.08924, -0.07847] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | random_eligible | -0.01528 [-0.02222, -0.00694] | 0.0002 | 0.0010 |
| fill_rate | t5_logreg | pilot | -0.06806 [-0.07604, -0.05972] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | stageroute | -0.01285 [-0.02014, -0.00521] | 0.0006 | 0.0024 |
| fill_rate | t5_gbdt | cheapest_eligible | -0.09722 [-0.10139, -0.09340] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | strongest_eligible | -0.01458 [-0.01840, -0.01111] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | random_eligible | -0.02882 [-0.03958, -0.01910] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | pilot | -0.08160 [-0.08646, -0.07708] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | stageroute | -0.02639 [-0.03681, -0.01389] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | strongest_eligible | +0.08264 [+0.08021, +0.08507] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | random_eligible | +0.06840 [+0.05903, +0.07639] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | pilot | +0.01562 [+0.01285, +0.01910] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | stageroute | +0.07083 [+0.06146, +0.08229] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | random_eligible | -0.01424 [-0.02292, -0.00694] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | pilot | -0.06701 [-0.07188, -0.06215] | 0.0000 | 0.0000 |
| fill_rate | random_eligible | pilot | -0.05278 [-0.06285, -0.04097] | 0.0000 | 0.0000 |
| fill_rate | pilot | stageroute | +0.05521 [+0.04306, +0.06910] | 0.0000 | 0.0000 |


## Unique-prompt hold-out side tables (15 hold-out prompt hashes, seeds [14, 15, 16, 17, 18, 19], n=6)

### pi = 1 (Required side table)

| Method | Family | Accuracy | Cost/task | Violation | E (fraud_share) | Fill rate | Oracle acc regret (side) | Oracle cost regret (side) |
|---|---|---|---|---|---|---|---|---|
| Two-stage LR (trained on logs) | trained_recommender | 0.7852 [0.7648, 0.8056] | 0.02076 [0.02035, 0.02116] | 0.0000 [0.0000, 0.0000] | 0.0122 [0.0061, 0.0182] | 0.9074 [0.9019, 0.9148] | 0.1481 [0.1278, 0.1685] | 0.00465 [0.00413, 0.00518] |
| Two-stage GBDT (trained on logs) | trained_recommender | 0.7519 [0.7333, 0.7667] | 0.02556 [0.02501, 0.02608] | 0.0000 [0.0000, 0.0000] | 0.0267 [0.0104, 0.0452] | 0.8981 [0.8907, 0.9074] | 0.1815 [0.1667, 0.2000] | 0.00876 [0.00752, 0.01011] |
| Cheapest eligible | untrained_baseline | 0.6093 [0.5852, 0.6334] | 0.00829 [0.00795, 0.00862] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 0.3241 [0.3000, 0.3481] | -0.00949 [-0.01014, -0.00881] |
| Strongest eligible | untrained_baseline | 0.7370 [0.7093, 0.7630] | 0.02052 [0.01984, 0.02119] | 0.0000 [0.0000, 0.0000] | 0.1178 [0.0960, 0.1379] | 0.9111 [0.9037, 0.9185] | 0.1963 [0.1704, 0.2222] | 0.00232 [0.00160, 0.00292] |
| Random eligible | untrained_baseline | 0.6519 [0.6333, 0.6667] | 0.01932 [0.01856, 0.02011] | 0.0000 [0.0000, 0.0000] | 0.0965 [0.0687, 0.1207] | 0.9222 [0.9148, 0.9296] | 0.2815 [0.2667, 0.3000] | 0.00171 [0.00093, 0.00253] |
| Market-adapted PILOT (pilot_v1) | untrained_baseline | 0.7648 [0.7519, 0.7852] | 0.02217 [0.02184, 0.02259] | 0.0000 [0.0000, 0.0000] | 0.1207 [0.1040, 0.1384] | 0.9815 [0.9648, 0.9944] | 0.1685 [0.1481, 0.1815] | 0.00483 [0.00404, 0.00556] |
| Market-adapted StageRoute (stageroute_v1) | untrained_baseline | 0.6889 [0.6648, 0.7111] | 0.02172 [0.02066, 0.02277] | 0.0000 [0.0000, 0.0000] | 0.0448 [0.0163, 0.0732] | 0.9056 [0.8963, 0.9148] | 0.2444 [0.2222, 0.2685] | 0.00389 [0.00236, 0.00527] |

Significant Holm-adjusted primary-metric pairs at pi=1 (p_Holm < 0.05, family size 21): **60**.

| Metric | Method A | Method B | Delta (A - B) [95% CI] | p_raw | p_Holm |
|---|---|---|---|---:|---:|
| accuracy | t5_logreg | cheapest_eligible | +0.17593 [+0.14444, +0.20556] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | random_eligible | +0.13333 [+0.10370, +0.16852] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | stageroute | +0.09630 [+0.06481, +0.12963] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | cheapest_eligible | +0.14259 [+0.10741, +0.17407] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | random_eligible | +0.10000 [+0.07407, +0.12407] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | stageroute | +0.06296 [+0.02778, +0.09815] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | strongest_eligible | -0.12778 [-0.15556, -0.10370] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | random_eligible | -0.04259 [-0.06481, -0.02222] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | pilot | -0.15556 [-0.18704, -0.12407] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | stageroute | -0.07963 [-0.12593, -0.03704] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | random_eligible | +0.08519 [+0.05926, +0.10185] | 0.0000 | 0.0000 |
| accuracy | random_eligible | pilot | -0.11296 [-0.13333, -0.09259] | 0.0000 | 0.0000 |
| accuracy | pilot | stageroute | +0.07593 [+0.04074, +0.11486] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | t5_gbdt | -0.00481 [-0.00528, -0.00435] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | cheapest_eligible | +0.01246 [+0.01210, +0.01304] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | random_eligible | +0.00144 [+0.00039, +0.00237] | 0.0058 | 0.0348 |
| cost_per_task | t5_logreg | pilot | -0.00142 [-0.00175, -0.00111] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | cheapest_eligible | +0.01727 [+0.01669, +0.01794] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | strongest_eligible | +0.00505 [+0.00466, +0.00544] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | random_eligible | +0.00625 [+0.00498, +0.00731] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | pilot | +0.00339 [+0.00277, +0.00407] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | stageroute | +0.00384 [+0.00281, +0.00500] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | strongest_eligible | -0.01222 [-0.01284, -0.01158] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | random_eligible | -0.01102 [-0.01188, -0.01034] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | pilot | -0.01388 [-0.01454, -0.01332] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | stageroute | -0.01343 [-0.01421, -0.01264] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | pilot | -0.00166 [-0.00249, -0.00077] | 0.0000 | 0.0000 |
| cost_per_task | random_eligible | pilot | -0.00286 [-0.00387, -0.00189] | 0.0000 | 0.0000 |
| cost_per_task | random_eligible | stageroute | -0.00241 [-0.00374, -0.00090] | 0.0016 | 0.0112 |
| E | t5_logreg | cheapest_eligible | +0.01220 [+0.00615, +0.01817] | 0.0002 | 0.0018 |
| E | t5_logreg | strongest_eligible | -0.10560 [-0.12676, -0.08155] | 0.0000 | 0.0000 |
| E | t5_logreg | random_eligible | -0.08432 [-0.10391, -0.06213] | 0.0000 | 0.0000 |
| E | t5_logreg | pilot | -0.10850 [-0.12778, -0.08879] | 0.0000 | 0.0000 |
| E | t5_gbdt | cheapest_eligible | +0.02670 [+0.01032, +0.04517] | 0.0000 | 0.0000 |
| E | t5_gbdt | strongest_eligible | -0.09110 [-0.11755, -0.05639] | 0.0000 | 0.0000 |
| E | t5_gbdt | random_eligible | -0.06981 [-0.09972, -0.04352] | 0.0000 | 0.0000 |
| E | t5_gbdt | pilot | -0.09400 [-0.10883, -0.08041] | 0.0000 | 0.0000 |
| E | cheapest_eligible | strongest_eligible | -0.11780 [-0.13788, -0.09601] | 0.0000 | 0.0000 |
| E | cheapest_eligible | random_eligible | -0.09651 [-0.12070, -0.06823] | 0.0000 | 0.0000 |
| E | cheapest_eligible | pilot | -0.12070 [-0.13837, -0.10395] | 0.0000 | 0.0000 |
| E | cheapest_eligible | stageroute | -0.04482 [-0.07258, -0.01626] | 0.0022 | 0.0154 |
| E | strongest_eligible | stageroute | +0.07298 [+0.05145, +0.08863] | 0.0000 | 0.0000 |
| E | random_eligible | stageroute | +0.05169 [+0.02101, +0.08111] | 0.0004 | 0.0032 |
| E | pilot | stageroute | +0.07587 [+0.04092, +0.10907] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | t5_gbdt | +0.00926 [+0.00556, +0.01111] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | cheapest_eligible | -0.09259 [-0.09815, -0.08519] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | random_eligible | -0.01481 [-0.02593, -0.00370] | 0.0036 | 0.0256 |
| fill_rate | t5_logreg | pilot | -0.07407 [-0.08333, -0.06111] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | cheapest_eligible | -0.10185 [-0.10926, -0.09444] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | strongest_eligible | -0.01296 [-0.01667, -0.01111] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | random_eligible | -0.02407 [-0.03519, -0.01296] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | pilot | -0.08333 [-0.09259, -0.07222] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | strongest_eligible | +0.08889 [+0.08148, +0.09630] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | random_eligible | +0.07778 [+0.07037, +0.08519] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | pilot | +0.01852 [+0.00556, +0.03519] | 0.0032 | 0.0256 |
| fill_rate | cheapest_eligible | stageroute | +0.09444 [+0.08519, +0.10370] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | pilot | -0.07037 [-0.07968, -0.05926] | 0.0000 | 0.0000 |
| fill_rate | random_eligible | pilot | -0.05926 [-0.07593, -0.04444] | 0.0000 | 0.0000 |
| fill_rate | random_eligible | stageroute | +0.01667 [+0.00741, +0.02593] | 0.0034 | 0.0256 |
| fill_rate | pilot | stageroute | +0.07593 [+0.06481, +0.08704] | 0.0000 | 0.0000 |

### pi = 0.1 (Required side table)

| Method | Family | Accuracy | Cost/task | Violation | E (fraud_share) | Fill rate | Oracle acc regret (side) | Oracle cost regret (side) |
|---|---|---|---|---|---|---|---|---|
| Two-stage LR (trained on logs) | trained_recommender | 0.7852 [0.7648, 0.8056] | 0.02075 [0.02035, 0.02116] | 0.0000 [0.0000, 0.0000] | 0.0122 [0.0061, 0.0182] | 0.9074 [0.9019, 0.9148] | 0.1481 [0.1278, 0.1685] | 0.00465 [0.00413, 0.00517] |
| Two-stage GBDT (trained on logs) | trained_recommender | 0.7519 [0.7333, 0.7667] | 0.02556 [0.02500, 0.02608] | 0.0000 [0.0000, 0.0000] | 0.0267 [0.0103, 0.0450] | 0.8981 [0.8907, 0.9056] | 0.1815 [0.1667, 0.2000] | 0.00876 [0.00756, 0.01011] |
| Cheapest eligible | untrained_baseline | 0.6093 [0.5852, 0.6352] | 0.00829 [0.00796, 0.00862] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 0.3241 [0.2981, 0.3481] | -0.00949 [-0.01014, -0.00881] |
| Strongest eligible | untrained_baseline | 0.7407 [0.7167, 0.7630] | 0.02050 [0.01983, 0.02117] | 0.0000 [0.0000, 0.0000] | 0.1137 [0.0919, 0.1358] | 0.9111 [0.9037, 0.9185] | 0.1926 [0.1704, 0.2167] | 0.00231 [0.00159, 0.00291] |
| Random eligible | untrained_baseline | 0.6500 [0.6222, 0.6704] | 0.01938 [0.01821, 0.02047] | 0.0000 [0.0000, 0.0000] | 0.1070 [0.0946, 0.1203] | 0.9185 [0.9093, 0.9259] | 0.2833 [0.2630, 0.3093] | 0.00166 [0.00036, 0.00295] |
| Market-adapted PILOT (pilot_v1) | untrained_baseline | 0.7185 [0.6907, 0.7444] | 0.02222 [0.02159, 0.02261] | 0.0000 [0.0000, 0.0000] | 0.1771 [0.1658, 0.1884] | 0.9722 [0.9611, 0.9815] | 0.2148 [0.1889, 0.2426] | 0.00337 [0.00215, 0.00455] |
| Market-adapted StageRoute (stageroute_v1) | untrained_baseline | 0.6815 [0.6463, 0.7130] | 0.02008 [0.01941, 0.02082] | 0.0000 [0.0000, 0.0000] | 0.0579 [0.0140, 0.1035] | 0.9222 [0.9148, 0.9296] | 0.2519 [0.2204, 0.2852] | 0.00230 [0.00128, 0.00329] |

Significant Holm-adjusted primary-metric pairs at pi=0.1 (p_Holm < 0.05, family size 21): **64**.

| Metric | Method A | Method B | Delta (A - B) [95% CI] | p_raw | p_Holm |
|---|---|---|---|---:|---:|
| accuracy | t5_logreg | cheapest_eligible | +0.17593 [+0.14444, +0.20556] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | random_eligible | +0.13519 [+0.10185, +0.16852] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | pilot | +0.06667 [+0.03889, +0.09074] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | stageroute | +0.10370 [+0.06296, +0.14815] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | cheapest_eligible | +0.14259 [+0.10741, +0.17222] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | random_eligible | +0.10185 [+0.07037, +0.13333] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | pilot | +0.03333 [+0.01481, +0.05370] | 0.0002 | 0.0022 |
| accuracy | t5_gbdt | stageroute | +0.07037 [+0.02593, +0.11481] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | strongest_eligible | -0.13148 [-0.15556, -0.10741] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | random_eligible | -0.04074 [-0.06296, -0.01667] | 0.0002 | 0.0022 |
| accuracy | cheapest_eligible | pilot | -0.10926 [-0.13889, -0.07222] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | random_eligible | +0.09074 [+0.06296, +0.11852] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | stageroute | +0.05926 [+0.01296, +0.10926] | 0.0050 | 0.0400 |
| accuracy | random_eligible | pilot | -0.06852 [-0.09259, -0.03519] | 0.0002 | 0.0022 |
| cost_per_task | t5_logreg | t5_gbdt | -0.00481 [-0.00530, -0.00434] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | cheapest_eligible | +0.01246 [+0.01210, +0.01304] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | random_eligible | +0.00137 [+0.00037, +0.00245] | 0.0026 | 0.0156 |
| cost_per_task | t5_logreg | pilot | -0.00147 [-0.00208, -0.00083] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | cheapest_eligible | +0.01727 [+0.01671, +0.01794] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | strongest_eligible | +0.00506 [+0.00466, +0.00547] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | random_eligible | +0.00618 [+0.00511, +0.00755] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | pilot | +0.00334 [+0.00255, +0.00433] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | stageroute | +0.00548 [+0.00498, +0.00621] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | strongest_eligible | -0.01221 [-0.01282, -0.01155] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | random_eligible | -0.01109 [-0.01210, -0.00992] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | pilot | -0.01393 [-0.01456, -0.01315] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | stageroute | -0.01179 [-0.01238, -0.01127] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | pilot | -0.00172 [-0.00262, -0.00056] | 0.0058 | 0.0290 |
| cost_per_task | strongest_eligible | stageroute | +0.00042 [+0.00009, +0.00087] | 0.0000 | 0.0000 |
| cost_per_task | random_eligible | pilot | -0.00284 [-0.00367, -0.00208] | 0.0000 | 0.0000 |
| cost_per_task | pilot | stageroute | +0.00214 [+0.00084, +0.00308] | 0.0016 | 0.0112 |
| E | t5_logreg | cheapest_eligible | +0.01220 [+0.00615, +0.01817] | 0.0000 | 0.0000 |
| E | t5_logreg | strongest_eligible | -0.10154 [-0.12346, -0.08126] | 0.0000 | 0.0000 |
| E | t5_logreg | random_eligible | -0.09480 [-0.10806, -0.08214] | 0.0000 | 0.0000 |
| E | t5_logreg | pilot | -0.16495 [-0.17259, -0.15650] | 0.0000 | 0.0000 |
| E | t5_gbdt | cheapest_eligible | +0.02670 [+0.01032, +0.04517] | 0.0000 | 0.0000 |
| E | t5_gbdt | strongest_eligible | -0.08703 [-0.11143, -0.05404] | 0.0000 | 0.0000 |
| E | t5_gbdt | random_eligible | -0.08030 [-0.10131, -0.05304] | 0.0000 | 0.0000 |
| E | t5_gbdt | pilot | -0.15045 [-0.17185, -0.12820] | 0.0000 | 0.0000 |
| E | cheapest_eligible | strongest_eligible | -0.11373 [-0.13508, -0.09194] | 0.0000 | 0.0000 |
| E | cheapest_eligible | random_eligible | -0.10700 [-0.12031, -0.09463] | 0.0000 | 0.0000 |
| E | cheapest_eligible | pilot | -0.17715 [-0.18795, -0.16578] | 0.0000 | 0.0000 |
| E | cheapest_eligible | stageroute | -0.05785 [-0.10580, -0.01606] | 0.0016 | 0.0112 |
| E | strongest_eligible | pilot | -0.06341 [-0.08732, -0.03634] | 0.0000 | 0.0000 |
| E | random_eligible | pilot | -0.07015 [-0.08657, -0.05353] | 0.0000 | 0.0000 |
| E | pilot | stageroute | +0.11930 [+0.08135, +0.15476] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | t5_gbdt | +0.00926 [+0.00556, +0.01111] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | cheapest_eligible | -0.09259 [-0.09815, -0.08519] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | random_eligible | -0.01111 [-0.01852, -0.00370] | 0.0036 | 0.0150 |
| fill_rate | t5_logreg | pilot | -0.06481 [-0.07778, -0.05185] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | stageroute | -0.01481 [-0.01852, -0.01111] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | cheapest_eligible | -0.10185 [-0.10926, -0.09444] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | strongest_eligible | -0.01296 [-0.01667, -0.01111] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | random_eligible | -0.02037 [-0.02778, -0.01296] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | pilot | -0.07407 [-0.08704, -0.06111] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | stageroute | -0.02407 [-0.02963, -0.01852] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | strongest_eligible | +0.08889 [+0.08148, +0.09630] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | random_eligible | +0.08148 [+0.07407, +0.09074] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | pilot | +0.02778 [+0.01852, +0.04074] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | stageroute | +0.07778 [+0.07037, +0.08519] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | pilot | -0.06111 [-0.07407, -0.05000] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | stageroute | -0.01111 [-0.01852, -0.00370] | 0.0030 | 0.0150 |
| fill_rate | random_eligible | pilot | -0.05370 [-0.06111, -0.04630] | 0.0000 | 0.0000 |
| fill_rate | pilot | stageroute | +0.05000 [+0.03889, +0.06111] | 0.0000 | 0.0000 |

### pi = 0 (Required side table)

| Method | Family | Accuracy | Cost/task | Violation | E (fraud_share) | Fill rate | Oracle acc regret (side) | Oracle cost regret (side) |
|---|---|---|---|---|---|---|---|---|
| Two-stage LR (trained on logs) | trained_recommender | 0.7852 [0.7648, 0.8056] | 0.02076 [0.02035, 0.02116] | 0.0000 [0.0000, 0.0000] | 0.0122 [0.0061, 0.0182] | 0.9074 [0.9019, 0.9148] | 0.1481 [0.1278, 0.1685] | 0.00465 [0.00413, 0.00519] |
| Two-stage GBDT (trained on logs) | trained_recommender | 0.7519 [0.7333, 0.7667] | 0.02556 [0.02500, 0.02608] | 0.0000 [0.0000, 0.0000] | 0.0267 [0.0103, 0.0452] | 0.8981 [0.8907, 0.9056] | 0.1815 [0.1667, 0.2000] | 0.00876 [0.00753, 0.01010] |
| Cheapest eligible | untrained_baseline | 0.6093 [0.5852, 0.6333] | 0.00829 [0.00794, 0.00863] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 0.3241 [0.3000, 0.3481] | -0.00949 [-0.01015, -0.00881] |
| Strongest eligible | untrained_baseline | 0.7370 [0.7111, 0.7630] | 0.02052 [0.01985, 0.02119] | 0.0000 [0.0000, 0.0000] | 0.1178 [0.0960, 0.1379] | 0.9111 [0.9037, 0.9185] | 0.1963 [0.1722, 0.2241] | 0.00232 [0.00159, 0.00292] |
| Random eligible | untrained_baseline | 0.6481 [0.6222, 0.6778] | 0.01938 [0.01870, 0.02010] | 0.0000 [0.0000, 0.0000] | 0.1103 [0.0923, 0.1269] | 0.9241 [0.9130, 0.9389] | 0.2852 [0.2556, 0.3111] | 0.00161 [0.00075, 0.00255] |
| Market-adapted PILOT (pilot_v1) | untrained_baseline | 0.7741 [0.7481, 0.7963] | 0.01979 [0.01935, 0.02023] | 0.0000 [0.0000, 0.0000] | 0.1077 [0.0662, 0.1512] | 0.9796 [0.9741, 0.9852] | 0.1593 [0.1370, 0.1852] | 0.00136 [0.00041, 0.00220] |
| Market-adapted StageRoute (stageroute_v1) | untrained_baseline | 0.6630 [0.6333, 0.7000] | 0.01857 [0.01693, 0.02016] | 0.0000 [0.0000, 0.0000] | 0.0364 [0.0201, 0.0507] | 0.9204 [0.9093, 0.9333] | 0.2704 [0.2333, 0.3000] | 0.00080 [-0.00102, 0.00248] |

Significant Holm-adjusted primary-metric pairs at pi=0 (p_Holm < 0.05, family size 21): **59**.

| Metric | Method A | Method B | Delta (A - B) [95% CI] | p_raw | p_Holm |
|---|---|---|---|---:|---:|
| accuracy | t5_logreg | cheapest_eligible | +0.17593 [+0.14444, +0.20556] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | random_eligible | +0.13704 [+0.10185, +0.17222] | 0.0000 | 0.0000 |
| accuracy | t5_logreg | stageroute | +0.12222 [+0.07037, +0.16852] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | cheapest_eligible | +0.14259 [+0.10741, +0.17222] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | random_eligible | +0.10370 [+0.07222, +0.13704] | 0.0000 | 0.0000 |
| accuracy | t5_gbdt | stageroute | +0.08889 [+0.03519, +0.12963] | 0.0012 | 0.0108 |
| accuracy | cheapest_eligible | strongest_eligible | -0.12778 [-0.15370, -0.10370] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | pilot | -0.16481 [-0.20000, -0.12222] | 0.0000 | 0.0000 |
| accuracy | cheapest_eligible | stageroute | -0.05370 [-0.08889, -0.02037] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | random_eligible | +0.08889 [+0.04630, +0.13148] | 0.0000 | 0.0000 |
| accuracy | strongest_eligible | stageroute | +0.07407 [+0.04074, +0.10926] | 0.0000 | 0.0000 |
| accuracy | random_eligible | pilot | -0.12593 [-0.15741, -0.09259] | 0.0000 | 0.0000 |
| accuracy | pilot | stageroute | +0.11111 [+0.08519, +0.13704] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | t5_gbdt | -0.00481 [-0.00528, -0.00434] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | cheapest_eligible | +0.01246 [+0.01210, +0.01304] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | random_eligible | +0.00137 [+0.00087, +0.00180] | 0.0000 | 0.0000 |
| cost_per_task | t5_logreg | pilot | +0.00097 [+0.00035, +0.00155] | 0.0020 | 0.0160 |
| cost_per_task | t5_gbdt | cheapest_eligible | +0.01727 [+0.01671, +0.01792] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | strongest_eligible | +0.00505 [+0.00466, +0.00545] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | random_eligible | +0.00618 [+0.00540, +0.00700] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | pilot | +0.00577 [+0.00526, +0.00632] | 0.0000 | 0.0000 |
| cost_per_task | t5_gbdt | stageroute | +0.00699 [+0.00556, +0.00860] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | strongest_eligible | -0.01222 [-0.01284, -0.01158] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | random_eligible | -0.01109 [-0.01166, -0.01053] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | pilot | -0.01150 [-0.01200, -0.01093] | 0.0000 | 0.0000 |
| cost_per_task | cheapest_eligible | stageroute | -0.01028 [-0.01175, -0.00875] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | pilot | +0.00073 [+0.00031, +0.00126] | 0.0000 | 0.0000 |
| cost_per_task | strongest_eligible | stageroute | +0.00195 [+0.00054, +0.00334] | 0.0028 | 0.0196 |
| E | t5_logreg | cheapest_eligible | +0.01220 [+0.00615, +0.01817] | 0.0000 | 0.0000 |
| E | t5_logreg | strongest_eligible | -0.10560 [-0.12752, -0.08383] | 0.0000 | 0.0000 |
| E | t5_logreg | random_eligible | -0.09808 [-0.11458, -0.07999] | 0.0000 | 0.0000 |
| E | t5_logreg | pilot | -0.09553 [-0.13517, -0.05575] | 0.0000 | 0.0000 |
| E | t5_logreg | stageroute | -0.02420 [-0.04043, -0.00784] | 0.0070 | 0.0420 |
| E | t5_gbdt | cheapest_eligible | +0.02670 [+0.01032, +0.04517] | 0.0000 | 0.0000 |
| E | t5_gbdt | strongest_eligible | -0.09110 [-0.11755, -0.05654] | 0.0000 | 0.0000 |
| E | t5_gbdt | random_eligible | -0.08358 [-0.10933, -0.05727] | 0.0000 | 0.0000 |
| E | t5_gbdt | pilot | -0.08102 [-0.13525, -0.02481] | 0.0028 | 0.0196 |
| E | cheapest_eligible | strongest_eligible | -0.11780 [-0.13788, -0.09641] | 0.0000 | 0.0000 |
| E | cheapest_eligible | random_eligible | -0.11028 [-0.12685, -0.09226] | 0.0000 | 0.0000 |
| E | cheapest_eligible | pilot | -0.10772 [-0.15115, -0.06614] | 0.0000 | 0.0000 |
| E | cheapest_eligible | stageroute | -0.03639 [-0.05062, -0.02014] | 0.0000 | 0.0000 |
| E | strongest_eligible | stageroute | +0.08141 [+0.07303, +0.09082] | 0.0000 | 0.0000 |
| E | random_eligible | stageroute | +0.07389 [+0.05248, +0.09317] | 0.0000 | 0.0000 |
| E | pilot | stageroute | +0.07133 [+0.03645, +0.10762] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | t5_gbdt | +0.00926 [+0.00556, +0.01111] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | cheapest_eligible | -0.09259 [-0.09815, -0.08519] | 0.0000 | 0.0000 |
| fill_rate | t5_logreg | pilot | -0.07222 [-0.07963, -0.06296] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | cheapest_eligible | -0.10185 [-0.10926, -0.09444] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | strongest_eligible | -0.01296 [-0.01667, -0.01111] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | random_eligible | -0.02593 [-0.03889, -0.01296] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | pilot | -0.08148 [-0.09074, -0.07407] | 0.0000 | 0.0000 |
| fill_rate | t5_gbdt | stageroute | -0.02222 [-0.03519, -0.00926] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | strongest_eligible | +0.08889 [+0.08148, +0.09630] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | random_eligible | +0.07593 [+0.06111, +0.08704] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | pilot | +0.02037 [+0.01481, +0.02593] | 0.0000 | 0.0000 |
| fill_rate | cheapest_eligible | stageroute | +0.07963 [+0.06667, +0.09074] | 0.0000 | 0.0000 |
| fill_rate | strongest_eligible | pilot | -0.06852 [-0.07407, -0.06296] | 0.0000 | 0.0000 |
| fill_rate | random_eligible | pilot | -0.05556 [-0.06852, -0.04074] | 0.0000 | 0.0000 |
| fill_rate | pilot | stageroute | +0.05926 [+0.04630, +0.07222] | 0.0000 | 0.0000 |

