# v1.0 run summary (plain means over seeds; inference is done by Experiment)

E = fraud_share (per purchase), E_tok = billed-token share; Q = unweighted mean of q over seller-present tail rounds, simple mean of modes; tail_trade_rate = fraction of runs with >=1 sale to a strategic seller in the last 12 rounds (Q not identifiable / hollow point when low).

| method | π | n | E | E_tok | Q | Q_swap | Q_theft | Q_downgrade | J | quality | cost | tail_trade_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cheapest_fixed | 1 | 20 | 0.0000 | 0.0000 | 0.5076 | 0.5139 | 0.4853 | 0.5237 | 0.5614 | 0.6266 | 3.2446 | 0.00 (0/20) |
| fixed_audit_a0.05 | 1 | 20 | 0.0013 | 0.0012 | 0.5324 | 0.5842 | 0.4943 | 0.5186 | 0.6604 | 0.8280 | 6.9624 | 0.05 (1/20) |
| fixed_audit_a0.10 | 1 | 20 | 0.0013 | 0.0012 | 0.5292 | 0.5711 | 0.4928 | 0.5237 | 0.6591 | 0.8260 | 7.1097 | 0.05 (1/20) |
| fixed_audit_a0.20 | 1 | 20 | 0.0013 | 0.0012 | 0.5181 | 0.5378 | 0.4928 | 0.5237 | 0.6530 | 0.8207 | 7.4219 | 0.05 (1/20) |
| pilot | 1 | 20 | 0.1591 | 0.1765 | 0.9248 | 0.9154 | 0.9379 | 0.9211 | 0.5492 | 0.7844 | 11.4696 | 1.00 (20/20) |
| random_audit | 1 | 20 | 0.0013 | 0.0012 | 0.5292 | 0.5711 | 0.4928 | 0.5237 | 0.6590 | 0.8256 | 7.1003 | 0.05 (1/20) |
| risk_adaptive_audit | 1 | 20 | 0.0013 | 0.0012 | 0.5292 | 0.5711 | 0.4928 | 0.5237 | 0.6603 | 0.8267 | 7.0683 | 0.05 (1/20) |
| stageroute | 1 | 20 | 0.0496 | 0.0549 | 0.6050 | 0.5174 | 0.7326 | 0.5650 | 0.5308 | 0.7340 | 11.0026 | 0.55 (11/20) |
| strongest_fixed | 1 | 20 | 0.5191 | 0.5655 | 0.7450 | 0.7937 | 0.6439 | 0.7974 | 0.1540 | 0.6046 | 10.7276 | 1.00 (20/20) |
