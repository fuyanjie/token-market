# v1.0 baselines (protocol §3): what is implemented, and how it deviates from the papers

All methods are selected by name through `tokenmarket/registry.py` (`scripts/run_v1.py --methods ...`).
The v0.1 policy ids (`pilot*`, `stageroute*`, `audited_compliance_cascade`, …) are unchanged and still reproduce the
v0.1 numbers (guarded by `tests/test_v1_infra.py::test_v01_numbers_unchanged`). The faithful reimplementations run
under new policy ids (`pilot_v1*`, `stageroute_v1*`).

| registry name | policy id | label in tables | family |
|---|---|---|---|
| `pilot` | `pilot_v1_compliant` | PILOT (Panda et al. 2025), faithful reimpl. | bandit router |
| `stageroute` | `stageroute_v1_compliant` | StageRoute (Li & Li 2025), faithful reimpl. incl. MIP | bandit router |
| `pilot_v01`, `stageroute_v01` | `pilot_compliant`, `stageroute_compliant` | v0.1 simplified reimpls (kept for comparison) | bandit router |
| `cheapest_fixed` | `single_cheapest_compliant` | cheapest fixed router | fixed router |
| `strongest_fixed` | `single_best_compliant` | strongest fixed router (highest listed quality) | fixed router |
| `random_audit` | `audited_compliance_cascade` + `audit_rule: random` | random-intensity audit (a_t ~ U(0, 0.2)) | audit |
| `fixed_audit_a0.05/0.10/0.20` | `audited_compliance_cascade` + `audit_rate` | fixed-rate audit reference baseline (a=…) | audit |
| `risk_adaptive_audit` | `audited_compliance_cascade` + `audit_rule: risk_adaptive` | risk-adaptive audit | audit |

Aliases: `d3`, `D3`, `audited_compliance_cascade`, `fixed_audit` → `fixed_audit_a0.10`. Per protocol §3, D3 is
labelled the **fixed-rate audit reference baseline** and is not presented as this paper's method. That D3 is
insensitive to π is true by construction, because audits do not use the outcome-label channel. It is not a finding.
All routers and fixed routers use the hard compliance filter (`*_compliant`). `market.compliance_filter: false`
(A2, `run_v1.py --no-compliance-filter`) removes the filter for every method.

Sources were read on 2026-11-10 from the arXiv abstract and HTML pages: https://arxiv.org/abs/2508.21141 and
https://arxiv.org/html/2508.21141 (v2) for PILOT, and https://arxiv.org/abs/2506.17254 and
https://arxiv.org/html/2506.17254 (v2) for StageRoute. Parts of both HTML pages were only available as a
model-written summary, not verbatim. Numbers taken from those parts are marked *(summary)* and should be checked
against the PDF before they are quoted in the paper.

---

## PILOT — Panda, Magazine, Devaguptapu, Takemori, Sharma. *Adaptive LLM Routing under Budget Constraints.* EMNLP 2025 Findings, arXiv:2508.21141.

**Paper algorithm**
1. Offline pretraining on ChatArena human preferences restricted to the 11 RouterBench LLMs. Phase 1 learns a
   projection ψ(q) = Wφ(q) + b of a frozen text embedding (OpenAI text-embedding-3-small) with a cosine triplet loss.
   Phase 2 learns LLM embeddings θ_i with p_i = exp(cos(θ_i, ψ(q))) / Σ_{k∈{i,j}} exp(cos(θ_k, ψ(q))) and BCE.
2. Online: E[r | a, q] = cos(ψ̂(q), θ̂_a) (Eq. 1). Ridge estimate θ̃ = A⁻¹b (Eq. 2). Updates A += ψ̂ψ̂ᵀ, b += r ψ̂.
   Prior A⁰ = λ_a I, b⁰ = λ_a θ_a^pref with λ_a = 1 / (pretraining accuracy of a). Selection is
   argmax cos(ψ̂, θ̃_a) + α √(ψ̂ᵀA⁻¹ψ̂).
3. Budget: ON-MCKP with the ZCL threshold (Algorithm 2), applied through binning (Algorithm 3, App. C.2):
   N = ⌈Q/S⌉ bins, B_bin = B/N, B_left += B_bin per bin, z reset per bin. Eligible arms are
   E = {l : C_l ≤ cos_l / ((UB·e/LB)^z · LB/e)}. If E is empty, fall back to {C_l ≤ B_left/Q_left}. If that is empty
   too, "insufficient budget". The chosen arm is l* = argmax_{l∈E} cos. Afterwards B_left −= C_l* and
   z += C_l*/B_bin.

**Implemented** (`tokenmarket/baselines.py::PilotV1Router`, `pilot_preference_prior`)
- Eq. 1, Eq. 2, the chosen-arm-only update, the prior with λ_a = 1/(mean listed accuracy of the claimed model) and
  Algorithm 3 follow the paper exactly. This includes the hard "insufficient budget" outcome, where no purchase is
  made. α = 2.0, which is the paper's best value from its grid {1, 1.5, 2, 5, 10} *(summary)*. n_bins = 4.

**Deviations, with reasons**
1. *No human preference data or text embeddings exist in a token market.* Phase 1 is replaced by our fixed,
   normalised hand-made context (difficulty one-hot, task type, log length, bias). Phase 2 is run as in the paper
   (BCE on the cos-softmax) on **synthetic preference tuples derived only from the public listing**. The soft label
   is P(i ≻ j) = acc_i(1−acc_j) + ½[acc_i·acc_j + (1−acc_i)(1−acc_j)], using the claimed models' listed accuracy
   at each pool query's difficulty. Embeddings are learned per *claimed model* and shared by every seller that
   claims it, so a model-swap seller inherits the prior. This is intended: buyers only see claims.
2. *No separate learning bucket.* The paper trains online on a learning bucket (learning:deployment = 10:1) and
   applies the budget policy at deployment. A live market has a single stream under budget. We therefore keep
   learning online throughout and select by UCB inside the ZCL-eligible set (`select: ucb`, the default).
   `select: greedy` uses Algorithm 3's plain argmax cos.
3. *UB / LB and the bin size S are not reported in the paper.* We use UB / LB = max / min over the market's sellers
   of listed accuracy / expected cost (price × claimed tokens), with S = ⌈Q/n_bins⌉. Both can be overridden via
   `market.pilot_v1`.
4. Reward is binary correctness, which matches the paper's thumbs-up framing. The paper's experiments use the
   continuous RouterBench score.
5. The compliance filter, strategic sellers, audits and delayed or sparse labels (π) are market extensions that
   are not in the paper.

**What the paper reports** (RouterBench, 11 LLMs, 36,497 queries)
- Multi-task: "93% of GPT-4's performance at just 25% of its cost". Single-task (MMLU): "86% of GPT-4 at only 27% of
  its cost" (Sec. 4, Fig. 3).
- Table 2 compares the cost policy with offline P−λC at budgets $0.25 / 0.50 / 1.00 / 1.50: PILOT scores
  0.6557 / 0.6840 / 0.7240 / 0.7814, against 0.6079 / 0.6602 / 0.7265 / 0.7740 for P−λC.
- Table 5 ablation at a $1 budget *(summary)*: PILOT 0.63, LinUCB 0.60, pretrained router only 0.34.

**Reproducing the paper's numbers.** This is not possible inside this repository. It would need RouterBench
responses, ChatArena preferences and OpenAI embeddings, none of which are in the token market. The gap is
therefore one of setting, not of implementation. The algorithmic pieces that can be checked in isolation are unit
tested: the prior, λ, Algorithm 3 binning, insufficient budget, and the chosen-arm update.

---

## StageRoute — Shaoang Li, Jian Li. *Near-Optimal Online Deployment and Routing for Streaming LLMs.* arXiv:2506.17254 (v2, 29 Jan 2026; arXiv comment: ICLR 2026).

**Paper algorithm** (equal-length stages, K of them, with K ≈ T^{1/3} recommended)
1. At each stage start, DeployOPT (Eq. 3), a MIP:
   max_{d,z} Σ μ^U_m d_m s.t. Σ c^L_m d_m ≤ b, Σ d_m = 1, 0 ≤ d_m ≤ α_m z_m, Σ z_m = min(M_max, |ℳ|), z ∈ {0,1}.
   The deployed set is 𝒟_k = {m : d*_m > 0} (Eq. 6).
2. Per query, RouteOPT (Eq. 7), an LP: max Σ μ^U p s.t. Σ c^L p ≤ b, Σ p = 1, 0 ≤ p ≤ α over 𝒟_k. Then sample
   m ~ p*.
3. Optimism: μ^U = proj_[0,1](μ̄ + 2 f_rad(μ̄, N+1)) and c^L = proj_[c1,c2](c̄ − 2 f_rad(c̄, N+1)), with
   f_rad(v, n) = √(γv/n) + γ/n.
4. Regret Õ(√(M_max K T) + NT/(M_max K)), which gives Õ(N^{1/3}T^{2/3}) with K = Θ(T^{1/3}) and
   M_max = Ω(N^{2/3}). There is an Ω(T^{2/3}) lower bound.

**Implemented** (`tokenmarket/baselines.py::StageRouteV1Router`, solvers in `tokenmarket/lp.py`)
- Equal stages with K = round(T^{1/3}) by default (T = queries per run; 480 queries gives K = 8).
  M_max = ⌈N^{2/3}⌉ by default (40 sellers gives 12).
- DeployOPT is solved **exactly as a MIP** by branch and bound over z, with a numpy two-phase simplex for the LP
  relaxations. RouteOPT uses the same simplex. Both are checked against brute force in the tests. scipy and Gurobi
  are not available in the pinned environment.
- Eq. 4–5 use the factor 2 and N+1. α_m = the seller's capacity share. γ = 0.1, the paper's experimental value
  *(summary, unverified)*. The theory uses Θ(log(NT/δ)).

**Deviations, with reasons**
1. *Deployed set.* Eq. 3 forces Σz = min(M_max, |ℳ|), but Eq. 6 deploys only supp(d*), which has at most about
   1/min α + 2 models. The paper leaves this open. In a compliance-filtered market a buyer whose compliant sellers
   miss supp(d*) would get nothing. We deploy supp(d*) and top it up with the remaining highest-μ^U sellers to
   n_deploy = min(M_max, N), so that it matches Σz.
2. *Budget per buyer.* The paper has a single budget stream with per-query budget b. Here RouteOPT uses each
   buyer's b = budget_scale · B_buyer / T_buyer, and DeployOPT uses the market-wide b̄ = ΣB / T.
3. *Market fallbacks* that are not in the paper: if no deployed seller is a compliant candidate for a query, route
   over all candidates; if RouteOPT is infeasible, pick the smallest-c^L arm (the v0.1 behaviour). Both are counted
   in `n_fallback_cands` and `n_fallback_infeasible`.
4. *c1, c2* are not reported in the paper. We use 0.25× the smallest and 4× the largest listed expected cost.
   Overridable.
5. *No model arrivals.* Every seller is listed from t = 1. Delisting by audits removes a seller from the candidate
   set but not from the deployed set.
6. The v0.1 `stageroute*` ids **skip the MIP**, use factor 1 with N instead of N+1, and use no cost projection.
   That is the "simplified reimplementation" protocol §3 asked us to replace.

**What the paper reports**
- Appendix E.1 uses RouterBench (36,497 queries, 8 datasets, 11 LLMs). Appendix E.2 uses a synthetic benchmark
  with 15 models, α = 0.4 (1 for Yi-Lightning), M_max ∈ {3, 5, 10}, update interval ∈ {250, 500, 1000} and
  b ∈ {2, 5} (Fig. 6). The headline Section 5 numbers and the baseline list could not be read verbatim. According
  to the summary they are an oracle, a greedy UCB-style selector and uniform random, over 10 runs, solved with
  Gurobi, with γ = 0.1, M_max = 5 and b = 0.001 $/query. **These must be checked against the PDF before any number
  is quoted.**

**Reproducing the paper's numbers.** As with PILOT, this is not possible without RouterBench and the authors'
model-arrival setup. The gap is one of setting. A RouterBench harness would be a separate task (open question in
the report).

---

## Audit baselines (`tokenmarket/audit_v1.py`)
All three share the D3 pipeline: compliance filter, budget, a confidence cascade, audit-trust-adjusted quality,
identity and length checks, and penalty P on a catch. Only the audit decision differs. Each uses its own RNG
stream, so the fixed-rate draws are unchanged.
- **fixed-rate audit reference baseline (a)**: every purchase is audited with probability a ∈ {0.05, 0.10, 0.20}.
  This is identical to v0.1 D3.
- **random audit**: at each round start a_t ~ U(0, 2a), with a = 0.1, clipped to [0, 1]. Each purchase in that
  round is audited with probability a_t. Expected rate a, but the intensity is unannounced and varies from round to
  round.
- **risk-adaptive audit**: a purchase from seller s is audited with probability
  a_s = a_min + (a_max − a_min) · q̂_s, where q̂_s = (k_s + a0)/(n_s·d̄ + a0 + b0) is clipped to [0, 1].
  - n_s = audits of s, k_s = audits that caught an attack, d̄ = the mean detection probability of the checks run.
  - Defaults: Beta(1, 9) prior, a_min = 0.05, a_max = 0.5. An unaudited seller starts at 0.095.
  - The rate rises after catches and decays towards a_min for clean sellers.
  - There is no budget normalisation. The realised audit rate is reported (`audit_rate_realised`, `n_audits`) so
    that cost can be compared.
