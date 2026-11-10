# v1.0 run summary (plain means over seeds; inference is done by Experiment)

E = fraud_share (per purchase), E_tok = billed-token share; Q = unweighted mean of q over seller-present tail rounds, simple mean of modes; tail_trade_rate = fraction of runs with >=1 sale to a strategic seller in the last 12 rounds (Q not identifiable / hollow point when low).

| method | π | n | E | E_tok | Q | Q_swap | Q_theft | Q_downgrade | J | quality | cost | tail_trade_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fixed_audit_a0.10 | 1 | 20 | 0.0066 | 0.0067 | 0.5056 | 0.4501 | 0.5464 | 0.5204 | 0.7609 | 0.7642 | 8.8661 | 0.80 (16/20) |
