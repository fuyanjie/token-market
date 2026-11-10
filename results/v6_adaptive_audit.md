# v6 — Adaptive audit under fixed expected budget (+ escrow)

Policy `audited_compliance_cascade`, target a=0.1, budget×2.0, escrow=True, attack modes ['swap', 'theft'], seeds=[0, 1, 2]. Adaptive arm scores sellers (TrustModel risk / billed÷actual EMA / prior detections) and spends the same expected audit budget on high-risk purchases first; leftover credit falls back to random.

| arm | learned q_swap / q_theft | J | fraud share | accuracy | n_audits | realized a | escrow held / slashed / released |
|---|---|---|---|---|---|---|---|
| fixed | 0.083±0.049 / 0.081±0.039 | 0.766±0.037 | 0.101±0.023 | 0.817 | 60.3 | 0.087 | 12.26 / 0.15 / 12.11 |
| adaptive | 0.056±0.035 / 0.053±0.029 | 0.803±0.019 | 0.044±0.009 | 0.825 | 66.0 | 0.099 | 11.47 / 0.23 / 11.24 |

Claim-safe reading: adaptive audit is a **cost-reduction / targeting** improvement under a fixed audit budget; the main claim remains deterrence (lower q*) via audits. Do **not** read a J gap vs PILOT/StageRoute under immediate feedback as a win. Escrow is payment timing (slash-from-hold), orthogonal to label delay L.
