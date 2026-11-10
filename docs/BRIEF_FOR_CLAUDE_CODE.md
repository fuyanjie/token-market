Brief for Claude Code: Cross-Border D&B paper, target KDD 2027 Datasets & Benchmarks

Please judge our next steps and what is missing for submission. Keep the frozen v0.1 claims. Do not turn this into a methods paper.

PROJECT
Cross-Border Reasoning Token Markets: a compliance-constrained reasoning-token procurement simulator and benchmark.
Paper v0.1 (claims frozen): "A Compliance-Constrained Reasoning-Token Market Simulator and Benchmark for Procurement under Sparse Audit Feedback".
Contribution = platform + publishable data schema + fixed evaluation protocol + baselines. Deterrence-method novelty belongs to a separate, unwritten companion methods paper.

SOURCES
- Google Doc: https://docs.google.com/document/d/1XyZTK-m52onncOKfWbuyhK9FrTlb44_y5MOlourdzlc/edit
- PDF: https://drive.google.com/file/d/13tN1X1vZ0XDpECSwAukJBN9056eHtbNj/view
- Repo: docs/BENCHMARK_PAPER_DRAFT_v0.1.md, docs/refs.bib, docs/figures/fig1_five_layers.png, docs/figures/fig2_pi_star_crossover.png, frozen pack release/v0.1/ (do not overwrite)

FROZEN CLAIMS (do not strengthen)
- Five-layer posted-price platform, not a limit-order book: admission/compliance, routing/portfolio procurement, escrow settlement, oversight audit, feedback/audit trails.
- Five-file JSONL schema with Feature/Label hygiene rules.
- Tasks: T1 fixed-rate audit deterrence; T2 sparse-label regime switch; T3 equal-budget adaptive audit (appendix only; delist also appendix only).
- Primary leaderboard: active_attack_rate and fraud_share only. learned_q_* are side columns. J is secondary; never claim beating PILOT on J.
- Regime crossover pi* in (0.10, 0.12): under sparse labels bandit avoidance collapses; fixed-rate audit keeps q* near 0.08.
- Appendix D maps RQ coverage: A2 = basic coverage, A1 = weak. Strong provenance, resale/rewrite/distill, auctions, multi-buyer congestion = v1.1, out of scope.

KNOWN GAPS
- Only seeds {0,1,2}; pi* rests on a sign change between grid points 0.10 and 0.12, with no intervals.
- A2 and weak A1 have no result tables yet.
- No leak-safe fraud-detection / label-leakage check yet.
- Draft header still says "NeurIPS / ICLR"; the section 6.1 table leads with secondary J, so the body can read like a J-ranking paper.
- Converting to SIGKDD LaTeX on Overleaf is in progress.

VENUE: KDD 2027 Datasets & Benchmarks Track
https://kdd2027.kdd.org/datasets-and-benchmarks-track-call-for-papers/
Single-blind (authors shown); \documentclass[sigconf,review]{acmart}; max 8 self-contained content pages, then references and an unlimited appendix. Cycle 1 closed; Cycle 2 dates not posted.

TWO CANDIDATE PLANS (neither approved or started)
Plan E (Experiment):
1. Seeds to 0-5; mean and interval of delta-J at each pi; check crossover per seed stays in (0.10, 0.12); add intervals to T3/delist appendix tables.
2. Appendix sweep of audit rate a: does attack rate fall with a; does D3 q* stay insensitive to pi.
3. A2 violation/reachability table; weak-A1 trail completeness; leak-safe fraud detection (train on features, test on labels.jsonl).
Plan I (Idea):
1. Harden T2: seeds 0-9, intervals at pi = 0.10 and 0.12, small robustness scan (delay L, audit rate a, swap vs theft separately). If pi* holds only in the original setting, report it as a conditional interval, not a general law.
2. Freeze A2 as one task card (violation rate, fill rate) using existing basic compliance rules only.
3. Feature/Label leakage contrast: hygiene-compliant training vs. misuse of forbidden columns, to show the default export must not be used as a fraud-detector training set. A hygiene check, not a new detector.
Both: no new audit/deterrence algorithm, no J race vs PILOT, no v1.1 items, at most one or two new tables in the 8-page body.

QUESTIONS
1. Which plan (or which merge of the two) is the best next step for a KDD D&B paper, in what order?
2. What else is missing for a strong, self-contained 8-page KDD D&B submission (body, data/release, documentation, reproducibility)?
Do not recommend changing the primary leaderboard or moving method novelty into this paper.
