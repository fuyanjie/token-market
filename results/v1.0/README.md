# results/v1.0 — v1.0 protocol runs (Experiment)

All files here are **v0.1-scale** (3 sellers, 1 strategic seller, swap+theft, n_tasks=480, n_rounds=48, LLM cache) unless stated.
They follow `docs/PROTOCOL_v1.0.md` but do NOT meet the §2 scale (≥40 sellers, ≥3 strategic, ≥3 attack types) or the §3 baselines; rerun when Coding's scaled sim and baselines land. `release/v0.1/` and frozen results were not touched.

| file | protocol section | content |
|---|---|---|
| `regression_gate_seed0-2.json` | §0 | seeds 0–2 rerun vs frozen `results/benchmark/production/T2_episodes.jsonl`: 1350 values, max |Δ| = 0 → PASS |
| `T2_per_seed_seed0-2.md` | §0 / §4 appendix | earlier per-seed table (seeds 0–2, read from frozen file) |
| `T2_v01scale_20seed.{md,json}` | §1, §2 (stats), §4, 口径补正 1–4 | headline E/Q vs π (20 seeds, paired bootstrap 10k, Holm), Q = unweighted mean over present tail rounds (Q_swap, Q_theft, simple average), tail-trade run fraction per policy×π, bandit degradation vs π=1, pairwise diffs, ΔJ appendix, π* rule, per-seed crossovers |
| `T2_v01scale_E_vs_pi.png`, `T2_v01scale_E_vs_pi_zoom.png`, `T2_v01scale_Q_vs_pi.png` | §4 headline | curves with 95% CI bands |
| `T2_v01scale_pareto_EQ.png` | §1 main figure, 口径补正 2 | (E,Q) with 95% CI crosses at π=1 and π=0.1; hollow = most runs have no tail trade (Q not identifiable as deterrence) |
| `Q_gate_v01scale.json` | appendix only (口径补正 3, 5) | hedge-learner Q-ranking check — NOT the formal gate; formal gate later with EXP3 / fictitious play, per π, at 40-seller scale |
| `A2_compliance_control.{md,json}` | §6 | filter ON vs OFF: violation / fill / blocked-filtered rates |
| `raw/*.jsonl` | — | per-run rows (T2 egreedy, T2 hedge, A2) |
| `_group_draft.md` | — | Chinese summary for the project group (draft, not posted) |

Q definition follows the 2026-11-10 口径补正 at the end of the protocol (no token weighting). Table note for every T2 table: v0.1 scale (3 sellers), to be replaced by the 40-seller main table.

Reproduce (≈25 s on 8 cores):
```
/workspace/tmvenv/bin/python scripts/v1/run_v1_t2_a2.py   # §0 gate (stops if fail), T2 20 seeds, A2
/workspace/tmvenv/bin/python scripts/v1/run_q_gate.py      # hedge appendix check (not the formal gate)
/workspace/tmvenv/bin/python scripts/v1/recompute_q_v1.py  # apply fixed Q definition (口径补正) to raw/, recompute stats
/workspace/tmvenv/bin/python scripts/v1/make_report_v1.py  # md + png
```
Wrappers live in `scripts/v1/` and call the existing simulator (`run_single`, `run_benchmark_tasks._episode`); no core code was changed.
