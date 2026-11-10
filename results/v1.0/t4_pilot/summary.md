# v1.0 run summary (plain means over seeds; inference is done by Experiment)

E = fraud_share (per purchase), E_tok = billed-token share; Q = unweighted mean of q over seller-present tail rounds, simple mean of modes; tail_trade_rate = fraction of runs with >=1 sale to a strategic seller in the last 12 rounds (Q not identifiable / hollow point when low).

| method | π | n | E | E_tok | Q | Q_swap | Q_theft | Q_downgrade | J | quality | cost | tail_trade_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pilot | 1 | 20 | 0.1580 | 0.1747 | 0.9162 | 0.9024 | 0.9481 | 0.8982 | 0.7009 | 0.7799 | 11.5326 | 1.00 (20/20) |
