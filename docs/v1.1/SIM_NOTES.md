# v1.1 WP0 — Simulator status notes (how v1.0 actually works)

Scope: the code at commit 41f90b4 (v1.0 snapshot), run through `scripts/run_v1.py` with `configs/v1.0/scale.yaml`
(sha256 780e9b96…a6c, identical to `configs/v1.0/frozen/scale.yaml`). Everything below comes from reading the code
unless it is marked **[measured]**. Measured numbers come from `results/v1.1/wp0_sim_facts/facts.{md,json}`, written by
`scripts/v1.1/sim_facts.py`. That script loads the config the same way `run_v1.py` does and changes no simulator
state. Citations are `file:function:line` at 41f90b4.

Effective v1.0 defaults (merged default.yaml ← benchmark/production.yaml ← v1.0/scale.yaml; **[measured]** facts.json):
P = `fraud.penalty` = 0.25, d = `fraud.detect_prob` = 0.9, d_len = `fraud.detect_prob_length` = 0.9,
`reputation_rounds` = 0 (both `fraud.` and `market.audited.`), audit cost 0.004 per audited purchase (charged to the buyer),
`market.audit.rate` = 0.0 (every non-audited policy), `theft_max_new_tokens` = 48, `billed_token_policy` = claimed_mean,
strategic sellers: honest cost 0.12/1k (1.5B), cheap cost 0.05/1k (0.5B), price ∈ [0.15, 0.21]/1k, capacity 2/round.
n_tasks = 480, n_rounds = 48, so 10 tasks/round. Synthetic pool: 80 items, difficulty counts {1: 28, 2: 28, 3: 24}.
Measured tokens_mean: 1.5B 142.34, 0.5B 149.44.

---

## 1. Seller per-round payoff / reward

### 1a. Per-purchase realised profit (all learners)

`tokenmarket/sim.py:run_single.buy:323`
```
profit = seller_receives − serve_cost · actual_tok / 1000 − slashed
```
- `seller_receives = price_per_1k · billed_tokens / 1000` (`verification.py:TrustingVerifier.settle:49-51`). The
  corridor fee is paid by the buyer on top and does not reduce seller revenue.
- `billed_tokens` = `actual_tok`, except for a theft purchase, where it is `max(actual, round(tokens_mean(claimed)))`
  (`sim.py:run_single.buy:269-270`, `strategic.py:billed_tokens:429-437`).
- `actual_tok` = tokens of the model actually served. A theft purchase is truncated to 48 tokens
  (`sim.py:run_single.buy:264-268`).
- `serve_cost` = `cost_per_1k` (0.05, cheap model) if the purchase is swapped or downgraded, otherwise
  `honest_cost_per_1k` (0.12) (`sim.py:run_single.buy:259-261`).
- `slashed` = P if **either** check caught the purchase (identity: `detector.detect(cheap)`; length:
  `length_auditor.detect(billed, actual)`), charged once per purchase (`sim.py:run_single.buy:293-310`). Identity
  detection fires w.p. d only if `cheap` (swap or downgrade) (`strategic.py:IdentityCheckDetector.detect:112-113`).
  Length detection fires w.p. d_len only if billed > actual·1.1 (`strategic.py:TokenLengthAuditor:138-145`). An audit
  happens w.p. a (`sim.py:run_single.buy:282-292`).
- This profit is passed to the learner by `s.strategy.observe(swapped, profit, theft, downgraded)`
  (`sim.py:run_single.buy:328`), which records it in per-cell running sums `_sum[c]`, `_n[c]` for the cell
  c = (swapped, theft, downgraded) and in an epoch accumulator `_ep_profit` (`strategic.py:AttackStrategy.observe:380-388`).

**Is the cost saved by attacking counted?** Yes, implicitly and on realised numbers. A swap or downgrade lowers
`serve_cost` from 0.12 to 0.05 per 1k. It also changes revenue, because revenue is billed on the cheap model's
actual tokens: 0.5B averages 149.4 tokens vs 142.3 for 1.5B **[measured]**. Theft lowers `actual_tok`, which lowers
cost, and keeps revenue at the claimed mean. Nothing is computed analytically for the learning strategy. The
analytic `cost_saving` and `theft_saving` fields (`strategic.py:make_strategy:471,481`) are used only by
`strategy: analytic|logit` (`strategic.py:start_epoch:285-293`). v1.0 runs `strategy: learning`.

**Is the expected penalty a·d·P counted?** Only through realised outcomes. No learner ever uses a, d or P as numbers.
The penalty enters the cell mean only when a purchase is actually audited **and** caught (realised `slashed`).
Delisting (`reputation_rounds`) is 0, so delisting costs nothing (`audit_v6.py:d3_reputation_rounds:14-20`;
`sim.py:run_single.buy:308-310`). Exception: EXP3 uses P as a reward *normaliser* (see below), not as a cost.
For every non-audited policy (pilot, stageroute, cheapest_fixed, strongest_fixed), a = `market.audit.rate` = 0
(`sim.py:policy_audit_rate:56-62`). For those policies slashed ≡ 0 and the expected penalty is identically zero.

So the per-cell estimate each learner sees is
```
m̂(c) = (1/n_c) Σ_{purchases in cell c} [ p·billed/1000 − serve_cost(c)·actual/1000 − P·1{audited ∧ caught} ]
```
Its expectation is `E[revenue − cost | c] − a · d_c · P`. Here d_c = d for swap/downgrade cells, d_len for theft
cells, and 0 for the honest cell (false-positive rate is 0).

### 1b. Estimated reward of a grid arm (egreedy, hedge, fictitious_play)
Arms are tuples (q_swap, q_theft, q_downgrade) on the grid {0, 0.1, …, 1} for enabled modes, 0 otherwise
(`strategic.py:__post_init__:204-207`). In v1.0 each strategic seller has exactly one mode, so each has 11 arms.
The reward is multilinear in the arm (`strategic.py:AttackStrategy._reward:260-275`):
```
r(qs, qt, qd) = Σ_c w_c(qs, qt, qd) · m̂(c)
w for non-downgrade cells: (qs or 1−qs)·(qt or 1−qt)·(1 − h·qd if not swapped)
w for downgrade cells:     (1−qs)·h·qd·(qt or 1−qt)          h = hard_share = share of this seller's purchases with difficulty ≥ 3
```
For a single-mode seller this reduces to `r(q) = (1−q)·m̂(honest) + q·m̂(attack)`. For downgrade it is
`(1 − h q)·m̂(honest) + h q·m̂(downgrade)`.

### 1c. Learner-specific update (all called once per round from `sim.py:run_single:176-182`)
| learner | code | rule |
|---|---|---|
| egreedy (v1.0 default) | `strategic.py:start_epoch:294-303` | If any enabled cell has no observation yet, **or** w.p. ε = 0.1: play a uniformly random arm. Otherwise argmax_arm r(arm) using the **all-history** cell means. Ties are broken toward 0.5. Because r is linear in q, the argmax is q ∈ {0, 1} unless the two cell means are exactly equal. |
| hedge | `strategic.py:start_epoch:308-315`, `_learn_update:366-378` | Full-information Hedge. If any purchase happened this epoch and all cells are observed: logw_i += η · r(arm_i) / scale, with η = 1 and scale = price · tokens_mean(claimed) / 1000 (`make_strategy:478`). Then w.p. ε a uniform arm, otherwise sample ∝ exp(logw). |
| exp3 | `strategic.py:_exp3_reward:322-327`, `_exp3_epoch:329-343` | Bandit feedback on the arm played last epoch. Reward = clip(0.5 + 0.5 · x̄ / max(scale, P), 0, 1), where x̄ is the mean realised profit of the epoch. Update: logw_arm += γ · (reward / p_arm) / K with γ = 0.1 and K = 11. Play probs (1−γ)·softmax + γ/K. Epochs with no sale give no update. With P = 0.25 ≫ scale ≈ 0.023–0.029, the normaliser is P. An honest-epoch profit (≈0.006–0.012 by price) then maps to reward ≈ 0.51–0.52 and an attack epoch (≈0.017–0.023) to ≈ 0.53–0.55. The reward is nearly flat around 0.5, so learning is very slow. This plausibly explains the v1.0 EXP3 Q ≈ 0.501 for every method (inferred, not tested). |
| fictitious_play | `strategic.py:_fp_epoch:345-364` | Until every enabled cell has been observed, keep the current q (no change). Then for each mode, q_m = sigmoid((r(q_m=1) − r(q_m=0)) / (fp_temperature · scale)), with fp_temperature = 0.1. No exploration. |

## 2. Initial value of q
`__post_init__` sets q = 0.5 for every enabled mode (`strategic.py:AttackStrategy.__post_init__:214-217`). However,
`start_epoch` is called at round 0 **before any purchase** (`sim.py:run_single:176-182`), so the q actually played in
round 0 is:
- **egreedy**: a uniform random arm, because no cell is observed yet (`strategic.py:299-300`). Uniform over 11 grid
  points, E[q] = 0.5. It **stays** uniform random every round until the seller has at least one purchase in both its
  honest and its attack cell.
- **hedge**: `_learn_update` returns early (no epoch purchases), all logw = 0, so uniform random (E = 0.5)
  (`strategic.py:310-315, 371-372`).
- **exp3**: logw = 0, so uniform probabilities and a random arm (E = 0.5) (`strategic.py:337-343`).
- **fictitious_play**: exactly 0.5, held until both cells are observed (`strategic.py:352-354`).

**Consequence for Q (problem 3).** A strategic seller that rarely or never sells keeps playing q ~ U(grid) (or 0.5
for FP), so its tail-window mean q is ≈ 0.5 *by construction*, whatever the deterrent. **[measured]** from
`results/v1.0/main/per_seed.csv` (facts.md, last table): cheapest_fixed has tail_trade_rate 0.000 (strategic sellers
make zero tail sales) and Q = 0.508. The five audit arms average 0.9–1.1 strategic tail sales per run (all 9 sellers
combined, last 12 rounds) and have Q = 0.52–0.54. The routers that do trade strategic sellers heavily move away from 0.5:
pilot (38.5 tail sales, Q = 0.89), strongest_fixed (80.3, Q = 0.79), stageroute (15.3, Q = 0.67). So "Q ≈ initial
value" mostly means "strategic sellers are not sold to, so they never learn", not "48 rounds is too short". More
rounds will not fix this for arms that do not trade with them.

## 3. Paths from an audit result to later routing
An audit outcome can, in principle, act through:
1. **TrustModel** (only for `AUDITED_POLICIES` = audited_compliance_cascade, audited_cascade_unfiltered;
   `sim.py:run_single:116-118`). `trust.record` / `record_length` run on every audit (`sim.py:298-304`). Prior a=0, b=1
   (`strategic.py:TrustModel.__init__:500`). After the **first detected** swap/downgrade, routing quality becomes
   (1−q̂)·acc(claimed) + q̂·acc(revealed model), with q̂ = k/(n·d+1). After the first detected theft, quality is
   multiplied by (1 − q̂_theft·0.5) (`strategic.py:TrustModel.quality:534-541`). Before any detection, quality = claimed
   reputation, exactly as for an untrusted policy. `quality(s)` dispatches to trust when it exists
   (`sim.py:run_single.quality:200-203`).
2. **Slash.** `s.stake_slashed += P` (`sim.py:307`). This only enters seller profit (§1). No router reads `stake_slashed`.
3. **Delist.** `banned_until_round` is set only if `rep_rounds > 0` (`sim.py:308-310`), and the `listed` filter
   (`sim.py:205`) then removes the seller for every policy. In v1.0 rep_rounds = 0, so this path is **dead**.
4. **Risk-adaptive audit rate.** `RiskAdaptiveAudit.record` (`sim.py:313-314`) changes future *audit probabilities*
   a_s = 0.05 + 0.45·q̂_s, with Beta(1, 9) prior and q̂ = (k+1)/(n·d̄+10) (`audit_v1.py:228-258`). It changes who
   gets audited, not who gets routed to.
5. The correctness-feedback channel (π) carries **labels only**. Audits are not routed through it (`sim.py:167`;
   `feedback.py:FeedbackRouter:117-150`).

Per router:
| method (policy) | audits? (a, checks) | reads trust / audit outcomes in routing? | code |
|---|---|---|---|
| pilot (`pilot_v1_compliant`) | a = market.audit.rate = **0**, identity only | **No.** LinUCB on claimed-reputation prior + correctness labels + cost; never sees trust or stake | `baselines.py:PilotV1Router.choose:409-427`, `update:429-432`; `portfolio.py:run_policy:86-94` (no `quality` passed) |
| stageroute (`stageroute_v1_compliant`) | a = **0** | **No.** Per-seller mean correctness μ and cost c from labels | `baselines.py:StageRouteV1Router.choose:547-558`, `update:560-564` |
| cheapest_fixed (`single_cheapest_compliant`) | a = **0** | **No.** argmin exp_cost (price · tokens_mean(claimed)/1000 · (1+fee)); quality only as a tie-break and trust is None, so claimed reputation | `portfolio.py:84,101-107`; `sim.py:224-226` |
| strongest_fixed (`single_best_compliant`) | a = **0** | **No.** argmax claimed reputation (trust None) | `portfolio.py:102-103` |
| random_audit, fixed_audit_a{0.05,0.10,0.20}, risk_adaptive_audit (all `audited_compliance_cascade`) | a from market.audited (rule fixed / random / risk_adaptive), checks identity + length | **Yes, via TrustModel only** (path 1): `quality()` enters the cascade's cost-sort tie-break (`portfolio.py:84`) and the escalation filter `quality(s) ≥ quality(cur)` (`portfolio.py:127`). The first purchase is always the cheapest compliant seller, whatever trust says | `portfolio.py:run_policy:96-138` |

Note: "audited_compliance_cascade" is not a separate method in the v1.0 table. It is an alias of fixed_audit_a0.10
(`registry.py:ALIASES:56-59`), and all five audit arms use that policy id with different `market.audited` overrides
(`registry.py:_METHODS:40-53`).

## 4. Can routing and auditing be separated into two knobs?

**Today, partially, with config only:**
- **cascade + a=0 already exists as a config point.** Run policy `audited_compliance_cascade` with
  `market.audited.audit_rate: 0.0`. Then a_rate = 0 (`sim.py:97`), `do_audit` is never true (`sim.py:282`), the rule
  falls back to "fixed" (`sim.py:140`), and TrustModel exists but never records, so quality = claimed reputation.
  This is the cascade router with no audits and no trust updates. It needs only a registry entry
  (e.g. `Method("cascade_a0", "audited_compliance_cascade", …, _audit(0.0))`). It is equivalent to plain
  `cascade_compliant` with the audited cascade settings (threshold 0.7, max 3 steps). (Inferred; not run in WP0.)
- **Other routers + fixed-rate audit** is reachable through `market.audit.rate` / `market.audit.types`
  (`sim.py:policy_audit_rate:56-62`, `policy_audit_checks:65-71`). Audit, slash and seller learning are generic code
  in `buy()` and work for any policy. Three limits apply: (i) `audit_rule` is forced to "fixed" for non-audited
  policies (`audit_v1.py:audit_rule:205-207`), so random and risk-adaptive are unavailable; (ii) the default checks are
  `[identity]` only, so theft is never caught unless `market.audit.types: [identity, length]`; (iii) TrustModel is
  None, so audit outcomes never reach those routers (that matches the "audit does not feed routing" design, but it
  differs from the cascade arms).
- `run_v1.py:point_config` merges the method's overrides **after** the base config (`run_v1.py:point_config:67-79`),
  so a base-config `market.audited.audit_rate` is overwritten by the method's `_audit(...)`. Every new
  (router, audit) cell therefore needs a registry entry, or a CLI override applied after the method merge.

**Minimal change for a clean router × audit factorial (describe only, not implemented):**
1. Add a policy-independent audit block, e.g. `market.audit_v11: {enabled, rate, rule, types, trust_feedback}`.
   When `enabled`, `policy_audit_rate`, `policy_audit_checks` and `audit_rule` read from it for **every** policy
   instead of branching on `policy in AUDITED_POLICIES` (`sim.py:56-71`, `audit_v1.py:205-211`). With
   `enabled: false` the code path is unchanged, so v1.0 stays bit-identical.
2. Decide `trust_feedback`: when true, construct `TrustModel` for any policy (`sim.py:116-118`). Only quality-reading
   routers (cascade, strongest, cheapest tie-break) would consume it. PILOT and StageRoute would need an explicit hook
   (e.g. drop or down-weight a seller after a catch), which changes those baselines. I recommend `trust_feedback:
   false` for all routers in the Q-A factorial, so routing is identical across audit levels, and a separate "cascade +
   trust" arm.
3. Registry: generate methods `"{router}__{audit}"` for router ∈ {cascade, pilot, stageroute, strongest, cheapest} ×
   audit ∈ {a0, a0.05, a0.10, a0.20, risk_adaptive}, where "cascade" = `audited_compliance_cascade` policy id with the
   v1.1 audit block.
4. Keep the RNG streams as they are (`audit-{seed}`, `audit-rate-{seed}`; `sim.py:135,141`). Within a seed and router,
   audit draws stay common across audit levels only until routing diverges.

## 5. Scaling n_rounds to 200 / 500
- **Where tasks come from:** `sample_run_tasks` concatenates independent seeded permutations of the fixed 80-item
  synthetic pool until n_tasks is reached (sampling without replacement within each permutation, cycling across them)
  (`tasks.py:sample_run_tasks:153-172`). Buyers are assigned round-robin.
- **Round length is derived, not set:** per_round = ceil(n_tasks / n_rounds) and round = i // per_round
  (`sim.py:149,177`). To keep 10 tasks/round you **must** set n_tasks = 10·n_rounds (2000 for 200, 5000 for 500).
  If only n_rounds changes (`--n-rounds 200` with n_tasks = 480), per_round = 3 and only 160 rounds actually happen.
  The Q tail window still uses n_rounds = 200 (rounds 150–199), and `v1_metrics.intent` silently drops rounds ≥ 160
  (`v1_metrics.py:intent:316`), so Q would come from 10 rounds. For n_rounds = 500, per_round = 1, giving 480 rounds
  and a 125-round tail with only 105 rounds present.
- **Cache:** **[measured]** `cache/llm_outputs.jsonl` holds 250 records: synthetic (max_new_tokens 256) 77 per model
  for Qwen2.5-0.5B and 1.5B. These are 77 unique prompts covering all 80 pool items; `model_stats` requires every pool
  item to hit (`precompute.py:model_stats:107-109`) and it returned measured stats. Long tasks (512 tokens):
  GSM8K 28 + MATH-500 20 per model, matching `data/long_tasks.jsonl` (28 + 20). Because tasks are recycled from the
  pool, **any n_tasks needs no new generation**: the cache is "large enough" by construction. The cost is that each
  synthetic item repeats ~25× (n = 2000) or ~62× (n = 5000) per run, with identical cached outputs (greedy, so the
  same answer and token count each time). Effective diversity stays 80 items. The long pool (48 items) would repeat
  ~42× / ~104× if used.
- **Budgets do not scale with n_tasks:** buyer budgets are fixed per run (budget × 2.0; total 24.0 across 6 buyers,
  `sim.py:93-95`, default.yaml buyers). **[measured]** a v1.0 PILOT run already spends ≈ 10.8 for 480 tasks
  (per_seed.csv `cost`). At 2000 tasks spend would be ≈ 45 > 24, so buyers run out of budget mid-run and fill_rate
  collapses. The tight buyer (budget 1.0) runs out first. A v1.1 long-horizon config must scale
  `market.budget_multiplier` (or budgets) by n_tasks/480. The routers' horizon and budget pacing also depend on
  n_tasks (`sim.py:153-162`; PILOT bins, StageRoute stages).

## 6. Break-even: when is one attack profitable?
From §1, a single-mode strategic seller's expected per-purchase gain of attacking rather than serving honestly is
```
Δ = S − a · d_c · P          S = E[revenue − cost | attack] − E[revenue − cost | honest]
swap / downgrade (identity, d = 0.9):  S_swap  = [(p − c_L)·T_L − (p − c_H)·T_H] / 1000
theft            (length,   d_len = 0.9): S_theft = [p·(B − T_H) + c_H·(T_H − 48)] / 1000,  B = round(T_H) = 142
profitable  ⇔  a < a* = S / (d_c · P)
```
with c_H = 0.12, c_L = 0.05, T_H = 142.34, T_L = 149.44 (measured means), P = 0.25, delist R = 0.
The code's analytic version (`strategic.py:swap_gain:68-72`, `make_strategy:471`) uses S = cost_gap·T_H/1000 and
ignores the revenue change from the cheap model's different token count. **[measured]** facts.md, break-even table:

| | S (per purchase) | a* |
|---|---|---|
| swap (code analytic) | 0.00996 | **0.0443** |
| swap (realised mean tokens, by seller price 0.161–0.207) | 0.01075–0.01108 | **0.0478–0.0492** |
| downgrade (per eligible hard purchase; same as swap) | same | **0.044–0.049** |
| theft | 0.01125–0.01127 | **0.0500–0.0501** |

Against the v1.0 audit grid:
- a = 0 (every non-audit arm): far below a*, so every attack is profitable (Δ ≈ +0.010 to +0.011 per purchase).
- a = 0.05: **essentially at the break-even point**. For swap/downgrade, Δ = −0.00017 to −0.00050 (realised tokens) or
  −0.0013 (code analytic), slightly unprofitable. For theft, Δ = +0.0000007 to +0.000016 (a* = 0.0500–0.0501), a
  knife edge on the profitable side.
- a = 0.10 / 0.20: 2× / 4× above a*, so attacking is unprofitable (Δ ≈ −0.012 / −0.034).
- random_audit: E[a_t] = 0.1, so above a* on average.
- risk_adaptive: a_s ≥ a_min = 0.05 and ≈ 0.095 before any catch, so at or above a* everywhere.

So **every audited arm in the v1.0 grid is at or above break-even (theft at a = 0.05 is a tie to 5 decimals), and only a = 0 is clearly below**. No arm sits strictly
inside the profitable region with a > 0. A discriminative Q-A grid needs points strictly between 0 and ≈ 0.045
(e.g. 0.01, 0.02, 0.03). Alternatively, scale P down (a* ∝ 1/P) to move the threshold into the grid.

Caveat: the learners do not compute Δ. They estimate it from realised cell means (§1). A cell mean at a = 0.05 with
a·d = 0.045 needs on the order of 1/(a·d) ≈ 22 attack purchases before the first slash is even expected. Most audit
arms make ~1 strategic sale per run in the tail (§2), so in v1.0 sellers in the audit arms cannot realistically learn
Δ at all.

## Other observations relevant to v1.1
- **π is inert for 7 of 9 methods.** Feedback labels feed only the bandit routers (`sim.py:187-192`). **[measured]**
  `results/v1.1/wp0_sim_facts/pi_invariance.txt`: for cheapest_fixed, strongest_fixed and all five audit arms, the 19
  π rows of each (method, seed) are byte-identical apart from π and config_hash. Their effective sample size is 20
  seeds, not 380 rows.
- **Why cheapest_fixed has E = 0 (problem 2).** **[measured]** facts.md seller ranking: the 12 cheapest sellers by
  expected cost are honest `sim-fast-mock` sellers (exp cost 0.0050–0.0076), then 5 honest 0.5B sellers. The cheapest
  strategic seller is rank 18 (0.0229). With capacity 2/round, 10 tasks/round and 12 mock sellers, cheapest_fixed
  never makes an attacked purchase (E = 0) and has zero strategic tail sales. Strategic sellers claim 1.5B, so their
  expected cost uses T_H = 142.3 tokens. To match the mock sellers' expected cost (0.0050–0.0076) they would need a
  price ≈ 0.035–0.053/1k, at or below their own 0.05 cheap-model serving cost. That is structurally impossible without new
  pricing semantics (Q-C).
- **Audit arms' low E is mostly routing.** **[measured]** E is 0.0043–0.0051 for audit rates 0.05→0.20 and ~1
  strategic tail sale per run, with no trend in a. The cascade starts from the cheapest seller (mock) and escalates
  only on low confidence, so strategic sellers rarely get demand. Consistent with §4: cascade + a=0 is the missing
  control.
