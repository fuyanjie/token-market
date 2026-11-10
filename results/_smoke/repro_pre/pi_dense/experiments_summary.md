# token-market v5 — experiment summary

Novelty framing: compliance-constrained portfolio purchasing + strategic fraud (model swap AND token theft) under IMPERFECT audits, compared with PILOT-style / StageRoute-style baselines on the JOINT objective J = accuracy − λ·violation rate − μ·fraud share (headline: section J). v5 (section F): the setting where audits matter is DELAYED / SPARSE outcome feedback - audits are a separate, immediate signal, while the bandits' correctness labels are delayed by L steps or revealed w.p. π. Reasoning-token length uncertainty is NOT claimed as a contribution: the expected-vs-actual cost logging is infrastructure and its finding is negative (overruns ≈ 0 under normal budgets, they only bind under tight budgets; section B).

config `results/_smoke/repro_pre/pi_dense_smoke.yaml`, seeds=[0], backend override=None, reputation source: Qwen/Qwen2.5-1.5B-Instruct: measured, sim-fast-mock: config_prior

## F — Delayed / sparse outcome feedback (v5 ablation)

**Setting.** Outcome feedback = whether a purchased answer was correct (the bandit reward). A purchase at step t (task index) has its label revealed with probability π and, if revealed, delivered to the router at step t + L (FIFO by due step, before that step's routing decision); labels still pending at the end of the episode are flushed if L is finite, never delivered if L = ∞. Only the LABEL is delayed: the realised cost is on the buyer's own bill and stays immediate (PILOT budget bins, StageRoute cost estimate).

**Audits are a separate signal.** D3's audits (rate 0.1, checks ['identity', 'length'], d_identity = 0.9, d_length = 0.9, P = 0.25) run, slash/delist the seller and update D3's TrustModel IMMEDIATELY in every regime; D3's routing never uses correctness labels, so the feedback channel only changes its logging. PILOT+compliance and StageRoute+compliance do NOT audit (audit rate 0).

Market: strategic learning seller seller_sg with attack modes ['swap', 'theft'] (same as section J), budget × 2.0, J = acc − 1.0·violation rate − 0.5·fraud share. Mean ± std over seeds [0]. q = seller's learned attack rate (mean over the last half of epochs). coverage = labels delivered during the episode / purchases.

Real vs simulated: the correctness labels come from the REAL cached Qwen outputs (no new generation); the feedback channel (delay L, reveal probability π, flush rule), audits, the seller's learning rule, prices and budgets are SIMULATED.

### Delay sweep (π = 1)

| L | policy | J | accuracy | violation rate | fraud share | sg q_swap / q_theft | share of purchases from sg | cost/task incl. audit | feedback coverage |
|---|---|---|---|---|---|---|---|---|---|
| 0 | **D3 (ours)** | 0.849 ± 0.000 | 0.917 ± 0.000 | 0.000 | 0.135 ± 0.000 | 0.55 / 0.45 | 0.243 | 0.0298 | 1.00 |

### Sparsity sweep (L = 0)

| π | policy | J | accuracy | violation rate | fraud share | sg q_swap / q_theft | share of purchases from sg | cost/task incl. audit | feedback coverage |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **D3 (ours)** | 0.849 ± 0.000 | 0.917 ± 0.000 | 0.000 | 0.135 ± 0.000 | 0.55 / 0.45 | 0.243 | 0.0298 | 1.00 |

### D3 advantage over the best compliant bandit

ΔJ = J(D3) − max J(bandits); Δfraud = min fraud share(bandits) − fraud share(D3); Δq = min learned q over bandits − D3's (positive = D3 better).

| (L, π) | best bandit | ΔJ | Δfraud share | Δq_swap | Δq_theft |
|---|---|---|---|---|---|

### Hypothesis verdict

Hypothesis: D3's advantage (J and fraud suppression) over the compliant bandits GROWS as outcome feedback becomes delayed or sparse.

- grows from immediate to L = ∞: **no** (ΔJ non-decreasing along the L sweep within 0.01: yes)
- grows from immediate to π = 1: **no** (ΔJ non-decreasing along the π sweep within 0.01: yes)
- regimes where D3 beats BOTH compliant bandits on J: none
- regimes where D3 has a lower fraud share than BOTH bandits: none
- seller attack rates: the bandits never lower q (they avoid the attacker instead of deterring it), D3's audits keep q low in every regime because audits do not depend on outcome feedback.
- **verdict: hypothesis NOT supported**

## What is real vs simulated

- **Real**: Qwen2.5-1.5B / 0.5B-Instruct outputs (local CPU inference, cached), their correctness against gold, reasoning-token counts and measured generation times on CPU; the GSM8K / MATH-500 long-task problems and golds. v4 token theft truncates these REAL cached outputs (character-proportional cut, answer re-parsed) - no new generation is run; the optional length-audit reference cross-check compares against the REAL cached greedy generation of the claimed model.
- **Simulated**: prices, serving costs (and the swap cost gap), latency noise and corridor penalties/fees, jurisdictions and the (simplified, NOT legal advice) compliance rules, buyers / budgets / sensitivities / consent, audits and BOTH detectors (identity check succeeding with prob d, length audit with prob d_length; miss / false-negative rates 1 - d, false positives 0), penalties / stake slashing / delisting, the strategic seller's learning rule and attack choice, the mock seller (seller_br, MockLLM), its confidence and its truncation model.

_total experiment time 0.5s_
