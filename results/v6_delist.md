# v6 — Delisting after catch (D3 reputation_rounds ablation)

Policy `audited_compliance_cascade`, a=0.1, budget×2.0, attack modes ['swap', 'theft'], seeds=[0, 1, 2]. Routing skips sellers with banned_until_round > current round (demand zero while banned).

| reputation_rounds | learned q_swap / q_theft | J | fraud share | accuracy | n_audits | n_bans | stake slashed |
|---|---|---|---|---|---|---|---|
| 0 | 0.083±0.049 / 0.081±0.039 | 0.766±0.037 | 0.101±0.023 | 0.817 | 60.3 | 0.0 | 1.42 |
| 5 | 0.181±0.136 / 0.094±0.099 | 0.787±0.010 | 0.063±0.006 | 0.819 | 57.7 | 3.7 | 0.92 |
| 20 | 0.439±0.427 / 0.685±0.468 | 0.807±0.019 | 0.041±0.022 | 0.827 | 55.0 | 2.3 | 0.58 |

Claim-safe reading: delisting strengthens deterrence (lower q*) by zeroing demand after a catch; it is NOT a claim about beating PILOT/StageRoute under immediate feedback. Default config keeps reputation_rounds=0 so prior F/J tables stay reproducible.

### Honest note on learned q vs fraud share

Longer delisting **cuts realised fraud share** (and lifts J) because the attacker is often offline; the epoch-mean learned q can *rise* because the seller gets fewer post-slash observations while banned and exploration drifts. Report both metrics; do not claim delisting alone drives q* → 0.
