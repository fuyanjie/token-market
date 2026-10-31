# token-market v1：跨境推理 Token 交易迷你沙盒（Research Sandbox）

一个**纯虚拟**的跨境推理 token 交易平台（cross-border reasoning-token marketplace）研究沙盒：
CN / SG / BR 三个司法辖区（jurisdiction）的买方（buyers）向卖方（sellers）购买"推理 token"来解答可校验答案的推理题，
平台比较不同撮合机制（matching mechanism）与路由策略（routing policy），并通过跨境网关（cross-border gateway）
执行简化的数据出境合规规则（compliance rules）。

> ⚠️ **免责声明（Disclaimer）**：合规规则仅为**简化模拟（simplified simulation）**，条款编号只作标签使用，
> **不构成法律意见（NOT legal advice）**。所有价格、模型、延迟均为合成数据（synthetic data）。默认不调用任何真实 API，不需要任何 API key。

依赖：Python 3、`pyyaml`、`pytest`（numpy 不需要）。仅 CPU。

## 快速开始（How to run）

```bash
pip install pyyaml pytest
python run_sim.py --config configs/default.yaml                  # 默认: 3 seeds × 6 组合, mock 后端, < 1 秒
python run_sim.py --config configs/default.yaml --seeds 0 1 2 --n-tasks 500
python run_sim.py --config configs/default.yaml --auction-format first_price
python run_sim.py --config configs/default.yaml --backend local_hf --n-tasks 20 --seeds 0   # 需 transformers + torch, 较慢
python -m pytest -q
```

输出（outputs）：
- `results/transactions.jsonl`：统一交易日志（unified transaction log），每笔交易一行（含被拦截的）。
- `results/summary.json`：每个 机制×策略 组合的逐 seed 指标与均值/标准差（mean/std）。
- `results/summary.md`：对比表（markdown table），mean ± std over seeds。

## 模块（Modules）

| 文件 | 作用 |
|---|---|
| `tokenmarket/sellers.py` | 卖方（Seller）：辖区、声明模型（claimed_model）与实际模型（actual_model）、每千 token 价格（price_per_1k）、成本、延迟分布（latency mean/std）、每轮容量（capacity per round）、质量画像（quality_profile）、法律机制标记（flags） |
| `tokenmarket/buyers.py` | 买方（Buyer）：辖区、预算（budget）、允许辖区（allowed_jurisdictions）、每个正确答案价值（value_per_correct）、敏感度分布（sensitivity_mix）、同意率（consent_rate） |
| `tokenmarket/tasks.py` | 任务流（task stream）：多步算术、应用题（word problem）、数列（sequence）、逻辑题，难度 1–3，整数标准答案（gold）；每个任务带数据敏感度标签（public / personal / sensitive_personal / important_data） |
| `tokenmarket/backends.py` | 推理后端：`MockLLM`（默认）、`LocalHFBackend`（Qwen/Qwen2.5-0.5B-Instruct，懒加载 transformers）、`RealLLMBackend`（OpenAI 兼容接口，urllib，默认不用） |
| `tokenmarket/matching.py` | 撮合机制：固定挂牌价（posted price）+ 路由策略；密封报价拍卖（sealed-bid auction，二价 second-price / 一价 first-price） |
| `tokenmarket/compliance.py` | 数据驱动的合规规则引擎（rule engine），每条规则有 `rule_id` |
| `tokenmarket/gateway.py` | 跨境网关：执行合规、加跨境延迟惩罚（latency penalty）与通道费/关税（fee/tariff per corridor）、统计放行/拦截流量 |
| `tokenmarket/verification.py` | 验证与结算接口（VerificationModule ABC）：`verify_model_identity` / `verify_token_count` / `settle`；TEE 远程证明（attestation）与水印（watermark）为桩（stub） |
| `tokenmarket/logging_schema.py` | 交易日志 schema 定义与校验（validate_record） |
| `tokenmarket/metrics.py` | 指标计算与跨 seed 聚合 |
| `tokenmarket/sim.py` | 仿真主循环，跑全部 机制 × 策略 × seeds |
| `run_sim.py` | 命令行入口（CLI） |

### 卖方（默认 3 个）

| id | 辖区 | claimed_model | actual_model | 价格/1K | 成本/1K | 延迟 (ms) | 容量/轮 | flags |
|---|---|---|---|---|---|---|---|---|
| seller_cn | CN | sim-strong-r1 | sim-strong-r1 | 0.020 | 0.012 | 900±250 | 12 | br_scc |
| **seller_sg** | SG | **sim-strong-r1** | **sim-weak-r1** | 0.011 | 0.004 | 600±150 | 12 | cn_standard_contract, br_scc |
| seller_br | BR | sim-mid-r1 | sim-mid-r1 | 0.010 | 0.006 | 1100±300 | 12 | sg_contractual_safeguards |

`seller_sg` 实施**模型替换欺诈（model-swap fraud）**：宣称强模型，实际提供弱模型（准确率更低、推理 token 更少）。
买方只能看到宣称质量（advertised quality），因此 quality_per_cost 等策略会被误导。每笔交易同时记录 `claimed_model` 与 `actual_model`，供后续检测研究。

### 撮合机制与路由策略（Mechanisms × Policies）

- **posted_price**（固定挂牌价）：买方按挂牌价选卖方。
  - `cheapest`：最低价；
  - `quality_per_cost`：最大化 宣称准确率/价格；
  - `compliance_aware`：先用网关预检过滤掉会被拦截的卖方，再按 quality_per_cost 选。
- **sealed_bid**（密封报价反向拍卖, procurement auction）：卖方报价 = 成本 × U(1.1, 1.8) 随机加价（markup）。
  评分 score = bid / quality（`cheapest` 时 quality=1，即纯价格拍卖）。
  `second_price`（默认）：赢家获得使其评分与第二名持平的价格（= 第二名评分 × 赢家 quality），以保留价（reserve price）封顶；只有一个投标人时付保留价。`first_price`：按自身报价成交。
  同样的三种策略决定评分方式与是否预先过滤不合规卖方。
- 所有策略都先按买方 `allowed_jurisdictions` 与卖方剩余容量过滤。非 compliance_aware 策略选中的卖方若违规，会在网关被**拦截（blocked）**，该任务不再回退（no fallback），以凸显合规感知路由的价值。

## 合规规则表（Compliance rule table — 简化模拟，非法律意见）

规则写在 `configs/default.yaml` 的 `compliance.rules` 中，按顺序评估，仅作用于跨境流（买方辖区 ≠ 卖方辖区）。
`allow` 类型命中即放行；`require` 类型需满足任一 `allow_if` 条件，否则以该 `rule_id` 拦截；没有命中任何规则则放行。

| rule_id | 来源辖区 | 敏感度 | 放行条件（allow_if） | 含义（简化） |
|---|---|---|---|---|
| GEN-PUBLIC | ANY | public | 无条件放行 | 公开数据可流向任何辖区 |
| CN-DSL-31 | CN | important_data | 卖方有 `cn_security_assessment` | 重要数据（important data）出境须安全评估；默认无卖方具备 → 拦截 |
| CN-PIPL-40 | CN | sensitive_personal | 卖方有 `cn_security_assessment` | 敏感个人信息出境须安全评估（简化）→ 默认拦截 |
| CN-PIPL-38 | CN | personal | 卖方有 `cn_security_assessment` / `cn_standard_contract` / `cn_certification` 之一 | 个人信息出境须合法机制（安全评估/标准合同/认证） |
| SG-PDPA-26 | SG | personal, sensitive_personal | 目的地在 SG 充分性名单（adequacy list, 默认 `[BR]`，虚构）或卖方有 `sg_contractual_safeguards` | 转移限制义务（transfer limitation obligation） |
| BR-LGPD-33-VIII | BR | sensitive_personal | 任务带 `specific_consent` | 敏感个人数据跨境须数据主体特定同意（specific consent） |
| BR-LGPD-33 | BR | personal, sensitive_personal | 目的地充分（默认名单为空）或卖方有 `br_scc`（标准合同条款, SCC）或任务带 `specific_consent` | 国际传输限于充分性国家/SCC/特定同意 |

充分性名单（adequacy lists）为**假设值**，仅用于仿真，可在配置里修改。

### 跨境网关（Gateway）

每个通道（corridor，如 `CN->SG`）配置延迟惩罚（latency_penalty_ms）与费率（fee_rate，按成交额比例，由买方支付）；国内交易为 0。
网关统计每个通道的放行/拦截次数；此外仿真对每笔放行交易做独立复核（post-hoc audit），"违规放行数（violating flows through）"应恒为 0。

## 交易日志 Schema（Transaction log schema）

每笔交易（含 blocked / unfilled）恰好写一行 JSONL，字段定义见 `tokenmarket/logging_schema.py`，写入前强制校验。

| 字段 | 类型 | 说明 |
|---|---|---|
| ts / round | float / int | 墙钟时间戳 / 仿真轮次 |
| run_id, mechanism, policy, seed | str/str/str/int | 运行标识 `机制__策略__seedN` |
| buyer_id, buyer_jurisdiction | str | 买方 |
| task_id, task_type, difficulty, sensitivity | str/str/int/str | 任务 |
| seller_id, seller_jurisdiction | str \| null | 选中的卖方（unfilled 时为 null） |
| claimed_model, actual_model | str \| null | 声明模型 / 实际模型（欺诈研究用） |
| cross_border | bool | 是否跨境 |
| price_per_1k | float | 成交价（每千推理 token） |
| reasoning_tokens | int | 推理 token 数（未服务时为 0） |
| cost | float | 买方支付给卖方 = price_per_1k × tokens / 1000 |
| fee | float | 网关通道费 |
| latency_ms | float | 卖方延迟 + 跨境惩罚 |
| answer, gold, correct | int\|null, int, bool\|null | 回答 / 标准答案 / 是否正确 |
| status | str | `allowed`（放行）/ `blocked`（合规拦截）/ `unfilled`（市场原因未成交） |
| rule_id | str \| null | blocked 时为合规规则 ID；unfilled 时为 `MKT-*` 原因（如 `MKT-NO-CAPACITY`, `MKT-BUDGET-EXHAUSTED`, `MKT-NO-COMPLIANT-SELLER`）；allowed 时为 null |
| buyer_surplus | float | value_per_correct × correct − cost − fee |
| seller_profit | float | 收入 − 实际模型服务成本 |
| verification_status | str | v1 恒为 `unverified` |

> 说明：需求中 status 为 allowed/blocked 二值；v1 增加了 `unfilled`，用来区分"因容量/预算/无合规卖方而未成交"与"被合规规则拦截"，避免把市场摩擦误计为合规拦截。

## 指标（Metrics, `results/summary.md`）

准确率（accuracy, 仅放行交易）、总成本（total cost）、通道费、平均/P95 延迟、合规违规（compliance violations = 拦截次数 + 违规放行数）、
各买方剩余（buyer surplus）与各卖方利润（seller profit）、跨境占比（cross-border share）、
欺诈暴露（fraud exposure：由替换模型服务的放行交易占比）、欺诈准确率差（fraud accuracy gap：声明模型的期望准确率 − 实际准确率）、
按规则统计的拦截次数。

## 后端（Backends）

- `MockLLM`（默认）：P(正确) = 实际模型在该难度的准确率；token 数 ~ N(模型均值 × 难度系数, std)；错误答案为扰动后的 gold。
- `LocalHFBackend`（`--backend local_hf`）：CPU 上运行 Qwen/Qwen2.5-0.5B-Instruct，懒加载 `transformers`（需自行 `pip install transformers torch`）；
  所有模拟模型共用同一权重，"弱模型"通过更小的 `hf_max_new_tokens` 体现；从输出解析最后一个数字（`Answer: N`）。
- `RealLLMBackend`（`--backend real`）：OpenAI 兼容 `/chat/completions`，`base_url` 与 `model_map` 在配置中，API key 从环境变量读取
  （如 `DASHSCOPE_API_KEY` 或 `DEEPSEEK_API_KEY`）。**默认不使用，仓库中不含任何 key。**

## 局限与 TODO（Limitations / TODO）

- **B1 验证（verification）**：`verification.py` 仅为接口桩。TODO：TEE 远程证明（TEE attestation，绑定模型哈希）、
  输出水印/指纹检测（watermark / fingerprint）、统计探测（probing）、推理 token 计数验证（token-count verification）、基于验证结果的结算/罚没（slashing）。
  当前 `TrustingVerifier` 信任卖方报告，因此无法发现模型替换欺诈。
- **真实 API（real APIs）**：RealLLMBackend 未在 CI 中测试；未处理限流、重试、计费对账。
- 合规规则高度简化：未建模数据量阈值、CIIO 身份、豁免情形、再转移（onward transfer）、数据本地化等。
- 买方路由策略是静态的，没有学习/声誉系统（reputation）；卖方报价为随机加价，没有策略性报价（strategic bidding）。
- 延迟与 token 数分布为合成值；未建模排队与拥塞。
