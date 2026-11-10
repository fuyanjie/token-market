# F — Delayed / sparse outcome feedback (v5 ablation)

**Setting.** Outcome feedback = whether a purchased answer was correct (the bandit reward). A purchase at step t (task index) has its label revealed with probability π and, if revealed, delivered to the router at step t + L (FIFO by due step, before that step's routing decision); labels still pending at the end of the episode are flushed if L is finite, never delivered if L = ∞. Only the LABEL is delayed: the realised cost is on the buyer's own bill and stays immediate (PILOT budget bins, StageRoute cost estimate).

**Audits are a separate signal.** D3's audits (rate 0.1, checks ['identity', 'length'], d_identity = 0.9, d_length = 0.9, P = 0.25) run, slash/delist the seller and update D3's TrustModel IMMEDIATELY in every regime; D3's routing never uses correctness labels, so the feedback channel only changes its logging. PILOT+compliance and StageRoute+compliance do NOT audit (audit rate 0).

Market: strategic learning seller seller_sg with attack modes ['swap', 'theft'] (same as section J), budget × 2.0, J = acc − 1.0·violation rate − 0.5·fraud share. Mean ± std over seeds [0]. q = seller's learned attack rate (mean over the last half of epochs). coverage = labels delivered during the episode / purchases.

Real vs simulated: the correctness labels come from the REAL cached Qwen outputs (no new generation); the feedback channel (delay L, reveal probability π, flush rule), audits, the seller's learning rule, prices and budgets are SIMULATED.

## Delay sweep (π = 1)

| L | policy | J | accuracy | violation rate | fraud share | sg q_swap / q_theft | share of purchases from sg | cost/task incl. audit | feedback coverage |
|---|---|---|---|---|---|---|---|---|---|
| 0 | **D3 (ours)** | 0.849 ± 0.000 | 0.917 ± 0.000 | 0.000 | 0.135 ± 0.000 | 0.55 / 0.45 | 0.243 | 0.0298 | 1.00 |

## Sparsity sweep (L = 0)

| π | policy | J | accuracy | violation rate | fraud share | sg q_swap / q_theft | share of purchases from sg | cost/task incl. audit | feedback coverage |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **D3 (ours)** | 0.849 ± 0.000 | 0.917 ± 0.000 | 0.000 | 0.135 ± 0.000 | 0.55 / 0.45 | 0.243 | 0.0298 | 1.00 |

## D3 advantage over the best compliant bandit

ΔJ = J(D3) − max J(bandits); Δfraud = min fraud share(bandits) − fraud share(D3); Δq = min learned q over bandits − D3's (positive = D3 better).

| (L, π) | best bandit | ΔJ | Δfraud share | Δq_swap | Δq_theft |
|---|---|---|---|---|---|

## Hypothesis verdict

Hypothesis: D3's advantage (J and fraud suppression) over the compliant bandits GROWS as outcome feedback becomes delayed or sparse.

- grows from immediate to L = ∞: **no** (ΔJ non-decreasing along the L sweep within 0.01: yes)
- grows from immediate to π = 1: **no** (ΔJ non-decreasing along the π sweep within 0.01: yes)
- regimes where D3 beats BOTH compliant bandits on J: none
- regimes where D3 has a lower fraud share than BOTH bandits: none
- seller attack rates: the bandits never lower q (they avoid the attacker instead of deterring it), D3's audits keep q low in every regime because audits do not depend on outcome feedback.
- **verdict: hypothesis NOT supported**
