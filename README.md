# token-market v2：合规约束下的多模型组合采购沙盒（Compliance-constrained Multi-model Portfolio Purchasing）

一个**纯虚拟**的跨境推理 token 交易平台（cross-border reasoning-token marketplace）研究沙盒。
CN / SG / BR 三个司法辖区（jurisdiction）的买方（buyers）向卖方（sellers）购买"推理 token"来解答有标准答案的推理题。
v2 的两个卖方是**真实运行的本地小模型**（Qwen2.5-1.5B / 0.5B-Instruct，CPU），一个卖方是模拟模型（MockLLM）。

> ⚠️ **免责声明（Disclaimer）**：合规规则仅为**简化模拟（simplified simulation）**，条款编号只作标签使用，
> **不构成法律意见（NOT legal advice）**。价格、预算、通道费均为合成数据（synthetic）。默认不调用任何真实 API，不需要任何 API key。

## 研究问题 C2（Research question）

**在硬性合规约束（hard compliance constraints）与预算约束（budget constraint）下，买方如何对多个模型做组合采购（portfolio purchasing）？**

- (a) **数据出境规则是硬约束**：不合规的卖方在购买**之前**被过滤掉（filtered），而不是加罚分（never just penalized）。
  合规检查使用已有的数据驱动规则引擎（rule engine：CN PIPL/DSL、SG PDPA、BR LGPD）。
- (b) **买方预算约束**：若一笔购买的**期望成本（expected cost）**超过剩余预算，则不购买；同时记录实际支出（realised spend）。
- (c) **按任务购买模型组合**（不仅是单卖方路由）：级联（cascade）与投票（vote）。
- (d) **推理 token 长度不确定（uncertain reasoning-token length）**：按每千推理 token 计价；购买前按卖方宣称模型的平均 token 数
  计算 expected_cost，购买后按实际 token 数计算 actual_cost，记录成本超支（cost_overrun）与预算超支（budget_overrun）。
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
| cost, fee | 付给卖方 = price × tokens/1000；网关通道费 |
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

## 局限（Limitations）

- **真实 API（real APIs）只有接口**：`RealLLMBackend`（OpenAI 兼容，key 从环境变量读）未在 CI 测试，未处理限流/重试/计费对账。
- **B1 验证为桩（stubs）**：TEE 远程证明（attestation）、水印/指纹（watermark / fingerprint）、token 计数验证均未实现；
  `TrustingVerifier` 信任卖方报告，因此平台本身无法发现 seller_sg 的模型替换（只有日志中的 actual_model 可供离线研究）。
- **合规规则高度简化，不是法律意见**：未建模数据量阈值、CIIO、豁免、再转移、本地化等。
- **小模型 + CPU**：0.5B/1.5B 在 80 道简单题上的准确率与 token 分布不代表大推理模型；gen time 为 CPU 批量摊销时间；
  同一题被重复抽到时真实模型输出相同（贪心 + 缓存），故 seed 间方差主要来自市场动态与 mock 卖方。
- 置信度代理较弱（基于格式与自洽），mock 置信度为合成噪声；声誉是静态的（无在线学习）；卖方报价为随机加价，非策略性报价。
