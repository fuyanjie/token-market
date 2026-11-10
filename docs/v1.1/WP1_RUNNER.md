# Frozen WP1 runner and horizon scaling
Use the new runner, not `scripts/run_v1.py`, for the router × audit factorial. It inherits `configs/v1.0/scale.yaml` without modifying it, checks the frozen protocol checksum, and applies v1.1 overrides after loading the base configuration.
## Official WP1 (Experiment only)
Run from the repository root with the project interpreter. First enumerate without running any simulation:
```bash
/workspace/tmvenv/bin/python scripts/v1.1/run_wp1.py --dry-run --out results/v1.1/wp1_plan
```
Execute the complete diagnostic grid in a different fresh directory:
```bash
/workspace/tmvenv/bin/python scripts/v1.1/run_wp1.py --out results/v1.1/wp1 --jobs 8 --log-transactions
```
The default is seeds 0–19, egreedy, 48 rounds, 480 tasks. Routers are cascade, PILOT, StageRoute, strongest, cheapest; only PILOT and StageRoute vary π over {1, 0.1, 0}. All other arms have π=1. Every router has audits {0, 0.01, 0.02, 0.03, 0.05, 0.10, 0.20, risk-adaptive} and penalties {0.25, 0.0625, 0.015625}. No cell selection or diagnostic parameter changes are permitted in official mode.
All factorial cells have trust_feedback=false. The `cascade+trust` control uses the same audit × penalty grid at π=1 but enables the existing TrustModel; it is saved separately, not mixed into factorial cells. All arms use identity+length inspections, zero delisting, no escrow, and the existing risk-adaptive rule rather than the older budget-constrained adaptive allocator. Risk-adaptive rate is seller-specific with the inherited frozen prior and bounds; its nominal rate flag enables the audit path, not a fixed realized audit budget.
Audits still affect seller profits/learning and buyer budgets. Thus observed routing sequences can change indirectly; trust_feedback=false means no router reads audit outcomes, not that full trajectories must be identical across audit levels.
## Outputs and interpretation
- `manifest.json`: every planned cell, router, audit, penalty, π, arm, and trust setting.
- `run_meta.json`: seeds, tasks, rounds, scaled budget multiplier, base config, backend selection, source commit, protocol hash, and invocation.
- `completed_runs.jsonl`: durable per-run metrics as each run finishes; no automatic resume or post-hoc dropping.
- `factorial/per_seed.csv` and `control/per_seed.csv`: E, E_tok, Q, per-mode Q (also q_swap/q_theft/q_downgrade), accuracy, cost/task including audit, audit diagnostics, fill rate, tail trade indicator/count and per-seller tail counts. Raw transactions are optional.
- `factorial/cells.json` and `control/cells.json`: plain cell means, run count with strategic tail trades, per-run tail counts, and Q_identifiable (strictly more than half of runs have a strategic tail trade).
- `completion.json`: written only on successful completion. Compare its completed-run count with the planned count before analysis.
P/16 cells are retained and marked `penalty_label="P/16"` and `audit_efficacy_evidence_allowed=false`. They cannot be evidence that audit works. Q is reported even when not identifiable; do not use such cells for significance or deterrence claims. These outputs do not compute paired bootstrap, Holm families, Decision-A, or convergence tests: Experiment must apply the frozen protocol. All inspection settings differ from some non-cascade v1.0 paths; do not directly compare their values without noting that change.
## WP2 horizon pairing / later learner reruns
`tokenmarket.wp1.scale_horizon(base, n_rounds)` is the single pairing helper used by every runner cell. It sets n_tasks=10*n_rounds and multiplies the reference buyer budget multiplier by n_tasks/480. Repeated application does not compound scaling. Do not independently override n_tasks.
For longer-horizon or Decision-A preparation, `--mode followup` accepts `--n-rounds 48`, `200`, or `500` and `--learner egreedy`, `fictitious_play`, or `exp3`. It keeps frozen WP1 cell definitions; this is not an automatic WP2 convergence-grid enumerator. For example, to enumerate a longer-horizon cell without running it:
```bash
/workspace/tmvenv/bin/python scripts/v1.1/run_wp1.py --mode followup --n-rounds 200 --learner egreedy --cell pilot__a0__P0.25__pi1 --dry-run --out results/v1.1/wp2_pilot_200_plan
```
Removing `--dry-run` executes that selection; choose a fresh directory. Experiment owns the WP2 router/cell selection and convergence analysis; this CLI only supplies frozen WP1 cell definitions and automatic task/budget pairing for followups. Task-pool diversity is unchanged by increasing tasks: cached synthetic prompts repeat, not new independent model generations. Tail counts use the same last quarter of rounds as Q.
## Tiny smoke only
Smoke mode enforces one seed, at most two explicit cells, and at most four rounds; backend mocking is available only here:
```bash
/workspace/tmvenv/bin/python scripts/v1.1/run_wp1.py --mode smoke --seeds 0 --n-rounds 4 --cell pilot__a0.1__P0.25__pi1 --cell cascade+trust__a0.1__P0.25__pi1 --backend-override mock --log-transactions --out results/v1.1/wp1_smoke
```
Output directories must be fresh/empty and resolve under `results/v1.1/`, including symlink resolution. No legacy result/release directory is written by this runner. Existing runs are never overwritten.
