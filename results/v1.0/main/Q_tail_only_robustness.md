# Q averaging check and gate robustness (not a change to the pre-registered rule)

## How the 0.52–0.54 figures were computed

The main-table Q (0.52–0.54 for audit methods) is the unweighted mean over **all 20 seeds**, including the 7–8 runs with no tail trade. That matches the protocol: Q is the q the seller *played* in tail rounds where it was listed (not delisted); a sale is not required. In no-tail D3 runs, `Q_present_rounds` is still 108 (9 strategic sellers × 12 tail rounds).

Those no-tail runs are **not** all stuck at 0.5. At π=1, egreedy:

| method | Q, all 20 seeds | Q, tail-trade runs only | Q, no-tail runs | n no-tail |
|---|---|---|---|---:|
| fixed a=0.05 | 0.531 [0.500, 0.559] | 0.527 [0.497, 0.555] (n=13) | 0.537 | 7 |
| D3-ref (a=0.10) | 0.538 [0.508, 0.566] | 0.536 [0.504, 0.565] (n=13) | 0.543 | 7 |
| fixed a=0.20 | 0.519 [0.485, 0.552] | 0.514 [0.474, 0.552] (n=13) | 0.529 | 7 |
| random-intensity | 0.533 [0.501, 0.563] | 0.523 [0.490, 0.553] (n=13) | 0.551 | 7 |
| risk-adaptive | 0.536 [0.505, 0.565] | 0.525 [0.492, 0.555] (n=12) | 0.552 | 8 |
| StageRoute | 0.609 [0.590, 0.629] | 0.610 [0.589, 0.630] (n=17) | 0.605 | 3 |
| PILOT / strongest | unchanged (20/20 tail trades) | same | — | 0 |

So “close to uniform” is not an artefact of averaging in no-trade runs. No-tail D3 Q values range from about 0.39 to 0.62.

## Gate robustness (not a rule change)

Dropping the five audit methods with low identifiability (12–13/20) leaves PILOT, StageRoute, and strongest. On these three, Kendall τ_a = 1.0 at all 19 π (3/3 pairs concordant) under egreedy vs fictitious play. Still ≥ 0.6. The pre-registered 8-method gate (τ_a=0.643) is unchanged; this column is robustness only.
