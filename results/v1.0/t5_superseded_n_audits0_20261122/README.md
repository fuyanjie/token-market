# Superseded T5 tree (NOT official)

This directory is an archival copy of the 2026-11-22 T5 readout that was originally written to `results/v1.0/t5/` and committed as `6c04451`.

**It is not official T5.** Research rejected that readout because all 126 official evaluation runs had `n_audits=0`, which violates `docs/PROTOCOL_T5.md` §1 (inherit the v1.0 default fixed audit `a=0.10`).

Cause: `tokenmarket/sim.py` `policy_audit_rate()` returns `market.audit.rate` (0) when the policy is not in `AUDITED_POLICIES` and `market.audit_v11` is not enabled. The T5 runner called `run_single` with `t5_recommender_compliant`, `pilot_v1_compliant`, and `stageroute_v1_compliant`, so both training logs and evaluation used a=0.

This archive is kept for audit. Do not treat its accuracy, cost, E, fill_rate, regret, AUROC, or other scores as official T5 numbers. Do not copy them into the paper. The replacement official tree, after the audit-wiring fix and a full train+eval rerun at fixed a=0.10, belongs only in `results/v1.0/t5/`.

Commit `6c04451` is not amended or rewritten.
