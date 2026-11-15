# Q gate audit — documentation 2026-11-15

docs/PROTOCOL_v1.0.md §1; 口径补正 2026-11-10 and 开跑前裁定 item 2

At every pi: tau_a >= 0.6 AND unchanged lower-better (E,Q) front on methods with tail_trade_rate > 0.5 under both learners.

Analyzer stably sorts equal mean Q in ORDER and assigns distinct sequential ranks; pairwise Kendall uses (C-D)/(n*(n-1)/2). Equal E,Q points do not dominate each other. No epsilon tie threshold.

Formal peer: fictitious play. EXP3 and the earlier Hedge check are excluded. The eligibility screen is reproduced without revising its interpretation or any paper verdict.

| π | eligible main / peer / common | τ_a | τ predicate | front main | front peer | front predicate | pass | agrees with frozen gate |
|---|---|---|---|---|---|---|---|---|
| 0.0 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 0.02 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 0.04 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 0.06 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 0.08 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 0.1 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 0.11 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 0.12 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 0.14 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 0.16 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 0.18 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 0.2 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 0.22 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 0.24 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 0.26 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 0.28 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 0.3 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 0.5 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |
| 1.0 | 8/8/8 | 0.642857142857143 | True | fixed_audit_a0.20 | fixed_audit_a0.20 | True | True | True |

All π pass: **True**. All agree with frozen gate: **True**.

The JSON lists each eligible/excluded method, means, ranks, pair counts and source hashes. Rebuild: `python scripts/pass17_q_gate_report.py`. No simulator or bootstrap is run.
