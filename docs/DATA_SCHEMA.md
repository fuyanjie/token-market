# Benchmark data schema (v1 publishable export)

The platform is a **benchmark generator**. Each mock / cached run exports **five JSONL files** (one JSON object per line). No CLOB, no multi-buyer expansion, no separate `ledger.jsonl` / `events.jsonl` on disk (those can be derived from `orders ⋈ audits`).

**Primary board** (read `episodes.jsonl`): `active_attack_rate` + `fraud_share`.
`active_attack_rate` = attacked / served purchases (NOT epoch-mean learned q).
`learned_q_swap` / `learned_q_theft` are separate secondary columns; with delist they can diverge from `active_attack_rate`.  
**Secondary**: `J`, learned q details. **Immediate-feedback J is NOT the primary ranking.**

Default config keeps `adaptive_audit=false`, `reputation_rounds=0`, `escrow=false` so legacy F/J tables stay reproducible.

Join keys: `run_id`, `seed`, `order_id` (= `purchase_id` when served), `config_hash`.

| File | Layer | Source |
|---|---|---|
| `sellers.jsonl` | seller catalog | `sellers` config + end-of-run learned q / slash |
| `buyers.jsonl` | buyer demand | `buyers` config + remaining budget from order log |
| `orders.jsonl` | order flow | `logging_schema` transaction lines (mapped) |
| `audits.jsonl` | audit events | per served purchase; linked by `order_id` |
| `episodes.jsonl` | eval protocol / board | one row per (run_id, seed) |

Five platform modules (code map):

1. Admission/compliance — `gateway.py` + `compliance.py`
2. Routing / portfolio procurement — `matching.py` / `portfolio.py` / `buyers.py` / `baselines.py`
3. Escrow settlement — `sim.py` + `audit_v6.py` (`locked→settled/slashed`; default off)
4. Oversight audit — `strategic.py` + `audit_v6.py`
5. Feedback & trails — `feedback.py` + `logging_schema.py`

---

## 1. `sellers.jsonl`

| field | type | nullable | meaning | analysis use |
|---|---|---|---|---|
| seller_id | str | no | seller id | entity key |
| jurisdiction | str | no | CN/SG/BR | cross-border / compliance |
| claimed_model | str | no | advertised model | fraud surface |
| actual_model | str | no | served when swapping | fraud surface |
| listed_quality | object | no | difficulty→accuracy prior | routing priors |
| latent_q_swap | float | no | end-of-run learned/static swap rate | deterrence q* |
| latent_q_theft | float | no | end-of-run theft rate | deterrence q* |
| list_price | float | no | posted USD / 1k tokens | pricing |
| capacity | int | no | capacity_per_round | supply |
| stake | float | no | synthetic stake pool (default 20×penalty) | slash capacity |
| stake_remaining | float | no | stake − episode slash (fraud seller) | residual stake |
| banned_until_round | int | no | delist watermark (0 if none at export) | suspension |
| run_id | str | no | episode id | join |
| seed | int | no | RNG seed | join |

### samples (3)

```json
{"seller_id":"seller_cn","jurisdiction":"CN","claimed_model":"Qwen/Qwen2.5-1.5B-Instruct","actual_model":"Qwen/Qwen2.5-1.5B-Instruct","listed_quality":{"1":0.95,"2":0.85,"3":0.7},"latent_q_swap":0.0,"latent_q_theft":0.0,"list_price":0.2,"capacity":20,"stake":5.0,"stake_remaining":5.0,"banned_until_round":0,"run_id":"posted_price__audited_compliance_cascade__seed0","seed":0}
{"seller_id":"seller_sg","jurisdiction":"SG","claimed_model":"Qwen/Qwen2.5-1.5B-Instruct","actual_model":"Qwen/Qwen2.5-0.5B-Instruct","listed_quality":{"1":0.95,"2":0.85,"3":0.7},"latent_q_swap":0.08,"latent_q_theft":0.08,"list_price":0.18,"capacity":20,"stake":5.0,"stake_remaining":4.5,"banned_until_round":0,"run_id":"posted_price__audited_compliance_cascade__seed0","seed":0}
{"seller_id":"seller_br","jurisdiction":"BR","claimed_model":"sim-fast-mock","actual_model":"sim-fast-mock","listed_quality":{"1":0.82,"2":0.62,"3":0.4},"latent_q_swap":0.0,"latent_q_theft":0.0,"list_price":0.06,"capacity":20,"stake":5.0,"stake_remaining":5.0,"banned_until_round":0,"run_id":"posted_price__audited_compliance_cascade__seed0","seed":0}
```

---

## 2. `buyers.jsonl`

| field | type | nullable | meaning | analysis use |
|---|---|---|---|---|
| buyer_id | str | no | buyer id | entity key |
| jurisdiction | str | no | buyer jurisdiction | corridor / rules |
| budget_total | float | no | budget × budget_multiplier | demand |
| budget_remaining | float | no | remaining after episode | spend pressure |
| strategy_id | str | no | route policy for this run | mechanism label |
| compliance_profile | object | no | allowed_jurisdictions, sensitivity_mix, consent_rate | compliance filter |
| run_id | str | no | episode id | join |
| seed | int | no | RNG seed | join |

### samples (3)

```json
{"buyer_id":"buyer_cn_1","jurisdiction":"CN","budget_total":2.5,"budget_remaining":1.12,"strategy_id":"audited_compliance_cascade","compliance_profile":{"allowed_jurisdictions":["CN","SG","BR"],"sensitivity_mix":{"public":0.4,"personal":0.35},"consent_rate":0.5},"run_id":"posted_price__audited_compliance_cascade__seed0","seed":0}
{"buyer_id":"buyer_sg_2","jurisdiction":"SG","budget_total":0.5,"budget_remaining":0.02,"strategy_id":"audited_compliance_cascade","compliance_profile":{"allowed_jurisdictions":["SG","BR"],"sensitivity_mix":{"public":0.6,"personal":0.4},"consent_rate":0.5},"run_id":"posted_price__audited_compliance_cascade__seed0","seed":0}
{"buyer_id":"buyer_br_1","jurisdiction":"BR","budget_total":2.0,"budget_remaining":0.84,"strategy_id":"audited_compliance_cascade","compliance_profile":{"allowed_jurisdictions":["CN","SG","BR"],"sensitivity_mix":{"public":0.4,"personal":0.3},"consent_rate":0.3},"run_id":"posted_price__audited_compliance_cascade__seed0","seed":0}
```

---

## 3. `orders.jsonl`

Mapped from `logging_schema` transaction lines. `order_id` = `purchase_id` when served; synthetic id for blocked/unfilled.

| field | type | nullable | meaning | analysis use |
|---|---|---|---|---|
| order_id | str | no | purchase / line id | join to audits |
| round | int | no | market round index | time |
| t_submit | float | yes | unix ts | timeline |
| t_deliver | float | yes | delivery ts (served only) | timeline |
| t_settle | float | yes | settle ts (served only) | escrow timeline |
| buyer_id | str | no | buyer | demand |
| seller_id | str | yes | seller (null if unfilled) | supply |
| task_id | str | no | task instance id | portfolio |
| portfolio_id | str | no | = task_id in v1 | multi-purchase tasks |
| tokens_billed | int | no | billed tokens | theft |
| tokens_actual | int | no | generated tokens | theft |
| price | float | no | price_per_1k | spend |
| amount_escrow | float | no | escrow_held (0 if escrow off) | escrow |
| amount_paid | float | no | actual_cost | spend |
| state | str | no | locked\|delivered\|audited\|settled\|slashed\|blocked\|unfilled | state machine |
| attack_mode | str | no | none\|swap\|theft\|both | fraud |
| correct | bool | yes | answer correctness | labels |
| jurisdiction_path | str | no | `buyer_j→seller_j` | cross-border |
| route_policy | str | no | policy name | baseline |
| run_id | str | no | episode id | join |
| seed | int | no | seed | join |
| config_hash | str | no | sha256[:16] of cfg | reproducibility |

### samples (3)

```json
{"order_id":"posted_price__audited_compliance_cascade__seed0|t0_x|0|seller_sg","round":0,"t_submit":1730000000.1,"t_deliver":1730000000.1,"t_settle":1730000000.1,"buyer_id":"buyer_cn_1","seller_id":"seller_sg","task_id":"t0_x","portfolio_id":"t0_x","tokens_billed":140,"tokens_actual":140,"price":0.18,"amount_escrow":0.0,"amount_paid":0.025,"state":"settled","attack_mode":"swap","correct":false,"jurisdiction_path":"CN->SG","route_policy":"audited_compliance_cascade","run_id":"posted_price__audited_compliance_cascade__seed0","seed":0,"config_hash":"abc123deadbeef00"}
{"order_id":"posted_price__audited_compliance_cascade__seed0|t1_y|0|seller_cn","round":0,"t_submit":1730000000.2,"t_deliver":1730000000.2,"t_settle":1730000000.2,"buyer_id":"buyer_sg_1","seller_id":"seller_cn","task_id":"t1_y","portfolio_id":"t1_y","tokens_billed":150,"tokens_actual":150,"price":0.2,"amount_escrow":0.0,"amount_paid":0.03,"state":"settled","attack_mode":"none","correct":true,"jurisdiction_path":"SG->CN","route_policy":"audited_compliance_cascade","run_id":"posted_price__audited_compliance_cascade__seed0","seed":0,"config_hash":"abc123deadbeef00"}
{"order_id":"posted_price__audited_compliance_cascade__seed0|t2_z|0|none|line42","round":1,"t_submit":1730000000.3,"t_deliver":null,"t_settle":null,"buyer_id":"buyer_sg_2","seller_id":null,"task_id":"t2_z","portfolio_id":"t2_z","tokens_billed":0,"tokens_actual":0,"price":0.0,"amount_escrow":0.0,"amount_paid":0.0,"state":"unfilled","attack_mode":"none","correct":null,"jurisdiction_path":"SG","route_policy":"audited_compliance_cascade","run_id":"posted_price__audited_compliance_cascade__seed0","seed":0,"config_hash":"abc123deadbeef00"}
```

---

## 4. `audits.jsonl`

Independent event rows for **served** purchases (join via `order_id`). Internal allocator credit is **not** exported.

| field | type | nullable | meaning | analysis use |
|---|---|---|---|---|
| audit_id | str | no | `audit\|{order_id}` | event key |
| order_id | str | no | join to orders | join |
| round | int | no | round index | time |
| mode | str | no | fixed\|adaptive\|none | audit regime |
| sampled | int | no | 0/1 audited | selection |
| identity_check | int | no | 0/1 | check type |
| length_check | int | no | 0/1 | check type |
| hit | int | no | 0/1 detection | detection |
| miss | int | no | 0/1 attacked but missed | miss rate |
| slash_amount | float | no | stake slashed | penalty |
| delist_rounds | int | no | suspension length | reputation |
| auditor_cost | float | no | audit fee | cost |
| label_revealed | int | no | 0/1 outcome label revealed | π channel |
| label_delay_L | int | yes | delay L (null=∞) | L channel |
| reveal_pi | float | no | reveal probability π | π channel |
| label_correct | bool | yes | correctness label | feedback |
| fraud_realized | int | no | 0/1 attack_mode≠none | realized fraud |
| run_id | str | no | episode id | join |
| seed | int | no | seed | join |

### samples (3)

```json
{"audit_id":"audit|...|seller_sg","order_id":"...|seller_sg","round":0,"mode":"fixed","sampled":1,"identity_check":1,"length_check":1,"hit":1,"miss":0,"slash_amount":0.25,"delist_rounds":0,"auditor_cost":0.004,"label_revealed":1,"label_delay_L":0,"reveal_pi":1.0,"label_correct":false,"fraud_realized":1,"run_id":"posted_price__audited_compliance_cascade__seed0","seed":0}
{"audit_id":"audit|...|seller_cn","order_id":"...|seller_cn","round":0,"mode":"fixed","sampled":0,"identity_check":0,"length_check":0,"hit":0,"miss":0,"slash_amount":0.0,"delist_rounds":0,"auditor_cost":0.0,"label_revealed":1,"label_delay_L":0,"reveal_pi":1.0,"label_correct":true,"fraud_realized":0,"run_id":"posted_price__audited_compliance_cascade__seed0","seed":0}
{"audit_id":"audit|...|seller_br","order_id":"...|seller_br","round":1,"mode":"fixed","sampled":1,"identity_check":1,"length_check":1,"hit":0,"miss":0,"slash_amount":0.0,"delist_rounds":0,"auditor_cost":0.004,"label_revealed":1,"label_delay_L":0,"reveal_pi":1.0,"label_correct":true,"fraud_realized":0,"run_id":"posted_price__audited_compliance_cascade__seed0","seed":0}
```

---

## 5. `episodes.jsonl` (primary board table)

One row per `(run_id, seed)`. Leaderboard scripts aggregate these.

| field | type | nullable | meaning | analysis use |
|---|---|---|---|---|
| run_id | str | no | episode id | join |
| seed | int | no | fixed seed | reproducibility |
| a | float | no | audit rate / budget | protocol |
| pi | float | no | label reveal prob | protocol |
| L | int | yes | label delay (null=∞) | protocol |
| reputation_rounds | int | no | delist length (default 0) | protocol |
| active_attack_rate | float | no | **primary**: attacked / served purchases (active trade attack rate; NOT learned q) | deterrence / realized attack |
| learned_q_swap | float | yes | **secondary**: epoch-mean learned swap q (fraud seller) | seller policy; diverges under delist |
| learned_q_theft | float | yes | **secondary**: epoch-mean learned theft q (fraud seller) | seller policy; diverges under delist |
| fraud_share | float | no | **primary**: realized attack share / served (same formula as active_attack_rate in v1) | realized fraud |
| J | float | no | **secondary** joint objective | appendix |
| n_audits | int | no | audit count | cost |
| config_hash | str | no | cfg hash | reproducibility |

> **Terminology lock:** do not treat `active_attack_rate` as an alias of epoch-mean learned q. Without delist the two may be close (esp. under D3); with delist they must be reported as separate columns. Primary board remains `active_attack_rate` + `fraud_share`.

### samples (3)

```json
{"run_id":"posted_price__audited_compliance_cascade__seed0","seed":0,"a":0.1,"pi":1.0,"L":0,"reputation_rounds":0,"active_attack_rate":0.101,"learned_q_swap":0.083,"learned_q_theft":0.083,"fraud_share":0.101,"J":0.766,"n_audits":60,"config_hash":"abc123deadbeef00"}
{"run_id":"posted_price__stageroute_compliant__seed0","seed":0,"a":0.0,"pi":1.0,"L":0,"reputation_rounds":0,"active_attack_rate":0.023,"learned_q_swap":0.80,"learned_q_theft":0.77,"fraud_share":0.023,"J":0.811,"n_audits":0,"config_hash":"def456cafe000111"}
{"run_id":"posted_price__pilot_compliant__seed0","seed":0,"a":0.0,"pi":0.1,"L":0,"reputation_rounds":0,"active_attack_rate":0.12,"learned_q_swap":0.95,"learned_q_theft":0.94,"fraud_share":0.12,"J":0.70,"n_audits":0,"config_hash":"fedcba9876543210"}
```

---


---

## Feature / Label separation (application constraint)

v1 keeps the **five default tables unchanged** for leaderboard convenience. Several columns in those tables are **evaluation labels**, not public training features. Using them as model inputs for fraud detection / routing ML will leak the supervision signal.

| Location | Label columns (do NOT use as training features) |
|---|---|
| `sellers.jsonl` | `actual_model`, `latent_q_swap`, `latent_q_theft` |
| `orders.jsonl` | `attack_mode`, `correct` |
| `audits.jsonl` | `fraud_realized`, `label_correct` |

**Safe public features (examples):** jurisdiction, claimed_model, list_price, capacity, stake*, budget*, tokens_billed/actual, price, amount_*, state, jurisdiction_path, route_policy, audit mode/sampled/checks/hit/miss/slash/delist/auditor_cost, feedback reveal timing fields (`label_revealed`, `label_delay_L`, `reveal_pi`).

**Held-out supervision file (optional):** `labels.jsonl` — join on `order_id`.

| field | type | nullable | meaning |
|---|---|---|---|
| order_id | str | no | join to orders |
| attack_mode | str | yes | none\|swap\|theft\|both |
| correct | bool | yes | answer correctness |
| actual_model | str | yes | seller true model (from sellers row) |
| latent_q_swap | float | yes | seller latent swap rate |
| latent_q_theft | float | yes | seller latent theft rate |
| run_id | str | no | episode id |
| seed | int | no | seed |

Export with `--with-labels` (default five files still written the same way). Full feature/label strip of the public pack is deferred to **v1.1**. Until then: **do not treat the default export as a clean supervised fraud-detection training set** without dropping the label columns above (or joining only via `labels.jsonl`).

### labels samples (3)

```json
{"order_id":"...|seller_sg","attack_mode":"swap","correct":false,"actual_model":"Qwen/Qwen2.5-0.5B-Instruct","latent_q_swap":0.08,"latent_q_theft":0.08,"run_id":"posted_price__audited_compliance_cascade__seed0","seed":0}
{"order_id":"...|seller_cn","attack_mode":"none","correct":true,"actual_model":"Qwen/Qwen2.5-1.5B-Instruct","latent_q_swap":0.0,"latent_q_theft":0.0,"run_id":"posted_price__audited_compliance_cascade__seed0","seed":0}
{"order_id":"...|none|line42","attack_mode":"none","correct":null,"actual_model":null,"latent_q_swap":null,"latent_q_theft":null,"run_id":"posted_price__audited_compliance_cascade__seed0","seed":0}
```

## Derived views (not shipped)

- Full ledger / event log: `orders` left-join `audits` on `order_id`.
- Escrow timeline: filter `orders.state ∈ {locked,settled,slashed}` (populated when `market.audited.escrow=true`).

## One-click export

```bash
/workspace/tmvenv/bin/python scripts/export_benchmark_layers.py \
  --out exports/latest --seed 0 --n-tasks 48 --learning
# optional held-out labels:
/workspace/tmvenv/bin/python scripts/export_benchmark_layers.py \
  --out exports/latest --seed 0 --n-tasks 48 --learning --with-labels
```
