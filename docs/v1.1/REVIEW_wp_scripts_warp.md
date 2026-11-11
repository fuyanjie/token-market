# Independent WP1/WP2 script review and WP2 convergence analysis

Date: 2026-11-11. Repository: `/workspace/token-market`, branch `v1.1`.
Local HEAD: `a98d43a5822a25967849e3a17613af3f1687d598`. No new commit was created; deliverables remain uncommitted. No git push was performed.

## Part A: verdicts

### `scripts/v1.1/analyze_wp1.py`: OK; no published number changes

Reviewed against frozen PROTOCOL §0 and §1.2, and independently recomputed every contrast and Holm adjustment.

- Same-seed treatment-minus-a0 differences are constructed for seeds 0–19, with router, penalty and pi held fixed. The cascade+trust control has its own router label and baseline, so it cannot collide with cascade.
- Bootstrap resamples the 20 paired differences, B=10000; intervals are the 2.5th/97.5th percentiles. Two-sided p is `min(1, 2*min(mean(bootstrap_mean<=0), mean(bootstrap_mean>=0)))`; ties are included. This matches the script's explicitly documented bootstrap convention.
- Report families are router × learner × pi, all (audit, penalty) contrasts, E and Q together. There are 10 families: nine of size 42 and cheapest of size 21. All runs use egreedy, so the learner is correctly constant in family keys.
- Decision-A contains exactly 28 tests: PILOT + strongest, P=0.25, pi=1, seven nonzero audit settings × two metrics × two routers. P/16 is excluded. P/16 remains in the report families, as required, but cannot support the efficacy conclusion.
- Q testability requires both treatment and baseline to have strategic-tail-trade run share strictly greater than 50%. All 21 cheapest Q contrasts are excluded from Holm and significance decisions; E remains testable. The script computes descriptive Q differences/raw p even when unidentifiable, but flags them untestable, leaves Holm p null, and does not use them in decisions.
- The diagnostic write-up does not declare Decision A from 48-round egreedy alone.
- All 4800 rows, 240 cells, seed coverage, and listed cell means pass checks. Largest cell-mean reconstruction difference is 2.220446049250313e-16.
- Executed the analysis with all output writes captured in memory: `wp1_eval.json`, `wp1_eval.md`, and `contrasts.csv` each reproduce the existing files byte-for-byte. Published report SHA256 matches the supplied checksum.

No correction is needed; no `wp1_eval_fix/` was created and `wp1_eval/` was not overwritten.

### `scripts/v1.1/run_wp2.py`: OK; output is valid for analysis

- Verified the exact Cartesian grid: 3 routers × 3 learners × 3 horizons × 20 seeds = 540 unique runs; completion and manifest agree.
- All cells are frozen WP1 PILOT/strongest/cascade at a=0.1, P=0.25, pi=1, trust_feedback=false, identity+length checks, fixed audit rule. Cascade+trust is not substituted.
- Learners are egreedy, fictitious_play, exp3; horizons are 48/200/500; seeds are 0–19 in every group.
- `cell_config` delegates to `scale_horizon`: tasks are 480/2000/5000, with budget multipliers 2.0/8.333333333333334/20.833333333333332. Rebuilt all 540 configurations and matched their SHA256 exactly.
- Q windows are half-open Q3=[n−2k,n−k), Q4=[n−k,n), k=max(1,int(n*0.25)). `intent_window` first averages each enabled seller/mode over present rounds, then averages sellers within each mode, then averages available modes, matching `tokenmarket.v1_metrics.intent`. Suspended/delisted rounds and missing history are treated consistently. This is not a pooled seller-round or trade-weighted average.
- Q4 equals official Q exactly for 540/540 runs. Stored Q3−Q4 equals the direct difference for 540/540. All CSV/JSONL fields and stored trajectory segments agree; all 27 listed group means and tail counts agree.
- Synthetic aggregation tests compare Q3/Q4 to official `intent` at all three horizons, including unequal mode counts, multi-mode sellers, delistings, and shortened histories.
- All 60 R48 egreedy runs match the corresponding official WP1 cell/seed across every one of the 52 shared fields, including configuration hashes and tail seller counts.
- `per_round_q` is only a diagnostic trajectory and uses a different seller-first average. The runner correctly does **not** average it to obtain segment Q; the new analyzer likewise uses the official segment columns.

No result-affecting bug found. Neither reviewed script was modified.

## Part B: convergence analysis

New implementation: `scripts/v1.1/analyze_wp2.py`.

For each group, compute d(seed)=Q3(seed)−Q4(seed), retaining all 20 seeds, and bootstrap the seed differences B=10000. Report 95% percentile CI; pass only if the whole CI lies inside the inclusive [−0.05,0.05] margin and Q is identifiable. Bootstrap RNG is deterministic: SHA256 of `20261111:<router>:<learner>:R<n>`, first eight bytes interpreted little endian, NumPy default_rng. No Holm or zero-null significance rule is substituted for this equivalence criterion. JSON includes descriptive two-sided bootstrap p, all seed differences, and input hashes.

**Recommended n_rounds: none among {48,200,500}.** PILOT egreedy fails all three horizons; at 500 rounds its upper CI bound is 0.055143, still above 0.05. PILOT fictitious_play fails at 48 and passes at 200/500. All strongest and cascade groups pass. Overall 23/27 groups pass, and every group is Q-identifiable; cascade tail-trade counts are observed rather than presumed unidentifiable.

EXP3 passes the convergence criterion on both decision routers at every horizon. Thus the §1.3 EXP3-nonconvergence exclusion is **not triggered** here. If EXP3 did not converge, its results would still be reported but excluded from direction consistency, requiring both egreedy and fictitious_play. That exception would not itself relax §2's three-learner recommendation rule. EXP3 Q remains approximately 0.5: passing this stability criterion is not evidence of learning a low-attack policy or of deterrence.

No Decision-A efficacy conclusion is made, and no alternate horizon is selected by relaxing the frozen margin. Any further horizon or protocol change needs a separate decision. The same 80-task pool is recycled: 200/500 rounds repeat tasks about 25/62 times (62.5 on average at 500), not new task diversity.

### All 27 groups

E, Q, Q3 and Q4 are unweighted 20-seed means. Tail runs means last-quarter strategic-tail-trade runs; Q id. requires >10/20. Decisions use full precision, not the rounded entries below.

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

## Validation and reproduction

- `PYTHONDONTWRITEBYTECODE=1 /workspace/tmvenv/bin/python scripts/v1.1/analyze_wp2.py`
- `PYTHONDONTWRITEBYTECODE=1 /workspace/tmvenv/bin/python -m pytest -q -p no:cacheprovider results/v1.1/wp2_eval/test_review.py tests/test_wp1.py --basetemp=/workspace/token-market/results/v1.1/wp2_eval/pytest_tmp`
- Result: **47 passed in 4.43s**. Tests cover all WP1 contrasts, independent Holm calculations, synthetic official-Q aggregation, independent sequential bootstrap resampling, invalid pairs, strict >50% identifiability, cascade exclusion, and smallest/no-recommendation cases.
- New Python sources passed AST syntax parsing. `git diff --check` passed; no configured lint/typecheck command exists in `pyproject.toml`.
- Reran analysis; both output checksums were identical. All 552 input hashes recorded in JSON still matched after validation.
- Frozen protocol and published WP1 report checksums match the supplied values. No writes were made to the protocol, raw WP1/WP2 directories, v1.0 results, release, or published WP1 evaluation directory.
- Existing untracked `run_wp2.py`, `wp2/`, `wp2_dry/`, and `wp2_smoke_r48s0/` were left in place. New files are the analysis script, this note, and artifacts/tests under `wp2_eval/`. Test temporary files are confined there.

## Paths and SHA256

- `scripts/v1.1/analyze_wp2.py`: `60ebb7c83a1b0be7550fb1f79fe69c23fd6a0b2a0f21aaad692bb9b299eacc21`
- `results/v1.1/wp2_eval/wp2_eval.md`: `4dec21cff6e7c90155528086d98a16bdcedc5159d333c551b96f753e7d16d12e`
- `results/v1.1/wp2_eval/wp2_eval.json`: `906c0de6edf4360b0259b093135d91183722dc2ff2f8e6926a7bba8e06ba1758`
- Corresponding checksum files: `results/v1.1/wp2_eval/wp2_eval.md.sha256` and `results/v1.1/wp2_eval/wp2_eval.json.sha256`.
- `results/v1.1/wp2_eval/test_review.py`: `200b34ad8b5da7249aa27ebb125d2b0b5482e6a0ae2518290b348e6fc21b7db9`
- Unchanged `docs/v1.1/PROTOCOL_v1.1.md`: `e9c84494a7031d7023d4861c02a5786a59fbc74541007978a13b9882f209c179`
- Unchanged published `results/v1.1/wp1_eval/wp1_eval.md`: `95f84e6ef716140cfba470c68ab7bd0f9bd1431e7ff73bcc8a4c063d1b7847fc`
- Local commit/HEAD remains `a98d43a5822a25967849e3a17613af3f1687d598`; these new deliverables are not in a commit.
