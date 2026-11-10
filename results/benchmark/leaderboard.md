# Benchmark leaderboard

Primary board = active_attack_rate + fraud_share. J is secondary. Immediate-feedback J is NOT the primary ranking.

## Table 1 — active attack rate (primary; learned q* mean)

| rank | baseline | active_attack_rate |
|---|---|---|
| 1 | random_audit | 0.800 ± 0.000 |
| 2 | D3_v6 | 0.925 ± 0.000 |
| 3 | fixed_a_audit | 0.925 ± 0.000 |
| 4 | StageRoute | 0.950 ± 0.000 |
| 5 | PILOT | 0.950 ± 0.000 |

## Table 2 — realized fraud_share (primary)

| rank | baseline | fraud_share |
|---|---|---|
| 1 | D3_v6 | 0.243 ± 0.000 |
| 2 | fixed_a_audit | 0.243 ± 0.000 |
| 3 | StageRoute | 0.250 ± 0.000 |
| 4 | PILOT | 0.250 ± 0.000 |
| 5 | random_audit | 0.792 ± 0.000 |

## Table 3 — J (secondary; NOT primary board)

| rank | baseline | J |
|---|---|---|
| 1 | D3_v6 | 0.837 ± 0.000 |
| 2 | fixed_a_audit | 0.837 ± 0.000 |
| 3 | StageRoute | 0.542 ± 0.000 |
| 4 | PILOT | 0.458 ± 0.000 |
| 5 | random_audit | -0.062 ± 0.000 |

Baselines: StageRoute / PILOT (immediate feedback, no audit), fixed-a D3 audit, random audit on single_best_compliant, v6 D3 (audited_compliance_cascade). D3_v6 and fixed_a_audit share the same arm in v1 (appendix may split adaptive).
