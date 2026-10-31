# Imperfect detection — audit rate a × detection probability d (miss rate 1 − d) × penalty P

Learning model-swap seller (swap only), buyer policy `single_best_compliant`, 960 tasks / 96 epochs per run, seeds=[0, 1, 2]. Identity check detects a swapped answer with probability d; **miss rate = false-negative rate = 1 − d**; false-positive rate = 0 (honest answers are never flagged). Detection is SIMULATED.

Swap saving per purchase = 0.00996. Analytic threshold **a\*(d) = saving / (d · P)** (decreasing in d: halving d doubles the audit rate needed). Empirical threshold = smallest grid audit rate from which on the learned q stays < 0.1.

## Thresholds a*(d) vs empirical

| P | d | miss rate 1−d | analytic a*(d) | first grid a > a* | empirical a (learned q < thr) | match |
|---|---|---|---|---|---|---|
| 0.1 | 0.3 | 0.7 | 0.3321 | 0.5 | 0.5 | yes |
| 0.1 | 0.5 | 0.5 | 0.1993 | 0.2 | 0.3 | no |
| 0.1 | 0.7 | 0.3 | 0.1423 | 0.2 | 0.2 | yes |
| 0.1 | 0.9 | 0.1 | 0.1107 | 0.2 | 0.2 | yes |
| 0.1 | 1.0 | 0.0 | 0.0996 | 0.1 | 0.2 | no |
| 0.5 | 0.3 | 0.7 | 0.0664 | 0.1 | 0.1 | yes |
| 0.5 | 0.5 | 0.5 | 0.0399 | 0.05 | 0.1 | no |
| 0.5 | 0.7 | 0.3 | 0.0285 | 0.05 | 0.05 | yes |
| 0.5 | 0.9 | 0.1 | 0.0221 | 0.05 | 0.05 | yes |
| 0.5 | 1.0 | 0.0 | 0.0199 | 0.02 | 0.02 | yes |

## learned swap rate q (P = 0.1; rows d, columns audit rate a; mean over seeds)

| d \ a | 0.0 | 0.02 | 0.05 | 0.1 | 0.2 | 0.3 | 0.5 | 0.7 | 1.0 |
|---|---|---|---|---|---|---|---|---|---|
| 0.3 | 0.96 | 0.96 | 0.96 | 0.96 | 0.96 | 0.96 | 0.03* | 0.03* | 0.03* |
| 0.5 | 0.96 | 0.96 | 0.96 | 0.96 | 0.35* | 0.07* | 0.03* | 0.03* | 0.03* |
| 0.7 | 0.96 | 0.96 | 0.96 | 0.96 | 0.03* | 0.06* | 0.03* | 0.03* | 0.03* |
| 0.9 | 0.96 | 0.96 | 0.96 | 0.64 | 0.03* | 0.03* | 0.03* | 0.03* | 0.03* |
| 1.0 | 0.96 | 0.96 | 0.96 | 0.64* | 0.03* | 0.03* | 0.03* | 0.03* | 0.03* |

## served swap rate (P = 0.1; rows d, columns audit rate a; mean over seeds)

| d \ a | 0.0 | 0.02 | 0.05 | 0.1 | 0.2 | 0.3 | 0.5 | 0.7 | 1.0 |
|---|---|---|---|---|---|---|---|---|---|
| 0.3 | 0.96 | 0.96 | 0.96 | 0.96 | 0.95 | 0.88 | 0.12* | 0.08* | 0.06* |
| 0.5 | 0.96 | 0.96 | 0.96 | 0.96 | 0.39* | 0.10* | 0.05* | 0.04* | 0.04* |
| 0.7 | 0.96 | 0.96 | 0.96 | 0.96 | 0.10* | 0.09* | 0.05* | 0.04* | 0.04* |
| 0.9 | 0.96 | 0.96 | 0.96 | 0.67 | 0.07* | 0.06* | 0.04* | 0.04* | 0.04* |
| 1.0 | 0.96 | 0.96 | 0.89 | 0.59* | 0.06* | 0.05* | 0.04* | 0.04* | 0.04* |

## learned swap rate q (P = 0.5; rows d, columns audit rate a; mean over seeds)

| d \ a | 0.0 | 0.02 | 0.05 | 0.1 | 0.2 | 0.3 | 0.5 | 0.7 | 1.0 |
|---|---|---|---|---|---|---|---|---|---|
| 0.3 | 0.96 | 0.96 | 0.71 | 0.03* | 0.03* | 0.03* | 0.03* | 0.03* | 0.03* |
| 0.5 | 0.96 | 0.96 | 0.11* | 0.03* | 0.03* | 0.03* | 0.03* | 0.03* | 0.03* |
| 0.7 | 0.96 | 0.37 | 0.05* | 0.03* | 0.03* | 0.03* | 0.03* | 0.03* | 0.03* |
| 0.9 | 0.96 | 0.46 | 0.03* | 0.03* | 0.03* | 0.03* | 0.03* | 0.03* | 0.03* |
| 1.0 | 0.96 | 0.05* | 0.03* | 0.03* | 0.03* | 0.03* | 0.03* | 0.03* | 0.03* |

## served swap rate (P = 0.5; rows d, columns audit rate a; mean over seeds)

| d \ a | 0.0 | 0.02 | 0.05 | 0.1 | 0.2 | 0.3 | 0.5 | 0.7 | 1.0 |
|---|---|---|---|---|---|---|---|---|---|
| 0.3 | 0.96 | 0.95 | 0.76 | 0.08* | 0.08* | 0.08* | 0.06* | 0.05* | 0.05* |
| 0.5 | 0.96 | 0.95 | 0.37* | 0.07* | 0.08* | 0.07* | 0.05* | 0.04* | 0.04* |
| 0.7 | 0.96 | 0.60 | 0.26* | 0.06* | 0.06* | 0.06* | 0.05* | 0.04* | 0.04* |
| 0.9 | 0.96 | 0.61 | 0.23* | 0.05* | 0.05* | 0.05* | 0.04* | 0.04* | 0.04* |
| 1.0 | 0.96 | 0.23* | 0.19* | 0.05* | 0.05* | 0.05* | 0.04* | 0.04* | 0.04* |

`*` = analytic best response is honest (a > a*(d)). Per-point details (seller profit, detections, stake slashed, buyer accuracy) in results/imperfect_detection.json.
