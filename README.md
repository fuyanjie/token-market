## Benchmark release (Datasets & Benchmarks track)

This repository is a **reproducible cross-border reasoning-token market simulator** used as a
**benchmark generator** (not an order-book / CLOB). The research claim for the Datasets & Benchmarks
paper is the **platform + evaluation protocol**; deterrence methods stay in a separate methods paper.

### Five platform layers ↔ code

| Layer | Code |
|---|---|
| 1. Admission / compliance | `tokenmarket/gateway.py`, `compliance.py` |
| 2. Routing / portfolio procurement (not an order book) | `matching.py`, `portfolio.py`, `buyers.py`, `baselines.py` |
| 3. Escrow settlement (`locked→settled/slashed`; **default OFF**) | `sim.py`, `audit_v6.py` |
| 4. Oversight audit (fixed `a`; optional delist / adaptive; **default OFF**) | `strategic.py`, `audit_v6.py` |
| 5. Feedback & trails | `feedback.py`, `logging_schema.py` |

### v1 publishable export (five JSONL files)

See field dictionary + samples: [`docs/DATA_SCHEMA.md`](docs/DATA_SCHEMA.md).

| File | Contents |
|---|---|
| `sellers.jsonl` | seller catalog |
| `buyers.jsonl` | buyer demand / compliance profile |
| `orders.jsonl` | order flow (from `logging_schema`) |
| `audits.jsonl` | audit events joined by `order_id` |
| `episodes.jsonl` | protocol + **primary board** metrics |

**Primary board** (from `episodes.jsonl`): `active_attack_rate` + `fraud_share`.  
**Secondary**: `J`, learned q. **Immediate-feedback J is NOT the primary ranking.**  
No `ledger.jsonl` / `events.jsonl` on disk (derive via `orders ⋈ audits`). Internal caches are not part of the release.

### One-click commands

```bash
# five-layer JSONL + knobs yaml (mock backend, no GPU)
/workspace/tmvenv/bin/python scripts/export_benchmark_layers.py \
  --out exports/latest --seed 0 --n-tasks 48 --learning

# knobs only (a, π, L, reputation_rounds, ...)
/workspace/tmvenv/bin/python scripts/export_config.py

# standard tasks T1–T3 (fixed seeds)
/workspace/tmvenv/bin/python scripts/run_benchmark_tasks.py --smoke          # fast
/workspace/tmvenv/bin/python scripts/run_benchmark_tasks.py --tasks T1 T2 T3

# leaderboard: three tables (attack, fraud, J-secondary)
/workspace/tmvenv/bin/python scripts/run_leaderboard.py --smoke
```

Config: `configs/benchmark/default.yaml` (seeds `[0,1,2]`; v6 switches remain off).

---

# token-market v5：合规约束下的多模型组合采购 + 不完美审计下的策略性欺诈 + 延迟/稀疏结果反馈（Compliance-constrained Portfolio Purchasing under Strategic Fraud and Delayed / Sparse Outcome Feedback）

一个**纯虚拟**的跨境推理 token 交易平台（cross-border reasoning-token marketplace）研究沙盒。
CN / SG / BR 三个司法辖区（jurisdiction）的买方（buyers）向卖方（sellers）购买"推理 token"来解答有标准答案的推理题。
v2 的两个卖方是**真实运行的本地小模型**（Qwen2.5-1.5B / 0.5B-Instruct，CPU），一个卖方是模拟模型（MockLLM）。

> ⚠️ **免责声明（Disclaimer）**：合规规则仅为**简化模拟（simplified simulation）**，条款编号只作标签使用，
> **不构成法律意见（NOT legal advice）**。价格、预算、通道费均为合成数据（synthetic）。默认不调用任何真实 API，不需要任何 API key。

## v5 新增：延迟 / 稀疏结果反馈消融（v5: delayed / sparse outcome-feedback ablation, F）

**研究定位更新（novelty framing）**：合规约束下的多模型组合采购 + 不完美审计下的策略性欺诈（swap + theft），
**在延迟 / 稀疏结果反馈（delayed / sparse outcome feedback）下**——这正是审计（audits）起作用的场景。
推理 token 长度不确定性仍然**降级**（不作为贡献点）。

**动机 / 假设（hypothesis）**：在**即时、完整**的结果反馈（immediate full feedback）下，PILOT+合规 与 StageRoute+合规
不付审计费也能逼近甚至超过 D3 的 J（v4 主表），因为 bandit 观察到正确性后学会避开欺诈卖方。
假设：反馈越**延迟**（delay L）或越**稀疏**（reveal prob π），D3 在 J 与欺诈抑制上的优势越大。

**反馈通道（feedback channel，`tokenmarket/feedback.py`）**：
- 结果反馈（outcome feedback）= 所购答案是否正确（bandit 的 reward / label）。在全局步 t（= 任务序号）购买后，
  标签以概率 π 被揭示（reveal），揭示的标签在步 t + L 交付（FIFO，按到期步排序，并在该步路由决策**之前**交付）；
  回合结束时尚未交付的标签：L 有限则以真实标签冲刷（flush），L = ∞（never）则永不交付。
- **只有标签被延迟 / 丢弃**：成本出现在买方自己的账单上，仍即时观测（PILOT 的预算分箱 budget bins、StageRoute 的成本估计）。
  为此两个路由器的 `update` 被拆成 `observe_cost`（即时）+ `learn`（标签）；`update` = 两者之和 = v3/v4 行为。
- **审计是独立信号（audits are a SEPARATE signal）**：D3 的审计（a = 0.1，identity + length，d_id = d_len = 0.9，P = 0.25）
  在任何反馈制度下都**即时**运行、罚没（slash）/下架卖方并更新 TrustModel；D3 的路由从不使用正确性标签，
  因此反馈通道只影响它的日志。两个 bandit **不审计**（audit rate = 0）。
- 配置：`market.feedback: {mode: immediate|delayed|sparse|delayed_sparse|never, delay_L: 0, reveal_prob: 1.0}`，
  默认 immediate（`run_sim.py` 默认指标与 v4 逐项一致；`joint_objective / baselines / cost_curves / imperfect_detection /
  token_theft / fraud_audit_threshold` 的 results 重跑后逐字节相同）。揭示抽样使用独立随机流 `feedback-{seed}`。
- 日志新增字段：`feedback_delay_L`（null = ∞）、`feedback_revealed`、`feedback_delivered_at`（交付步；= n_tasks 表示回合末冲刷；null = 永不）。

**实验 F**（`experiments.F`，3 seeds，缓存命中约 8 秒）：同一个 swap+theft 学习型策略卖方（同 J），预算 ×2；
延迟扫描 L ∈ {0, 5, 20, 50, ∞}（π = 1），稀疏扫描 π ∈ {1, 0.2, 0.05, 0}（L = 0），组合点 (20, 0.2)、(50, 0.05)。
输出 `results/feedback_ablation.{md,json,png}`。

| (L, π) | PILOT+合规 J / fraud | StageRoute+合规 J / fraud | **D3 J / fraud** | D3 − 最佳 bandit ΔJ |
|---|---|---|---|---|
| (0, 1) 即时 | 0.789 / 0.045 | 0.811 / 0.023 | 0.766 / 0.101 | −0.045 |
| (5, 1) | 0.785 / 0.044 | 0.814 / 0.017 | 0.766 / 0.101 | −0.047 |
| (20, 1) | 0.782 / 0.042 | 0.797 / 0.019 | 0.766 / 0.101 | −0.030 |
| (50, 1) | 0.748 / 0.076 | 0.788 / 0.024 | 0.766 / 0.101 | −0.022 |
| (∞, ·) never | −0.030 / 0.678 | 0.585 / 0.075 | 0.766 / 0.101 | **+0.181** |
| (0, 0.2) | 0.780 / 0.058 | 0.803 / 0.018 | 0.766 / 0.101 | −0.037 |
| (0, 0.05) | 0.673 / 0.135 | 0.681 / 0.097 | 0.766 / 0.101 | **+0.085** |
| (0, 0) | −0.030 / 0.678 | 0.585 / 0.075 | 0.766 / 0.101 | **+0.181** |
| (20, 0.2) | 0.747 / 0.070 | 0.752 / 0.048 | 0.766 / 0.101 | +0.014（在噪声内） |
| (50, 0.05) | 0.634 / 0.166 | 0.672 / 0.084 | 0.766 / 0.101 | **+0.094** |

卖方学到的攻击率 q_swap / q_theft：两个 bandit 下在所有制度中都保持 0.64–0.95（bandit **避开**攻击者，而不是**威慑**它）；
D3 下所有制度都是 0.08 / 0.08（审计不依赖结果反馈）。

**结论（verdict）：假设在方向上成立（HELD in direction）**。D3 相对最佳 bandit 的 J 优势随延迟 / 稀疏单调增大
（L 扫描 −0.045 → +0.181，π 扫描 −0.045 → +0.181），但：
1. 纯延迟（L ≤ 50，覆盖率 ≥ 0.90）和中度稀疏（π = 0.2）下 bandit 仍然胜出——480 个任务、3 个卖方，少量迟到标签已足够；
   D3 只在标签几乎没有（π ≤ 0.05）、完全没有（L = ∞ / π = 0）或“延迟 **且** 稀疏”（(50, 0.05)；(20, 0.2) 仅 +0.014，在噪声内）时胜出。
2. **欺诈份额（fraud_share）**上 D3（0.101）在任何制度下都不低于 StageRoute+合规：无标签时 StageRoute 的 LP 只剩成本信息，
   退化为“最便宜卖方”（准确率 0.62），**碰巧**避开了 seller_sg；无标签的 PILOT 则按声誉先验把 71% 的购买送给 sg（fraud 0.68）。
   D3 的优势体现在 J 和攻击率 q（威慑），而不是购买层面的欺诈份额。

**真实 vs 模拟（v5）**：正确性标签本身来自**真实**缓存的 Qwen 输出（与 v2–v4 相同，无新生成）；
反馈通道（延迟 L、揭示概率 π、冲刷规则）、审计、卖方学习规则、价格与预算均为**模拟**。

## v4 新增（v4 additions）

**研究定位 / 创新点（novelty framing）**：合规约束下的多模型组合采购（compliance-constrained portfolio purchasing）
+ **不完美审计（imperfect audits）下的策略性欺诈**（模型替换 model swap **与** token 盗刷 token theft），
在**联合目标（joint objective）J** 上与 PILOT 式 / StageRoute 式基线对比。
推理 token 长度不确定性**不再**作为贡献点（见下文“降级说明”）。

v2/v3 的行为、默认命令与测试保持不变：默认配置（`attack_modes_enabled: [swap]`）下 `run_sim.py` 的所有指标与 v3 逐项一致，
`results/fraud_audit_threshold.*` 与 `results/cost_curves.*` 重跑后逐字节相同；新随机流（`theft-*`、`length-audit-*`）不扰动旧的随机抽样。

| 部分 | 内容 | 输出 |
|---|---|---|
| **I** 不完美检测（imperfect detection） | 审计率 a × 检测概率 d ∈ {0.3,0.5,0.7,0.9,1.0}（**漏检率 / 假阴性率 miss rate = false-negative rate = 1−d**；假阳性 false positive = 0）× 罚金 P ∈ {0.1,0.5}；解析阈值 a\*(d) = saving/(d·P) 与学习型卖方的经验阈值 | `results/imperfect_detection.{md,json,png}` |
| **T** token 盗刷卖方（token-theft seller） | seller_sg 每轮学习 (q_swap, q_theft)；攻击模式 attack_mode ∈ {none, swap, theft, both}；身份审计（identity）/ 长度审计（length，`TokenLengthAuditor`）/ 两者 | `results/token_theft.{md,json}` |
| **J** 联合目标（joint objective，**v4 主表 headline**） | 10 个策略在 swap+theft 策略卖方下按 J 排名，(λ, μ) 敏感性，等成本视图（equal-cost view）；原准确率表作为附录 | `results/joint_objective.{md,json}`；`results/baselines.md` 增加 J 列 |

```bash
PY=/workspace/tmvenv/bin/python
$PY run_experiments.py                         # C, I, T, D, A, J, F, B 全部（缓存命中约 80 秒）
$PY run_experiments.py --only I T J            # 只跑 v4 部分（约 45 秒）
$PY -m pytest -q                               # 63 个测试（39 个 v2/v3 + 12 个 v4 + 12 个 v5），约 1.8 秒
$PY run_experiments.py --only F                # 只跑 v5 反馈消融（约 8 秒）
```

### 联合目标（Joint objective）

**J = accuracy − λ · compliance_violation_rate − μ · fraud_share**，默认 **λ = 1.0，μ = 0.5**（`market.joint`），敏感性 (λ, μ) ∈ {(1, 0.5), (0.5, 0.25), (2, 1), (1, 0)}。

- accuracy = 任务准确率（最终答案 == gold；无答案算错）；
- compliance_violation_rate = 合规违规数 / **任务数**（per task，与 accuracy 同分母）；
- fraud_share = 被攻击的购买 / **购买数**（per purchase）；被攻击 = 模型替换（actual_model ≠ claimed_model）**或** token 盗刷（billed_tokens > actual_tokens，即 attack_mode ∈ {swap, theft, both}）。

**主基线是 PILOT + 合规过滤（`pilot_compliant`），比较 J 而不是原始准确率。** 结果（swap+theft 学习型卖方，预算 ×2，3 seeds，`results/joint_objective.md`）：

| 排名 | 策略 | J | 准确率 | 违规率 | 欺诈占比 |
|---|---|---|---|---|---|
| 1 | stageroute_compliant | 0.811 | 0.822 | 0 | 0.023 |
| 2 | **pilot_compliant（主基线）** | 0.789 | 0.811 | 0 | 0.045 |
| 3 | **audited_compliance_cascade（D3，我们的）** | 0.766 | 0.817 | 0 | 0.101 |
| 4–5 | stageroute / pilot（无合规过滤） | 0.735 / 0.697 | 0.868 / 0.853 | 0.128 / 0.137 | 0.011 / 0.040 |

**诚实结论（honest finding）**：在默认操作点，D3 的准确率略高于 PILOT+合规，但 J 落后 0.022。原因是残余欺诈占比 0.10：
D3 把学习型卖方的 q_swap / q_theft 压到约 0.08，但 ε 探索使攻击无法降到 0，而 D3 的级联仍会向 seller_sg 购买。
PILOT/StageRoute 则使用购买后的**真实正确性（神谕反馈 oracle feedback）**，学会绕开被攻击卖方。
在 (λ, μ) = (1, 0)（不计欺诈）下 D3 排第 2，高于 PILOT+合规。等成本视图中，D3 只有在更高预算（成本/任务 ≈ 0.0275）时
J 才达到 0.80–0.81，超过 PILOT+合规能达到的最高值 0.789（PILOT 在约 0.0235 处饱和，不会花更多）；
在相同的较低成本下 PILOT+合规更好。原始准确率表保留为附录，未删减任何内容。

### 不完美检测（Imperfect detection, I）

- `IdentityCheckDetector`：以概率 d 检出替换；**漏检率 / 假阴性率 = 1 − d**（`miss_rate`）；**假阳性率 = 0**（`false_positive_rate`，诚实答案永不被标记）。
- 解析阈值 **a\*(d) = saving / (d · P)**，对 d 单调递减：d 减半，所需审计率加倍；d → 0 时 a\* → ∞（测试覆盖）。
- 结果：10 个 (P, d) 组合中，7 个的经验阈值恰好落在解析 a\* 之上的第一个网格点；另外 3 个晚一个网格点，都发生在 a 紧贴 a\* 处（收益 ≈ 0）。
  例：P = 0.1、d = 0.3 时 a\* = 0.33，a ≤ 0.3 时学到的 q 仍为 0.96。

### Token 盗刷（Token theft, T）

- **攻击**：卖方宣称长链/高投入生成，按 `billed_token_policy` 计费：`claimed_mean`（按宣称模型广告的平均 token 数，默认）或
  `inflated_factor`（× 完整长度，默认 2.0）；实际只生成 `theft_max_new_tokens`（默认 48）个 token。
  **买方按计费 token（billed）付款，卖方按实际 token（actual）承担成本**。
  对真实 Qwen 输出，盗刷是**对缓存的真实输出按字符比例截断**并重新解析答案（不重新生成）；截断后的答案几乎都错。
  mock 卖方则模拟截断：正确答案以 max_tokens/tokens 的概率保留。
- **攻击选择**：`AttackStrategy` 每轮在 {0, 0.1, …, 1}² 上选 (q_swap, q_theft)，用 ε-greedy / Hedge 基于自身实际利润学习；每笔独立抽 swap 与 theft，
  得到 attack_mode ∈ {none, swap, theft, both}。`SwapStrategy` 保留为向后兼容的薄封装（theft 关闭，随机抽样与 v3 完全相同）。
  解析收益：theft_saving = (price·E[billed − full] + cost·E[full − actual]) / 1000 ≈ 0.0113（替换为 0.0100），阈值 a\*_theft = theft_saving / (d_length · P)。
- **长度审计 `TokenLengthAuditor`**：当 billed > actual·(1 + tol)（`length_audit_tol` = 0.1）或 billed − actual > abs_gap 时标记，检测概率 d_length（漏检率 1 − d_length）；
  诚实计费永不误报。**这是模拟审计（SIMULATED）**：真实买方通常看不到隐藏的推理 token。
  可选 `length_audit_reference: true`：与宣称模型在同一 prompt 上**缓存的真实贪心生成长度**交叉核对（真实信号，对替换答案可能误报）。
- 被任一检查抓到即罚没一次 P（两项同时命中也只罚一次）。
- **结果（a = 0.1，d = 0.9/0.9，P = 0.5）：每种攻击都需要对应的审计**：

| 攻击 | 无审计 | 仅身份 | 仅长度 | 身份 + 长度 |
|---|---|---|---|---|
| swap-only | ✗ | ✓ | ✗ | ✓ |
| theft-only | ✗ | ✗ | ✓ | ✓ |
| both | ✗ | ✗ | ✗ | ✓ |

  只做身份审计时，组合攻击者停止替换但继续盗刷（q_theft 0.97，买方准确率 0.18）；两种审计都做时准确率回到 0.83。
  不审计时，inflated_factor = 2 的盗刷让买方多付 31.5（合成 USD），准确率 0.17。

### 降级说明：推理 token 长度不确定性（demoted: reasoning-token length uncertainty）

期望 vs 实际成本日志（expected_cost / actual_cost / cost_overrun / budget_overrun）和长数学任务表（B）保留为**基础设施（infrastructure）
与负面发现（negative finding）**：逐笔超支在长输出下可以很大，但正常预算下预算违规 ≈ 0，只有紧预算时才会约束。
**这一点不再作为研究贡献（not a contribution claim）。**

### 日志字段（schema v4）

`billed_tokens`（计费 token）、`actual_tokens`（实际生成 token，= `reasoning_tokens`）、`token_inflation`（= billed/actual）、
`attack_mode`（none|swap|theft|both）、`theft_prob`（卖方当前 q_theft）、`audit_type`（none|identity|length|both）、
`swap_detected` / `theft_detected`（对应检查未运行时为 null）、`detect_prob_identity` / `detect_prob_length`（买方审计制度的 d；该检查不在制度内时为 null）。
`cost` = price × **billed_tokens** / 1000。

### 配置（`fraud:` / `market:`）

`fraud.detect_prob`（身份 d）、`detect_prob_length`、`attack_modes_enabled: [swap]`（默认 = v3；`[swap, theft]`、`[theft]`、`[]` = 诚实）、
`billed_token_policy: claimed_mean | inflated_factor`、`inflated_factor`、`theft_max_new_tokens`、`length_audit_tol`、`length_audit_abs_gap`、
`length_audit_reference`、`q_theft_static`；`market.audit.types`（非 D3 策略，默认 `[identity]`）、`market.audited.audit_types`
（D3，默认 `[identity, length]`）、`market.audited.theft_quality_factor`、`market.joint: {lambda, mu}`。
v4 扫描在 `configs/experiments.yaml` 的 `experiments.I / T / J`。

### 真实 vs 模拟（v4）

**真实**：Qwen 输出、正确性、token 数，以及盗刷截断所依据的缓存输出和可选的参考长度交叉核对。
**模拟**：两种审计与检测（身份 d、长度 d_length、漏检率 1 − d、零假阳性）、罚金、卖方学习与攻击选择、mock 截断模型、价格/成本。

## v3 新增（v3 additions）概览

v2 的行为、默认命令与测试保持不变（默认配置下 `run_sim.py` 的结果与 v2 逐项一致）。v3 新增：

| 部分 | 内容 | 输出 |
|---|---|---|
| **C** 策略性模型替换卖方（strategic model-swap seller） | seller_sg 每轮（epoch）选择替换概率 q；买方按审计率（audit_rate）审计，检测概率 d，罚没押金（penalty / stake slash）P，可选下架 k 轮（reputation loss） | `results/fraud_audit_threshold.{md,json,png}` |
| **D** 基线（baselines） | PILOT 式 LinUCB + ON-MCKP ZCL、StageRoute 式每查询 LP 路由（各有无合规过滤两版），与 v2 策略及**我们的** `audited_compliance_cascade`（D3）对比 | `results/baselines.{md,json}` |
| **A** 准确率-成本曲线（accuracy-vs-cost curves） | 所有策略 × 预算倍数 / 策略旋钮扫描，等成本准确率（accuracy at equal cost）与帕累托前沿（Pareto frontier） | `results/cost_curves.{md,json,png}` |
| **B** 长推理任务（long reasoning tasks） | 48 道真实题（28 道 GSM8K 最难题 + 20 道 MATH-500 整数答案 L≥3），两个 Qwen 模型真实输出；长输出下的期望/实际成本与预算超支 | `results/long_math.{md,json}`、`results/long_math{,_tight}/summary.md` |
| 汇总 | 以上关键表 + "What is real vs simulated" | `results/experiments_summary.md` |

```bash
PY=/workspace/tmvenv/bin/python
$PY run_sim.py --config configs/default.yaml          # v2 默认仿真（缓存命中 < 1 秒）
$PY run_experiments.py                                # C、D、A、B（B 需长任务缓存）；缓存命中约 25 秒
$PY run_experiments.py --only C D --backend-override mock --seeds 0   # 全 mock 快速版（约 2 秒）
$PY run_sim.py --config configs/long_math.yaml        # 在长任务池上运行市场
$PY run_sim.py --config configs/long_math.yaml --precompute-only     # 长任务预计算（本机 818 秒）
$PY scripts/build_long_tasks.py                       # 从 data/raw 重建 data/long_tasks.jsonl（确定性）
$PY -m pytest -q                                      # 63 个测试（v5），全部 mock / 假 runner，约 1.8 秒
```

配置：`configs/default.yaml`（新增 `fraud:`、`market.audit / audited / pilot / stageroute / budget_multiplier`、
`task_pool.kind`、`backends.local_hf.long_*`）；`configs/experiments.yaml` 与 `configs/long_math.yaml` 通过
`extends: default.yaml` 继承（深度合并 deep merge，列表整体替换；`tokenmarket/config.py`）。
新模块：`tokenmarket/strategic.py`（C 与审计/信任模型）、`tokenmarket/baselines.py`（D1/D2）、
`tokenmarket/experiments.py`（A/B/C/D 实验与报告）、`run_experiments.py`。

### 交易日志新增字段（schema v3）

`audited`（本笔是否被审计）、`audit_cost`（审计费，计入买方预算）、`swap_detected`（审计结果；未审计为 null）、
`swap_prob`（卖方当前 q；诚实卖方 0；unfilled 为 null）。`actual_model` = 本笔**实际服务**的模型（策略卖方逐笔变化）。
`seller_profit` 已扣除被罚没的押金。

### C：策略性替换卖方与审计阈值

- seller_sg 宣称 1.5B；以概率 q 服务 0.5B（成本 0.05/1K），否则服务 1.5B（成本 0.12/1K）。
  `fraud.strategy`：`static`（v2 行为，恒替换，默认）| `analytic` | `logit` | `learning`（实验使用）。
- **解析最优反应（analytic best response）**：每笔替换期望收益 = cost_saving − a·d·(P + R)，
  cost_saving = cost_gap × 宣称模型平均 token / 1000 ≈ 0.07 × 142.3 / 1000 = 0.00996；q* = 1[收益 > 0]，
  阈值 **a\* = cost_saving / (d·P)**。
- **学习型卖方（learning seller）**：不知道 a、d、P，只用自己**实际实现的利润**（含被罚没的押金）——
  对 q 网格 {0, 0.1, …, 1} 做 ε-greedy（默认，ε=0.1）或 Hedge，利用“期望利润对 q 线性”从替换/诚实两类购买的利润均值估计每个 q 的收益。
- **审计/检测为模拟（simulated）**：身份核验以概率 d 检出替换（漏检率 / 假阴性率 1−d，v4 实验 I 扫描 d），诚实答案不会误报（假阳性 = 0）；`TokenFingerprintDetector` 只是桩（stub）。
  罚金从卖方押金扣除，**不退给买方**（对买方保守）。审计费 `market.audit.cost`（默认 0.004/次）计入买方预算；
  只在剩余预算足够时审计，因此审计本身不会造成预算超支。
- 实验：买方策略 `single_best_compliant`（把大部分需求送给欺诈卖方），a ∈ {0,…,0.5} × P ∈ {0.02, 0.1, 0.5}，
  960 任务 / 96 轮 × 3 seeds。**结果：三个罚金水平下，经验阈值（学到的 q < 0.1 的最小网格审计率）都落在解析 a\* 之上的第一个网格点**
  （P=0.1：a\*=0.111 → 经验 0.2；P=0.5：a\*=0.022 → 经验 0.05；P=0.02：a\*=0.55 超出网格，始终替换）。
  在 a 恰好接近 a\* 的点（收益≈0）学习结果在 seeds 间分化。

### D：基线（我们的简化复现，our simplified reimplementations）

| policy | 论文 | 我们的简化 / 与论文的差别 |
|---|---|---|
| `pilot`, `pilot_compliant` | PILOT（Panda et al., arXiv:2508.21141, *Adaptive LLM Routing Under Budget Constraints*） | LinUCB，臂 = 卖方；上下文 = 难度 one-hot、任务类型/来源 one-hot、log 提示长度、偏置（论文用查询嵌入 query embeddings）；“偏好先验（preference prior）” = **宣称模型声誉**：A=λI，b=λθ_prior；奖励 = 购买后观察到的正确性（与论文一样信任观测结果）；成本策略 ON-MCKP ZCL：合格条件 est_cost ≤ est_reward / ((UB·e/LB)^z·(LB/e))，z = 当前预算箱使用率，预算分箱 + 结转（spillover），无合格臂时退化为 B_left/Q_left；取 UCB 最高的合格臂；一个 LinUCB 由所有买方共享，预算按买方 |
| `stageroute`, `stageroute_compliant` | StageRoute（Li & Li, arXiv:2506.17254, *Near-Optimal Online Deployment and Routing for Streaming LLMs*） | 只实现每查询路由 LP：max Σ μᵁ p s.t. Σ cᴸ p ≤ b = B/T, Σp=1, 0≤p≤α（α = 卖方容量份额），按 p 抽样；f_rad(v,n)=√(γv/n)+γ/n；**跳过分阶段部署 MIP**（只有 3 个固定卖方）；LP 用顶点枚举精确求解（无求解器依赖） |
| `audited_compliance_cascade`（**D3，我们的**） | — | 硬合规过滤 + 预算 + v2 级联，**外加**按 `market.audited.audit_rate`（默认 0.1）审计；每卖方信任模型：检出后路由质量从宣称模型降为 (1−q̂)·rep(宣称)+q̂·rep(审计揭示的实际模型)，q̂ = 检出数/(审计数·d)（平滑）；被检出即罚没押金 |

两个文献基线都**没有**审计成本、策略性卖方模型和合规过滤（`_compliant` 变体加上硬过滤以公平比较；无过滤版本走 audit_only 网关，违规被计数）。
**主要发现（strategic seller, P=0.25, d=0.9，3 seeds，见 `results/baselines.md`）**：
- 非审计策略面对的 a=0，卖方学到 q≈0.95；D3（a=0.1 > a\*≈0.044）把 q 压到 ≈0.13，欺诈服务占比从 v2 级联的 0.30 降到 0.04，
  准确率 0.811 vs 级联 0.768，总成本（含审计费 0.23）更低。
- PILOT 式基线准确率最高（0.883 / 带过滤 0.856），因为它**使用购买后的真实正确性作为反馈**——在真实市场中买方通常没有 gold
  （有 gold 就不必买答案），这是它的“神谕反馈（oracle feedback）”优势；无过滤版本有 ~78 次合规违规。等成本比较见 A。

### A：准确率-成本曲线

`configs/experiments.yaml: experiments.A`：预算倍数 {0.2,…,5.0} × {single_cheapest, single_best, cascade, PILOT(两版), StageRoute(两版), D3}，
级联置信阈值 {0.1,…,0.95}、vote k=1..3（并各自扫描预算）、D3 审计率 {0.02,…,0.3}；共 102 个点 × 3 seeds。
成本 = 每任务平均成本**含审计费**。`results/cost_curves.md` 给出所有点（mean ± std）、等成本准确率（各族帕累托包络线性插值）与全局帕累托前沿；
`results/cost_curves.png` 为图（matplotlib 已装入 venv）。

### B：长推理任务

- 子集：`data/long_tasks.jsonl`（`scripts/build_long_tasks.py`，seed 2024）：GSM8K 测试集按参考解步数/长度排序取前 84 再抽 28；
  MATH-500 取答案匹配 `^-?\d+$` 且 level ≥ 3 的题抽 20。记录 source、index/id、level、gold。市场中难度记为 4（GSM8K-hard）/ 5（MATH-500）。
- `task_pool.kind: synthetic | long_math | mixed`；`configs/long_math.yaml` 在长任务池上跑市场（144 任务/run，预算 ×3）。
- 长任务 prompt：逐步求解并以 `Answer: <integer>` 结尾；缓存键方案不变（模型, sha256(prompt), max_new_tokens）。
- **max_new_tokens = 512（目标 768 已降低）**：基准测试（benchmark）显示 fp32 下 0.5B 一个 16 题批次 768 token 需 146–618 秒，
  且 1.5B fp32（≈6.2 GB）超出本机可用内存；改用 **bf16**（CPU 有 AMX/AVX512-bf16）后 1.5B 约 0.52 s/step，768 预计约 30 分钟 > 25 分钟预算，
  因此按规则降到 512。实际预计算 818 秒（0.5B 149 秒，1.5B 669 秒）。合成任务池仍是 fp32（v2 缓存不变）；缓存行记录 `dtype` 与 `source`。
- 实测（`results/long_math.md`）：1.5B 准确率 0.438（GSM8K-hard 0.536，MATH-500 0.300），0.5B 0.146；token 均值约 414–425 ± 90，
  p95 = max = 512，截断率 29% / 42%（两个模型大多用 `\boxed{}` 而非 `Answer:`，解析器回退到最后一个数字）。
- **C2(d) 成本不确定性（v4：仅作基础设施 / 负面发现，不是贡献点）**：期望成本按宣称模型平均 token 计，长输出下逐笔相对超支（relative overrun）p95 达 +120%–150%，最大 +219%；
  但正常预算（×3）下**预算违规几乎为 0**（vote_k 1 次）——因为只有期望成本 ≤ 剩余预算才购买，且单笔成本相对预算很小，
  只有预算即将耗尽的那一两笔可能超支。**紧预算变体（×0.5）**下预算真正约束，每个策略出现 2–10 次预算违规（3 seeds 合计），
  最大超支约 0.018 USD（合成单位）。

### 真实 vs 模拟（What is real vs simulated）

- **真实**：Qwen2.5-1.5B / 0.5B-Instruct 的输出（本地 CPU 推理并缓存）、与 gold 比对的正确性、推理 token 数、CPU 生成时间；GSM8K / MATH-500 题目与答案。
- **模拟**：价格、服务成本与成本差、延迟噪声与通道惩罚/费用、辖区与（简化的，非法律意见）合规规则、买方/预算/敏感度、
  审计与替换检测、罚金/押金罚没/下架、卖方学习规则、mock 卖方（seller_br）及其置信度。

### 数据与许可（Data & licences）

GSM8K（MIT, Copyright (c) 2021 OpenAI）与 MATH-500 / PRM800K（MIT, Copyright (c) 2023 OpenAI），详见 `LICENSES/DATA_LICENSES.md`。
原始测试集 `data/raw/*.jsonl`（约 1.2 MB）**直接提交入库**，以便确定性地重建子集；`data/long_tasks.jsonl` 与 `cache/llm_outputs.jsonl`（含 2×48 条长任务输出）也入库。
实验交易日志 `results/experiments/*.jsonl` 与 `results/long_math*/transactions.jsonl` 较大，不入 git。

## 研究问题 C2（Research question）

**在硬性合规约束（hard compliance constraints）与预算约束（budget constraint）下，买方如何对多个模型做组合采购（portfolio purchasing）？**

- (a) **数据出境规则是硬约束**：不合规的卖方在购买**之前**被过滤掉（filtered），而不是加罚分（never just penalized）。
  合规检查使用已有的数据驱动规则引擎（rule engine：CN PIPL/DSL、SG PDPA、BR LGPD）。
- (b) **买方预算约束**：若一笔购买的**期望成本（expected cost）**超过剩余预算，则不购买；同时记录实际支出（realised spend）。
- (c) **按任务购买模型组合**（不仅是单卖方路由）：级联（cascade）与投票（vote）。
- (d) *基础设施（infrastructure），v4 起不再是贡献点*：按每千推理 token 计价；购买前按卖方宣称模型的平均 token 数
  计算 expected_cost，购买后按实际 token 数计算 actual_cost，记录成本超支（cost_overrun）与预算超支（budget_overrun）。
  负面发现：正常预算下预算违规 ≈ 0，只在紧预算下约束。
- (e) **v4：不完美审计下的策略性欺诈**（模型替换 + token 盗刷），以联合目标 J 评估（见上文 v4）。
- 路由使用的质量估计（estimated quality）= **卖方宣称模型（claimed model）的声誉**，因此模型替换欺诈卖方会欺骗基于质量的路由
  —— 这把 C2 与 B2（欺诈检测）联系起来。

## 卖方（Sellers，默认 3 个）

| id | 辖区 | 后端 backend | claimed_model | actual_model | 价格/1K token | 成本/1K | 说明 |
|---|---|---|---|---|---|---|---|
| seller_cn | CN | `local_hf`（真实） | Qwen/Qwen2.5-1.5B-Instruct | Qwen/Qwen2.5-1.5B-Instruct | 0.20 | 0.12 | 诚实卖方 |
| **seller_sg** | SG | `local_hf`（真实） | **Qwen/Qwen2.5-1.5B-Instruct** | **Qwen/Qwen2.5-0.5B-Instruct** | 0.18 | 0.05 | **模型替换欺诈（model-swap fraud）**：宣称 1.5B，实际跑 0.5B；价格略低于 seller_cn |
| seller_br | BR | `mock`（模拟） | sim-fast-mock | sim-fast-mock | 0.06 | 0.03 | 快速/便宜的模拟模型 |

- 每个卖方的 `backend` 可选 `local_hf | mock | real`。真实卖方的质量差异**完全来自模型实际输出与 gold 的比对**，不是预设值。
- 每笔交易都记录 `claimed_model` 与 `actual_model`（供 B2 检测研究）。
- 实测准确率见 `results/model_accuracy.md`（例如本机：1.5B 总体 0.925，0.5B 总体 0.662）。

## 快速开始（How to run）

```bash
PY=/workspace/tmvenv/bin/python      # 需要 torch(CPU) + transformers + pyyaml + pytest
$PY run_sim.py --config configs/default.yaml                     # 首次: 预计算(precompute) 两个模型 × 80 题（本机约 8 分钟），之后 < 1 秒
$PY run_sim.py --config configs/default.yaml --precompute-only   # 只做预计算，填充缓存
$PY run_sim.py --config configs/default.yaml --backend-override mock   # 所有卖方用 mock：无需 torch，CI/测试用
$PY run_sim.py --config configs/default.yaml --auction-format first_price
$PY -m pytest -q                                                 # 测试全部使用 mock override，不加载模型，< 1 秒
```

`transformers`/`torch` 为**懒加载（lazy import）**：mock-only 运行不需要安装 torch（有测试保证）。

输出（outputs）：
- `results/transactions.jsonl`：统一交易日志（不入 git）。
- `results/summary.md` / `results/summary.json`：C2 对比表、机制对比表等，mean ± std over 3 seeds。
- `results/model_accuracy.md`：本地模型实测准确率（按难度/总体）、推理 token 均值/标准差、生成耗时。
- `cache/llm_outputs.jsonl`：模型输出缓存（入 git，便于快速重跑）。

## 预计算与缓存（Precompute & output cache）

1. **固定任务池（fixed task pool）**：80 道短推理题（算术 arithmetic、应用题 word problem、数列 sequence、简单逻辑 logic），
   难度 1–3，整数 gold。任务池只由 `task_pool.task_seed` 决定，**与运行 seed 无关**，因此缓存总能命中。
2. **Prompt**：要求模型简短推理，并以 `Answer: <number>` 结尾；chat template，贪心解码（greedy），fp32，左填充（left padding），
   批量生成（batch 16），`torch.set_num_threads(8)`，`max_new_tokens=256`。
3. **预计算阶段**：对每个**不同的实际本地模型（distinct actual local model）**在整个任务池上跑一次；**一次只加载一个模型**，
   用完 `del + gc` 释放再加载下一个。批次按难度/题长排序（一个 batch 的耗时取决于其中最长的生成）。
4. **缓存键（cache key）** = `(model_name, sha256(prompt), max_new_tokens)`；每行保存 raw text、解析答案 parsed_answer、
   是否显式 `Answer:`、correct、reasoning_tokens（实际生成 token 数，不含 EOS/padding）、gen_time_s 等。
   改 prompt 或 max_new_tokens 会自动失效并重新计算缺失项。任务池中有 3 道题文本重复（共用同一缓存键），所以缓存为 2 × 77 = 154 行。
   本机实测：首次冷启动 `run_sim.py` 总耗时 9 分 39 秒（预计算 577 秒：0.5B 361 秒，1.5B 216 秒），缓存命中后重跑约 0.6 秒。
5. **答案解析（robust parser）**：取最后一个 `Answer:` 后的数字（容忍 `**`、`$`、`\(`、`\boxed{` 等修饰），否则取全文最后一个数字。
6. **seed 的作用**：seed 改变市场动态 —— 每次运行从任务池中按 seed 抽样/打乱（240 个任务实例 = 3 个独立排列），
   以及买方分配、数据敏感度、同意标记、拍卖报价、延迟噪声、mock 卖方答案；真实模型输出对同一题是确定的。
7. **真实卖方延迟（latency）** = `latency.mean_ms`（辖区/网络开销） + 实测 `gen_time_s × 1000 × latency_scale` + N(0, `std_ms`)
   + 网关通道延迟惩罚。`gen_time_s` 是批次墙钟时间按生成 token 数分摊到每题的份额（CPU 时间，`latency_scale` 可设 0.1 模拟 GPU）。

## 采购策略（Policies, `tokenmarket/portfolio.py`）

所有策略先按买方 `allowed_jurisdictions`（买方偏好）与卖方本轮剩余容量（capacity）过滤。

| policy | 合规 | 行为 |
|---|---|---|
| `single_cheapest_compliant` | 硬过滤 | 合规卖方中期望成本最低者 |
| `single_best_compliant` | 硬过滤 | 合规卖方中估计质量（宣称模型声誉）最高者，平局取更便宜 → 会被 seller_sg 欺骗 |
| `cascade_compliant` | 硬过滤 | 先买最便宜的合规卖方；若置信度 < 阈值（0.7）则升级（escalate）到**估计质量 ≥ 当前**的未购卖方中最便宜者；直到置信、卖方耗尽、预算不足或达到 max_steps |
| `vote_k_compliant` | 硬过滤 | 按估计质量取前 k=3 个合规卖方各买一次，多数投票（majority vote）；平局取估计质量更高卖方的答案；预算不足的那一笔跳过 |
| `compliance_unaware_cheapest` | **忽略规则（基线 baseline）** | 不做合规过滤，选最便宜者；其流量经过**审计模式网关（audit_only）**：违规流量放行（status=allowed）但标记 `violation=true` 与 `rule_id`，用来统计"没有硬约束会怎样" |

**置信度信号（confidence signal）**：
- 真实模型（local_hf）：免费、可缓存的**答案格式/自洽代理（answer-format / self-consistency proxy）**，不额外调用模型：
  无可解析数字 0.0；没有显式 `Answer:` 行或生成被 max_new_tokens 截断 0.2；多个 `Answer:` 值互相矛盾 0.4；
  显式答案但推理过程中从未出现该数值 0.6；显式、一致、且在推理中推导出 0.9。
- mock：带噪声的弱信息置信度 N(0.75 | 0.45, 0.15)（答对 | 答错），截断到 [0,1]。

**撮合机制（mechanisms）**：C2 策略对比默认在**固定挂牌价（posted price）**下运行；单卖方策略另外在**密封报价反向拍卖
（sealed-bid second-price scoring auction）**下运行（报价 = 成本 × U(1.1,1.8)，score = bid / quality，best 策略用估计质量加权，
其余 quality=1；二价：赢家价格使其评分与第二名持平，以保留价封顶）。`--auction-format first_price` 可切换一价。

## 合规规则（Compliance rules — 简化模拟，非法律意见）

规则写在 `configs/default.yaml` 的 `compliance.rules`，按顺序评估，仅作用于跨境流（买方辖区 ≠ 卖方辖区）。

| rule_id | 来源 | 敏感度 | 放行条件（allow_if） | 含义（简化） |
|---|---|---|---|---|
| GEN-PUBLIC | ANY | public | 无条件 | 公开数据可流向任何辖区 |
| CN-DSL-31 | CN | important_data | 卖方有 `cn_security_assessment` | 重要数据出境须安全评估（默认无卖方具备 → 不可出境） |
| CN-PIPL-40 | CN | sensitive_personal | 卖方有 `cn_security_assessment` | 敏感个人信息出境须安全评估 |
| CN-PIPL-38 | CN | personal | 安全评估 / 标准合同 / 认证 之一 | 个人信息出境须合法机制 |
| SG-PDPA-26 | SG | personal, sensitive_personal | 目的地在充分性名单（虚构 `[BR]`）或卖方有 `sg_contractual_safeguards` | 转移限制义务 |
| BR-LGPD-33-VIII | BR | sensitive_personal | 任务带 `specific_consent` | 敏感数据跨境须特定同意（简化） |
| BR-LGPD-33 | BR | personal, sensitive_personal | 充分性 / 卖方 `br_scc` / 特定同意 | 国际传输的合法基础 |

网关（gateway）有两种模式：`enforce`（硬约束策略使用；违规即拦截 blocked）与 `audit_only`（基线使用；违规放行但记录）。
每笔放行流量还会被规则引擎独立复核（post-hoc audit）。

## 交易日志 Schema（Unified JSONL log, `tokenmarket/logging_schema.py`）

**每笔交易一行**：交易 = 一次对单个卖方的购买（allowed 或 blocked）；级联/投票中的**每一次卖方购买都是单独一行**
（`portfolio_step` = 0,1,2…）。没有发生任何购买的任务写一行 `unfilled`。
**每个任务的最后一行 `final=true`**，携带组合的最终决策 `final_answer` / `final_correct`；其余行 `final=false` 且这两个字段为 null。
同一任务各行的 `buyer_surplus` 求和 = 该任务的买方剩余（答对价值记在 final 行上）。写入前强制校验。

| 字段 | 说明 |
|---|---|
| ts, round, run_id, mechanism, policy, seed | 运行标识 `机制__策略__seedN` |
| buyer_id, buyer_jurisdiction | 买方 |
| task_id, pool_task_id, portfolio_step | 任务实例 id（`t<k>_<池 id>`）、任务池 id、组合内购买序号 |
| task_type, difficulty, sensitivity | 任务属性 |
| seller_id, seller_jurisdiction, claimed_model, actual_model, backend | 卖方；backend = local_hf / mock / real（unfilled 时为 null） |
| cross_border, price_per_1k, reasoning_tokens | 是否跨境、成交价（每千推理 token）、实际推理 token |
| cost, fee | 付给卖方 = price × billed_tokens/1000（v4：诚实时 billed = 实际 token）；网关通道费 |
| expected_cost | 购买前：price × 宣称模型平均 token/1000 × (1+fee_rate) |
| actual_cost, cost_overrun | 实际支出 = cost + fee；actual − expected |
| budget_remaining, budget_overrun | 本行之后的剩余预算；实际累计支出是否超过预算 |
| latency_ms | 卖方延迟（见上） + 跨境惩罚 |
| answer, gold, correct, confidence | 本次购买的答案 / 标准答案 / 是否正确 / 置信度 |
| status | `allowed` / `blocked`（合规拦截）/ `unfilled`（市场原因：`MKT-BUDGET-EXHAUSTED`、`MKT-NO-COMPLIANT-SELLER`、`MKT-NO-CAPACITY`…） |
| violation, rule_id | 违规流量是否通过（仅 audit_only 可能为 true）；blocked/违规时为规则 ID，unfilled 时为 MKT-* 原因 |
| final, final_answer, final_correct | 任务最终决策（仅 final 行） |
| buyer_surplus, seller_profit, verification_status | 买方剩余 / 卖方利润 / v2 恒为 `unverified` |

## 指标定义（Metrics, `results/summary.md`）

- **task accuracy**：最终组合答案 == gold 的任务占比（无答案的任务算错）。
- **total cost / mean cost per task**：Σ actual_cost（含通道费）/ 任务数。
- **expected vs actual cost gap**：Σ(actual_cost − expected_cost)，及相对 Σ expected 的比例。
- **budget violations**：购买后实际累计支出超出预算的购买次数（budget_overrun=true），及占购买数的比率。
  由于只有 expected_cost ≤ 剩余预算才购买，超支只可能来自 token 长度不确定性。
- **compliance violations**：违反规则却实际跨境的购买数（violation=true）。硬约束策略必须为 0；基线在 audit_only 下计数。
- **blocked/filtered**：被硬合规过滤掉的卖方候选数 + 网关拦截次数。
- **cross-border share / fraud-seller share**：跨境购买占比 / 由模型替换卖方服务的购买占比。
- **buyer surplus**：Σ value_per_correct × final_correct − Σ actual_cost；**seller profit**：收入 − 实际模型服务成本。
- 另有：机制对比表、各卖方实际准确率与欺诈准确率差（fraud acc gap = 宣称模型声誉 − 实际准确率）、各买方剩余/预算使用率、
  按规则统计的违规与过滤、级联/投票停止原因、路由所用声誉（实测 measured 或配置先验 config_prior）。

## 模块（Modules）

| 文件 | 作用 |
|---|---|
| `tokenmarket/tasks.py` | 固定任务池 `build_task_pool`、按 seed 抽样 `sample_run_tasks`（v1 的 `generate_stream` 保留） |
| `tokenmarket/backends.py` | `MockLLM`、`LocalHFRunner`（批量生成）、`CachedLocalBackend`（仿真时从缓存服务）、`RealLLMBackend`（OpenAI 兼容接口）、答案解析与置信度 |
| `tokenmarket/cache.py` | 输出缓存 `OutputCache` |
| `tokenmarket/precompute.py` | 预计算阶段、模型实测统计、`model_accuracy.md` |
| `tokenmarket/portfolio.py` | C2 组合采购策略、多数投票 |
| `tokenmarket/matching.py` | 候选卖方过滤（硬约束）、密封报价拍卖 |
| `tokenmarket/sellers.py` / `buyers.py` | 卖方（含 backend）与声誉 `Reputation`；买方（预算） |
| `tokenmarket/compliance.py` / `gateway.py` | 规则引擎；跨境网关（enforce / audit_only、通道费与延迟） |
| `tokenmarket/logging_schema.py` / `metrics.py` / `sim.py` | 日志 schema 与校验；指标；仿真主循环 |
| `tokenmarket/verification.py` | 验证与结算接口（B1 桩） |
| `tokenmarket/strategic.py` | v3：策略性替换卖方（analytic / logit / learning）、模拟身份核验、D3 信任模型；v4：`AttackStrategy`（swap + theft）、`TokenLengthAuditor`、漏检率 |
| `tokenmarket/baselines.py` | v3：PILOT 式（LinUCB + ZCL）与 StageRoute 式（每查询 LP）路由器 |
| `tokenmarket/experiments.py` / `run_experiments.py` | v3：A/B/C/D 实验与报告；v4：I（不完美检测）、T（token 盗刷）、J（联合目标）；v5：F（延迟/稀疏反馈消融）|
| `tokenmarket/config.py` | v3：`extends:` 配置继承 |
| `tokenmarket/feedback.py` | v5：`FeedbackBuffer`（延迟 L / 揭示概率 π，FIFO 交付，回合末冲刷）、`FeedbackRouter`（成本即时、标签经缓冲）、`feedback_params` |

## 局限（Limitations）

- **真实 API（real APIs）只有接口**：`RealLLMBackend`（OpenAI 兼容，key 从环境变量读）未在 CI 测试，未处理限流/重试/计费对账。
- **B1 验证为桩（stubs）**：TEE 远程证明（attestation）、水印/指纹（watermark / fingerprint）、token 计数验证均未实现；
  `TrustingVerifier` 信任卖方报告，因此平台本身无法发现 seller_sg 的模型替换（只有日志中的 actual_model 可供离线研究）。
- **合规规则高度简化，不是法律意见**：未建模数据量阈值、CIIO、豁免、再转移、本地化等。
- **小模型 + CPU**：0.5B/1.5B 在 80 道简单题上的准确率与 token 分布不代表大推理模型；gen time 为 CPU 批量摊销时间；
  同一题被重复抽到时真实模型输出相同（贪心 + 缓存），故 seed 间方差主要来自市场动态与 mock 卖方。
- 置信度代理较弱（基于格式与自洽），mock 置信度为合成噪声；v2 策略的声誉是静态的（v3 的 PILOT/StageRoute 在线学习，D3 只按审计更新）；卖方报价为随机加价，非策略性报价。
- v3：审计/检测是概率模拟，不是真实的模型指纹；PILOT/StageRoute 为简化复现且使用真实正确性作为反馈（神谕反馈）；
  长任务 max_new_tokens 受 CPU 限制为 512（截断率 29–42%）且用 bf16；mock 卖方在长任务上的 token 数按难度外推（期望成本偏差为合成结果）。
- v4：两种检测都是概率模拟（零假阳性是建模假设）；盗刷对真实输出的截断是按字符比例近似 token 截断，而非真实地用更小的 max_new_tokens 重新生成；
  攻击者在 (q_swap, q_theft) 上独立随机，罚金每笔最多一次；D3 对盗刷的路由折扣（theft_quality_factor = 0.5）是先验而非估计值；
  J 的权重 (λ, μ) 是规范性选择，结论对其敏感（见敏感性表）。
- v5：延迟以“任务步”计且为常数 L（无随机延迟分布）；揭示是独立伯努利（不依赖正确与否或卖方，非 missing-not-at-random）；
  卖方的学习规则不知道买方的反馈制度（它只对利润与罚金做出反应），因此 bandit 下的 q 主要由 bandit 的路由份额决定；
  480 个任务的短时域使中等延迟几乎无害，更长时域 / 更多卖方下的结论可能不同；D3 在所有制度下数值相同是设计使然（不使用标签）。
