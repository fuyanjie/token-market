# WP0 reproduction gate: v1.1 re-run vs v1.0 main (seeds 0 1 2)

- reference: `results/v1.0/main/per_seed.csv`
- re-run: `results/v1.1/wp0_repro/per_seed.csv`
- match key: (method, pi, seed); tolerance |Δ| ≤ 1e-09
- **result: PASS**
- rows: ref 513, new 513, compared 513; only in ref 0, only in new 0
- column lists identical: True
- max |Δ| over all numeric columns: 0
- mismatching rows: 0

## Numeric columns (28): max |Δ|

| column | max abs Δ |
|---|---|
| E | 0 |
| E_tok | 0 |
| fraud_share | 0 |
| fraud_share_swap | 0 |
| fraud_share_theft | 0 |
| fraud_share_downgrade | 0 |
| Q | 0 |
| Q_swap | 0 |
| Q_theft | 0 |
| Q_downgrade | 0 |
| tail_trade | 0 |
| tail_trade_sellers | 0 |
| tail_sales | 0 |
| n_strategic | 0 |
| Q_present_rounds | 0 |
| delisted_rounds_tail | 0 |
| q_delisted_mean | 0 |
| J | 0 |
| quality | 0 |
| cost | 0 |
| cost_per_task | 0 |
| audit_cost | 0 |
| n_audits | 0 |
| audit_rate_realised | 0 |
| violation_rate | 0 |
| fill_rate | 0 |
| n_served | 0 |
| compliance_filter | 0 |

## Text columns compared by exact equality (6)

label, policy, seller_learner, audit_rule, roster_seed, config_hash

