# Cross-Border v1.1 WP2 convergence analysis

**No recommended n_rounds:** no tested horizon satisfies all three learners on both PILOT and strongest.

EXP3 converges on both decision routers at 500 rounds; the §1.3 nonconvergence exclusion is not triggered at that horizon.

## Method

All cells use a=0.1, P=0.25, pi=1, trust_feedback=false; 20 seeds (0–19). Per seed d=Q3−Q4. Resample the 20 paired differences B=10000 times; report the 2.5/97.5 percentiles of mean d. A CI must lie wholly inside the inclusive [−0.05, 0.05] bounds; containing zero alone is insufficient. Deterministic RNG: base 20261111, group-specific SHA256 seed (see JSON). All 20 differences are retained; missing/nonfinite pairs abort rather than silently reduce the sample.

Q identifiability uses the final-quarter trade share >50%; unidentifiable cells are descriptive only and cannot pass convergence. Cascade never selects the recommended horizon: only PILOT and strongest, all three learners, determine it. Two-sided bootstrap p values in JSON are descriptive only; convergence uses no null-significance test, Holm adjustment, or test against zero.

The 80-task pool is reused: 200/500 rounds repeat each task about 25/62 times (62.5 on average at 500); effective task diversity remains 80. These results are horizon diagnostics, not the audit-grid Decision-A experiment.

## All groups

| router | learner | rounds | E | Q | Q3 | Q4 | tail runs | Q id. | mean Q3−Q4 [95% CI] | converged |
|---|---|---:|---:|---:|---:|---:|---:|---|---|---|
| pilot | egreedy | 48 | 0.103785 | 0.434769 | 0.517037 | 0.434769 | 20/20 | yes | 0.082269 [0.051250, 0.115139] | no |
| pilot | egreedy | 200 | 0.048577 | 0.285567 | 0.320400 | 0.285567 | 20/20 | yes | 0.034833 [0.011189, 0.059578] | no |
| pilot | egreedy | 500 | 0.033808 | 0.236373 | 0.264707 | 0.236373 | 20/20 | yes | 0.028333 [0.002480, 0.055143] | no |
| pilot | fictitious_play | 48 | 0.103468 | 0.449411 | 0.535832 | 0.449411 | 20/20 | yes | 0.086421 [0.046868, 0.126421] | no |
| pilot | fictitious_play | 200 | 0.044264 | 0.262771 | 0.294418 | 0.262771 | 20/20 | yes | 0.031647 [0.018663, 0.045762] | yes |
| pilot | fictitious_play | 500 | 0.023818 | 0.167570 | 0.177088 | 0.167570 | 20/20 | yes | 0.009518 [-0.002152, 0.022120] | yes |
| pilot | exp3 | 48 | 0.110443 | 0.501065 | 0.509583 | 0.501065 | 20/20 | yes | 0.008519 [-0.007640, 0.024862] | yes |
| pilot | exp3 | 200 | 0.091823 | 0.506133 | 0.499489 | 0.506133 | 20/20 | yes | -0.006644 [-0.016911, 0.003678] | yes |
| pilot | exp3 | 500 | 0.082896 | 0.501716 | 0.498773 | 0.501716 | 20/20 | yes | -0.002942 [-0.007791, 0.002062] | yes |
| strongest | egreedy | 48 | 0.145656 | 0.367083 | 0.385185 | 0.367083 | 20/20 | yes | 0.018102 [-0.003611, 0.040787] | yes |
| strongest | egreedy | 200 | 0.076727 | 0.236489 | 0.253589 | 0.236489 | 20/20 | yes | 0.017100 [-0.002000, 0.036979] | yes |
| strongest | egreedy | 500 | 0.056748 | 0.234720 | 0.248178 | 0.234720 | 20/20 | yes | 0.013458 [-0.000205, 0.027054] | yes |
| strongest | fictitious_play | 48 | 0.140677 | 0.332809 | 0.357841 | 0.332809 | 20/20 | yes | 0.025031 [0.008882, 0.041897] | yes |
| strongest | fictitious_play | 200 | 0.062735 | 0.229764 | 0.259434 | 0.229764 | 20/20 | yes | 0.029670 [0.015925, 0.043528] | yes |
| strongest | fictitious_play | 500 | 0.053033 | 0.241945 | 0.251074 | 0.241945 | 20/20 | yes | 0.009129 [-0.001462, 0.019741] | yes |
| strongest | exp3 | 48 | 0.250135 | 0.500417 | 0.508843 | 0.500417 | 20/20 | yes | 0.008426 [-0.007037, 0.025094] | yes |
| strongest | exp3 | 200 | 0.241724 | 0.506933 | 0.499900 | 0.506933 | 20/20 | yes | -0.007033 [-0.017122, 0.003411] | yes |
| strongest | exp3 | 500 | 0.242095 | 0.499644 | 0.498053 | 0.499644 | 20/20 | yes | -0.001591 [-0.006471, 0.003667] | yes |
| cascade | egreedy | 48 | 0.004727 | 0.538333 | 0.528657 | 0.538333 | 13/20 | yes | -0.009676 [-0.031759, 0.014444] | yes |
| cascade | egreedy | 200 | 0.003267 | 0.490378 | 0.490411 | 0.490378 | 19/20 | yes | 0.000033 [-0.011700, 0.012511] | yes |
| cascade | egreedy | 500 | 0.002085 | 0.485102 | 0.490102 | 0.485102 | 20/20 | yes | 0.005000 [-0.005951, 0.018640] | yes |
| cascade | fictitious_play | 48 | 0.003675 | 0.519592 | 0.513136 | 0.519592 | 12/20 | yes | -0.006456 [-0.018578, 0.005666] | yes |
| cascade | fictitious_play | 200 | 0.002935 | 0.487974 | 0.484549 | 0.487974 | 19/20 | yes | -0.003426 [-0.009336, 0.001941] | yes |
| cascade | fictitious_play | 500 | 0.002005 | 0.491438 | 0.490531 | 0.491438 | 20/20 | yes | -0.000907 [-0.009368, 0.006791] | yes |
| cascade | exp3 | 48 | 0.003787 | 0.500833 | 0.508750 | 0.500833 | 12/20 | yes | 0.007917 [-0.008796, 0.024861] | yes |
| cascade | exp3 | 200 | 0.003735 | 0.506611 | 0.499978 | 0.506611 | 19/20 | yes | -0.006633 [-0.016456, 0.003178] | yes |
| cascade | exp3 | 500 | 0.003774 | 0.501338 | 0.499373 | 0.501338 | 20/20 | yes | -0.001964 [-0.007107, 0.003116] | yes |

## Validation

{
  "runs": 540,
  "groups": 27,
  "seeds_per_group": 20,
  "Q4_equals_official_Q_exactly": 540,
  "WP1_R48_shared_field_matches": 60,
  "config_hashes_recomputed": 540,
  "trajectories_checked": 540,
  "csv_jsonl_equal": true,
  "summaries_equal": true
}

All input SHA256 values (including 540 trajectories) are recorded in wp2_eval.json. Q4 equals official Q exactly for 540/540 runs; the 60 egreedy R48 runs match every WP1 shared field. Configuration hashes are independently reconstructed with frozen cell_config/scale_horizon. No raw runs were modified.
