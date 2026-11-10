# v1.0 run summary (plain means over seeds; inference is done by Experiment)

E = fraud_share (per purchase), E_tok = billed-token share; Q = unweighted mean of q over seller-present tail rounds, simple mean of modes; tail_trade_rate = fraction of runs with >=1 sale to a strategic seller in the last 12 rounds (Q not identifiable / hollow point when low).

| method | π | n | E | E_tok | Q | Q_swap | Q_theft | Q_downgrade | J | quality | cost | tail_trade_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| audited_cascade_unfiltered | 1 | 2 | 0.0022 | 0.0016 | 0.5306 | 0.5833 | 0.4833 | 0.5250 | 0.6447 | 0.8167 | 7.1840 | 0.00 (0/2) |
| audited_cascade_unfiltered | 0.1 | 2 | 0.0022 | 0.0016 | 0.5306 | 0.5833 | 0.4833 | 0.5250 | 0.6447 | 0.8167 | 7.1840 | 0.00 (0/2) |
| fixed_audit_a0.10 | 1 | 2 | 0.0065 | 0.0081 | 0.5764 | 0.6694 | 0.4819 | 0.5778 | 0.8186 | 0.8219 | 7.3189 | 1.00 (2/2) |
| fixed_audit_a0.10 | 0.1 | 2 | 0.0065 | 0.0081 | 0.5764 | 0.6694 | 0.4819 | 0.5778 | 0.8186 | 0.8219 | 7.3189 | 1.00 (2/2) |
| pilot | 1 | 2 | 0.1699 | 0.1894 | 0.9431 | 0.9319 | 0.9681 | 0.9292 | 0.6911 | 0.7760 | 11.5403 | 1.00 (2/2) |
| pilot | 0.1 | 2 | 0.2304 | 0.2380 | 0.8255 | 0.9653 | 0.8153 | 0.6958 | 0.6483 | 0.7635 | 11.7484 | 1.00 (2/2) |
| stageroute | 1 | 2 | 0.0361 | 0.0422 | 0.5648 | 0.5250 | 0.5722 | 0.5972 | 0.7132 | 0.7312 | 10.1295 | 1.00 (2/2) |
| stageroute | 0.1 | 2 | 0.0990 | 0.1140 | 0.6292 | 0.4528 | 0.8583 | 0.5764 | 0.6109 | 0.6604 | 8.4517 | 1.00 (2/2) |
