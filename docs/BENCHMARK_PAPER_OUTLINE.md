# Reasoning-Token Market Benchmark — English Outline (Datasets & Benchmarks track)

**Working title.** A Compliance-Constrained Reasoning-Token Market Simulator and Benchmark for Procurement under Sparse Audit Feedback

**Claim (locked).** We release a *platform* that simulates cross-border *reasoning-service* trades (not a CLOB), plus a fixed evaluation protocol. Primary board: **active attack rate (q\*)** and **realized fraud share**. Immediate-feedback J vs PILOT/StageRoute is **not** the primary ranking. Deterrence-method novelty stays in the companion methods paper; this paper’s contribution is the **platform + protocol + baselines**.

**Venue.** NeurIPS / ICLR Datasets & Benchmarks (or equivalent data/benchmark track). Workshop fallback if full D&B cycle missed.

---

## 1. Introduction (≈1–1.5 pp)
- Cross-border LLM/API procurement: quality revealed late; jurisdictions constrain routing; sellers can swap/theft.
- Gap: existing market sims = CLOB microstructure or bandit routing with instant labels; neither couples **compliance + strategic fraud + sparse/delayed labels + escrow/audit**.
- Contribution bullets:
  1. Five-layer trading platform (admission → routing → escrow → oversight → feedback/trails).
  2. Publishable five-file JSONL schema + one-click scripts.
  3. Tasks T1–T3 with fixed seeds; primary metrics q\* / fraud_share; π\*∈(0.10,0.12) regime switch as protocol result.
  4. Baselines: PILOT, StageRoute, fixed-a audit (D3), random audit; adaptive/delist as appendix switches.

## 2. Related Work (≈1 pp)
- Cloud/API marketplaces & SLA disputes; ad quality audit; prediction-market dispute resolution.
- Bandit / portfolio routing (PILOT, StageRoute) under *immediate* feedback.
- Exchange surveillance / escrow economics (what we borrow) vs order-book microstructure (what we do **not**).
- Position vs companion methods paper: here = generator + leaderboard; there = deterrence theory.

## 3. Platform Design (main section, ≈3–4 pp) — Figure 1
Five layers (code map in `docs/DATA_SCHEMA.md`):
1. **Admission/compliance** (`gateway`, `compliance`): jurisdiction hard filters.
2. **Routing / portfolio procurement** (`matching`, `portfolio`, `buyers`, `baselines`): plugins, **not** a limit order book.
3. **Escrow settlement** (`sim`, `audit_v6`): `locked → delivered → audited? → settled/slashed` (default off for legacy F/J).
4. **Oversight** (`strategic`, `audit_v6`): fixed audit rate *a* (main path); optional adaptive boost & delist.
5. **Feedback & trails** (`feedback`, `logging_schema`): label channel (π, L) orthogonal to payment escrow.

External API surface: place order, delivery receipt, audit verdict, settlement, trail query.

**Design principles.** Borrow audit economics (sampling, slash, freeze); do **not** port CLOB, HFT, circuit breakers, multi-CCP.

## 4. Data Release (≈1.5–2 pp) — Table 1
Shipped v1 files under `exports/latest/`:
| File | Role |
|---|---|
| `sellers.jsonl` | Catalog + latent q, stake, ban watermark |
| `buyers.jsonl` | Budget, strategy_id, compliance_profile |
| `orders.jsonl` | State-machine fact table (join key `order_id`) |
| `audits.jsonl` | Sampled checks, slash, delist, π/L reveal |
| `episodes.jsonl` | **Primary board** row per (run_id, seed) |

Join keys: `run_id`, `seed`, `order_id`, `config_hash`.  
Derived (not shipped): ledger/event timeline = `orders ⋈ audits`.  
Label hygiene (v1): shipped `orders.attack_mode` / `correct` and `sellers.actual_model` / `latent_q_*` are **evaluation labels**, not public training features—v1 exports are **not** safe as a supervised fraud-detection training set without a hold-out split. Optional `labels.jsonl` + Feature/Label section in `DATA_SCHEMA.md` land in v1.1; default five files stay `sellers/buyers/orders/audits/episodes`.

One-click:
`scripts/export_benchmark_layers.py`, `run_benchmark_tasks.py`, `run_leaderboard.py`.

## 5. Benchmark Protocol (≈2 pp)
**T1 — Fixed-a deterrence.** Main board: active_attack_rate + fraud_share under fixed *a* (default 0.1).  
**T2 — Sparse-label regime.** Sweep π (dense grid around 0.05–0.20); report crossover **π\*∈(0.10,0.12)** where D3’s J exceeds StageRoute *as a regime switch* (bandit collapse), not as “D3 wins under full feedback.” L grid already fixed; no need to re-sweep for outline claims.  
**T3 — Audit-cost efficiency (appendix).** Same expected budget: fixed vs adaptive; report fraud/J vs n_audits; **not** primary novelty.

Baselines: StageRoute+compliance, PILOT+compliance, fixed-a D3, random audit.  
Seeds / `config_hash` frozen in `episodes.jsonl`. Default switches off so legacy F/J reproducible.

## 6. Platform Capability Results (≈2 pp) — not method ablations as novelty
- T1 table: q\* locked ~0.08 under D3 across π; bandits’ q blows up when π≤0.10.
- T2 figure: J crossover at π\*; narrative = deterrence independent of label density.
- Appendix: delist trade-off (realized fraud↓, J↑; learned q may rise from missing observations); adaptive vs fixed under equal budget.
- Reproducibility: 74 pytest; smoke leaderboard command.

## 7. Limitations
- Single-platform auditor / no multi-buyer congestion (explicit).
- No CLOB; posted prices + routing only.
- Synthetic / cached model answers mixed with mechanism sim — document which fields are mechanism vs model cache.
- Adaptive audit & long delist are optional cost/ops knobs, not claimed SOTA over instantaneous bandits.

## 8. Conclusion
Platform-as-benchmark-generator for compliance-constrained reasoning-token trade under sparse audit feedback; invite leaderboard submissions on T1–T2 primary metrics.

## Checklist for first draft
- [ ] Fig.1 five-layer diagram (from Idea mermaid + Coding file map)
- [ ] Table schema excerpt + 3-row samples (from `DATA_SCHEMA.md`)
- [ ] T1/T2 numbers from `results/pi_dense/` + `exports/latest/episodes.jsonl`
- [ ] Related-work table (Survey to fill: ad audit, cloud API, prediction markets)
- [ ] Feature/Label leakage disclaimer (v1 not for supervised fraud train set; labels.jsonl in v1.1)
- [ ] Ethics / synthetic-data statement
- [ ] Companion methods paper cross-cite (deterrence claim ownership)

*Outline synced to shipped v1 (2026-11-08). If Idea’s `events`/`labels` split lands later, move to §4.1 optional release without changing primary board.*
