---
title: "Markets for LLM Reasoning Tokens: A Survey of Procurement, Auditing, and Compliance"
author:
  - "TODO: Yanjie Fu, University of Macau"
bibliography: survey_refs.bib
link-citations: true
numbersections: true
abstract: |
  Large language models (LLMs) are increasingly bought rather than built. Organizations procure inference from a growing set of API providers, pay per token, and, with the rise of reasoning models, pay for long hidden chains of intermediate "reasoning tokens" that they cannot see. This creates a market with unusual properties: the good is consumed instantly, its quality is hard to verify, its quantity is reported by the seller, and its supply chain may cross jurisdictions with different data and AI rules. This survey organizes the literature that bears on such markets from the buyer's point of view. We cover (i) API pricing and token billing; (ii) routing, cascades, and model selection; (iii) auditing providers for model substitution, billing inflation, and verifiable inference; (iv) procurement and contract design under asymmetric information, sparse audits, and learning with delayed or partial feedback; (v) cross-border compliance constraints from the EU and China; and (vi) simulators and benchmarks for agentic and economic settings. We propose a taxonomy along four axes (decision problem, feedback regime, threat model, and jurisdiction), compare representative methods and benchmarks, and close with open problems at the intersection of machine learning, mechanism design, and regulation.
---

# Introduction

Most organizations that use large language models (LLMs) do not train or host them. They buy inference through application programming interfaces (APIs) from a handful of frontier labs, cloud platforms, and a long tail of resellers and open-weight hosting services. The unit of exchange is the *token*: providers meter input and output text in subword units and charge a posted price per million tokens, often with different rates for input, output, cached, and batch traffic. Over the past two years a further unit has become economically significant. *Reasoning models* produce an extended chain of intermediate text before their final answer [@wei2022cot; @openai2024o1card; @deepseek2025r1]. We call these intermediate outputs *reasoning tokens*. They are billed, usually as output tokens, but are often summarized or hidden from the buyer. Spending more of them at inference time can improve accuracy on hard problems [@snell2024scaling], but they are also spent wastefully on easy ones [@chen2024overthinking; @han2024tokenbudget].

This combination makes LLM inference an unusual good. It is an *experience good* whose quality is revealed only partially and with delay. Its quantity is reported by the seller. The seller can, in principle, substitute a cheaper model for the one advertised. And the buyer's choice of seller is constrained by law: personal data, and increasingly AI outputs themselves, are subject to rules on where they may be processed and by whom. Classical economics has a language for each ingredient (quality uncertainty [@akerlof1970lemons], hidden action [@holmstrom1979moral], costly state verification [@townsend1979csv], and deterrence through probabilistic inspection [@becker1968crime; @avenhaus2002inspection]), but the machine learning literature on LLM routing and auditing has developed largely separately from it.

This survey brings these threads together from the perspective of a buyer, or *procurer*, of reasoning tokens. We ask four questions. Which provider and model should handle a given request, at what price? How can the buyer tell whether it received what it paid for? How often should it check, given that checks are costly and their results arrive late? And which providers is it allowed to use at all? Section 2 introduces a taxonomy. Sections 3–8 survey pricing and billing, routing, provider auditing, procurement and learning theory, cross-border compliance, and simulators and benchmarks. Section 9 discusses open problems, and Section 10 concludes.

**Scope.** We focus on text LLM inference purchased through APIs. We do not survey training-data markets, compute (GPU) markets, or model licensing, except where they inform inference procurement. The legal discussion is descriptive and is not legal advice.

# A Taxonomy of Reasoning-Token Markets

We organize the literature along four dimensions. Table 1 maps representative work onto them.

*Decision problem.* What does the buyer choose? Options include (a) *routing*, which assigns each query to one of several models; (b) *cascading*, which tries models in sequence and escalates when a cheaper model's answer seems unreliable; (c) *budgeting*, which sets the number of reasoning tokens a model may spend; (d) *auditing*, which decides whether, when, and how to check a provider; and (e) *contracting*, which sets prices, penalties, and allocation rules ex ante.

*Feedback regime.* What does the buyer observe after a decision? Feedback may be *full* (the quality of every candidate is known, as in offline benchmarks), *bandit* (only the chosen option's outcome is seen), *delayed* (outcomes arrive after a lag, e.g., when a downstream task completes), *sparse* (outcomes are observed only for an audited subset of transactions), or *partial monitoring* (the observation is a noisy signal that may not directly reveal the loss).

*Threat model.* What can the seller do wrong? We distinguish *honest-but-variable* providers, whose quality drifts over time [@chen2024drift]; *model substitution*, in which a provider serves a cheaper or quantized model in place of the advertised one; *billing inflation*, in which a provider reports more tokens than it consumed, which is easiest to do with hidden reasoning tokens; and *strategic* sellers, who adapt their misbehavior to the buyer's audit policy.

*Jurisdiction.* Which legal regimes constrain the transaction? We focus on the European Union and China, and on the cross-border case in which buyer, provider, and data subject fall under different regimes.

: Taxonomy of literature relevant to reasoning-token markets. "Feedback" is the regime assumed by most work in the row.

| Area | Decision problem | Feedback | Threat model | Representative work |
|---|---|---|---|---|
| Pricing and billing | Contracting, budgeting | Full (posted prices) | Billing inflation | [@duetting2024mechanism; @velasco2025overcharging; @han2024tokenbudget] |
| Routing | Per-query model choice | Full (offline) or bandit | Honest | [@ong2025routellm; @ding2024hybrid; @shnitzer2023routing; @hu2024routerbench] |
| Cascades | Sequential escalation | Self-assessed confidence | Honest | [@chen2023frugalgpt; @yue2024cascades; @aggarwal2024automix] |
| Budgeted online routing | Routing under a spend cap | Bandit | Honest | [@panda2025pilot; @li2026stageroute; @badanidiyuru2018bwk] |
| Substitution detection | Auditing | Sampled outputs | Substitution, drift | [@gao2025equality; @cai2025substitution; @sun2025idiosyncrasies; @pasquini2025llmmap] |
| Verifiable inference | Auditing (cryptographic or hardware) | Proof per query | Substitution, incorrect computation | [@sun2024zkllm; @chen2024zkml; @tramer2019slalom; @ong2025toploc] |
| Audit economics | Audit frequency, penalties | Sparse | Strategic | [@becker1968crime; @border1987samurai; @avenhaus2002inspection; @polinsky2000enforcement] |
| Learning with limited feedback | Online selection | Delayed, sparse, partial | Mostly stochastic | [@joulani2013delayed; @vernade2017delayed; @bartok2014partial; @cesabianchi2005label] |
| Compliance | Feasible provider set | Ex ante (rules) | Legal exposure | [@eu2024aiact; @cac2023genai; @cac2024crossborder; @eu2016gdpr] |
| Simulators and benchmarks | Evaluation | Configurable | Configurable | [@hu2024routerbench; @zheng2022aieconomist; @fish2024collusion; @backlund2025vending] |

Two observations follow from Table 1. First, most of the routing literature assumes honest providers and full or bandit feedback. Second, the auditing literature typically treats a single test in isolation and says little about how often to audit or how audit outcomes should feed back into routing. The economics of inspection addresses exactly that question but has not been instantiated for LLM APIs. Much of the open territory lies between these rows.

# API Markets, Pricing, and Billing

## Token metering and price structure

Commercial LLM APIs charge per token, with separate posted prices for prompt (input) and completion (output) tokens. Output tokens typically cost more because autoregressive decoding is memory-bandwidth bound and harder to batch than prompt processing. Serving systems such as vLLM, with PagedAttention memory management, show how strongly cost per token depends on batching and memory efficiency [@kwon2023vllm]. That dependence helps explain why providers offer discounted batch, cached-prefix, and off-peak tiers. For the buyer the result is a menu of price points that varies across providers and within a single provider's catalog, and that changes frequently.

## The reasoning-token problem

Reasoning models change the economics in two ways. First, the number of output tokens per query becomes a decision variable with a large range. A model may spend a few dozen tokens or tens of thousands on the same prompt depending on its internal policy or on a user-set "effort" parameter. Test-time scaling results suggest that, for a fixed compute budget, adaptively allocating inference compute can match or exceed the gains from scaling model parameters [@snell2024scaling]. The buyer therefore faces a budgeting problem that did not exist when outputs were short. Second, providers frequently hide or summarize the raw reasoning trace [@openai2024o1card], so the buyer is billed for tokens it cannot inspect. Work on *overthinking* documents that reasoning models can spend many tokens on trivial problems [@chen2024overthinking], and token-budget prompting reduces usage at modest accuracy cost [@han2024tokenbudget]. Both suggest that a meaningful fraction of reasoning-token spend is discretionary.

## Incentives in pay-per-token contracts

Pay-per-token pricing creates a misaligned incentive when the seller controls, and reports, the quantity. Velasco et al. formalize this for tokenization. A provider that is paid per token and reports the tokenization of its output has an incentive to misreport, because the same string can be tokenized in many ways. They argue for pricing schemes that remove the incentive, such as charging per character [@velasco2025overcharging]. The same logic applies more strongly to hidden reasoning tokens, whose very existence the buyer cannot confirm. In mechanism-design terms, the buyer is purchasing a good whose quantity is privately observed by the seller, a costly-state-verification setting [@townsend1979csv] (Section 6).

A separate line of work applies mechanism design *inside* LLM generation. Duetting et al. study auctions in which several agents bid to influence a jointly generated output, token by token [@duetting2024mechanism]. That setting differs from API procurement, but it shows that token-level allocation rules can be analyzed with standard incentive-compatibility tools.

## Price competition and collusion

Because LLM API prices are posted, frequently updated, and increasingly set with algorithmic support, results on algorithmic pricing are relevant. Calvano et al. show that reinforcement-learning pricing agents can learn to sustain supra-competitive prices without explicit communication [@calvano2020collusion]. Fish et al. report analogous behavior with LLM-based pricing agents [@fish2024collusion]. Whether such dynamics arise among API providers themselves is an open empirical question. A procurement system that routes across providers is, however, also a demand-side participant in this market, and its routing rule shapes providers' pricing incentives.

# Routing, Cascades, and Model Selection

*Routing* means choosing, per query, which model or provider should answer. A *cascade* is a sequential router: a cheap model answers first, and the query escalates to a more expensive model only if a scoring function judges the cheap answer inadequate. Both aim to reach a target quality at lower cost, or higher quality at a fixed cost.

## Cascades

FrugalGPT introduced the LLM cascade as a cost-reduction strategy. It combines prompt adaptation, model approximation, and a learned scorer that decides whether to accept an answer or escalate [@chen2023frugalgpt]. Yue et al. build cascades for reasoning tasks that use agreement between answers produced with different "thought representations" (e.g., chain-of-thought versus program-of-thought) as the escalation signal, avoiding a separately trained scorer [@yue2024cascades]. AutoMix uses the smaller model's own self-verification, together with a meta-verifier that accounts for noisy self-assessment, to decide when to route to a larger model [@aggarwal2024automix]. Cascades fit naturally with reasoning budgets: the cheapest "model" in a cascade may simply be the same model with a lower reasoning-effort setting.

## Learned routers

Learned routers predict, before generation, which model will perform best or which is cheapest while still adequate. Shnitzer et al. learn routers from existing benchmark datasets by predicting per-model correctness [@shnitzer2023routing]. Hybrid LLM trains a router between a small and a large model with a tunable quality threshold [@ding2024hybrid]. RouteLLM trains routers between a strong and a weak model from human preference data, with data augmentation, and studies transfer to model pairs not seen in training [@ong2025routellm]. LLM-Blender instead ranks and fuses outputs from several models after generation. This improves quality but requires paying for all candidates [@jiang2023blender]. RouterBench provides a standardized dataset of model outputs and costs for comparing routers offline [@hu2024routerbench].

## Online and budgeted routing

Offline-trained routers assume a fixed set of models, a stationary query distribution, and labeled quality data. In deployment, providers add models, change prices, and update weights [@chen2024drift], and labels are expensive. This motivates online formulations in which routing is a contextual bandit problem [@lattimore2020bandit; @auer2002ucb]. PILOT casts routing as a contextual bandit with a budget constraint: it initializes from offline preference data and adapts online, with a separate policy for allocating spend [@panda2025pilot]. StageRoute studies the related problem of online model deployment and per-query routing under streaming workload, budget, and throughput constraints, with near-optimal regret guarantees [@li2026stageroute]. Budget constraints of this kind are the subject of the bandits-with-knapsacks literature [@badanidiyuru2018bwk], which provides regret guarantees when each action consumes a limited resource.

## What routing typically assumes

Across this literature, three assumptions are common and matter for procurement. First, providers are honest: the model named in the API call is the model that answers. Second, cost is known: the reported token count is taken as correct. Third, quality feedback is available, either offline for every model or online for the chosen one. Sections 5 and 6 survey work that relaxes each assumption in turn.

# Auditing Providers: Substitution, Billing, and Verifiable Inference

An *audit* is any procedure by which the buyer checks a provider's claims about which model ran, how many tokens it consumed, and whether the computation was performed as specified. Audits range from statistical tests on sampled outputs, which are cheap but probabilistic, to cryptographic proofs of correct execution, which are strong but expensive.

## Model substitution and identity testing

*Model substitution* occurs when a provider serves a model other than the one advertised, for example a smaller model, a quantized variant, or a different vendor's model. It may be deliberate cost-cutting or a side effect of infrastructure changes. Even without substitution, a nominally fixed API endpoint can change behavior substantially over months [@chen2024drift].

Gao et al. formalize the problem as *model equality testing*: given samples from an API and from a reference model, decide whether the two output distributions are equal. They propose a kernel two-sample test (maximum mean discrepancy) over output strings [@gao2025equality]. Cai et al. survey the threat model for substitution in LLM APIs and evaluate output-based classifiers, statistical tests, and log-probability methods. They find that simple text-level tests can miss subtle substitutions such as quantization, and they discuss hardware-based attestation as a complement [@cai2025substitution]. A related line of work shows that LLM outputs carry model-identifying regularities. Sun et al. find that classifiers can attribute text to its source model with high accuracy [@sun2025idiosyncrasies], and LLMmap fingerprints a deployed model from a small number of crafted queries [@pasquini2025llmmap]. These techniques are dual-use: they help buyers detect substitution but also help adversaries identify and target deployed models.

A complementary class of methods embeds a fingerprint or watermark in the model or its outputs. Instructional fingerprinting implants a secret input-output pair through light fine-tuning so that a model owner can later verify provenance [@xu2024instructional]. Output watermarks bias generation toward a pseudo-random subset of tokens so that text can be detected statistically [@kirchenbauer2023watermark]. Both require the cooperation of the model owner, so they protect owners against unauthorized redistribution more naturally than they protect buyers against a dishonest host. Finally, research on model extraction shows that API outputs leak more than intended. Logit access can reveal a model's hidden dimension and enable identity checks [@finlayson2024logits], and targeted queries can recover a production model's final projection layer [@carlini2024stealing]. The first result can serve the buyer, while the second is a reason providers restrict log-probability access, which in turn limits some audits.

## Billing verification

Auditing token counts is harder than auditing identity, because the buyer usually never sees hidden reasoning tokens. The incentive analysis of Velasco et al. [@velasco2025overcharging] shows that misreporting can be profitable and hard to detect even for visible outputs. For hidden reasoning, the buyer can observe only the final answer, latency, and the billed count, and must infer whether the count is plausible. Budget-aware reasoning methods [@han2024tokenbudget] and overthinking studies [@chen2024overthinking] give some empirical basis for estimating how many tokens a task should need. Turning such estimates into a test with controlled error rates is, to our knowledge, largely open. Possible approaches include statistical comparison against a self-hosted reference model, consistency checks between latency and reported length, and contractual access to the raw trace for a random subset of requests.

## Verifiable inference

*Verifiable inference* aims to give the buyer a proof that a specific model was evaluated correctly on a given input. Early work focused on small networks. SafetyNets uses interactive proofs for a restricted class of networks [@ghodsi2017safetynets], and Slalom combines a trusted execution environment with outsourcing linear layers to an untrusted GPU and verifying them cheaply [@tramer2019slalom]. Zero-knowledge machine learning (zkML) produces succinct proofs that a committed model produced a given output without revealing the weights. zkCNN targets convolutional networks [@liu2021zkcnn], ZKML provides an optimizing compiler for larger models [@chen2024zkml], and zkLLM extends zero-knowledge proofs to transformer-based LLMs with specialized protocols for attention and non-arithmetic operations [@sun2024zkllm]. Proving time and cost remain orders of magnitude above plain inference, which makes per-query proofs impractical for most commercial traffic today. Lighter-weight schemes trade cryptographic soundness for efficiency. TOPLOC, for example, commits to locality-sensitive hashes of intermediate activations, which a verifier can check by recomputation [@ong2025toploc]. Related "proof-of-work" ideas in training, such as proof-of-learning [@jia2021pol], illustrate both the appeal and the subtle attack surface of such certificates.

## From tests to policies

The common thread is that each audit has a cost and an error profile, and most papers evaluate a single audit in isolation. In a market, the buyer instead chooses an *audit policy*: which transactions to audit, with which method, and how to respond to a failure (e.g., withhold payment, down-weight the provider in routing, or exclude it). A *sparse audit* policy checks only a small random fraction of transactions and relies on deterrence for the rest. Designing such policies is an economic problem, which we turn to next.

# Procurement, Sparse Audits, and Learning Under Delayed Feedback

## Asymmetric information and procurement

Procurement of reasoning tokens combines adverse selection and moral hazard. Before contracting, the buyer does not know a provider's true model quality or cost (*hidden information*). After contracting, it cannot observe whether the provider ran the promised model or reported tokens honestly (*hidden action*). Akerlof showed that quality uncertainty can unravel markets [@akerlof1970lemons]. Holmström characterized optimal contracts when actions are unobservable but informative signals exist [@holmstrom1979moral]. Myerson's optimal auction design gives the revenue-maximizing allocation and payment rules when bidders hold private values [@myerson1981optimal], and Laffont and Tirole develop the theory of regulated procurement with private cost information [@laffont1993procurement]. Applied to LLM APIs, these frameworks suggest that posted per-token prices with no verification invite quality shading, and that the buyer's ability to verify, even occasionally, is central to contract design.

## Costly verification and audits

When verifying the seller's report is costly, the buyer must decide when to verify. Townsend's costly-state-verification model shows that optimal contracts verify only in some states, with payments structured to make truthful reporting incentive compatible [@townsend1979csv]. Border and Sobel extend this to random auditing, showing that randomized audits can reduce expected audit costs while preserving truthful reporting [@border1987samurai]. These models fit token billing directly. The seller reports a token count, the buyer can pay to verify it (e.g., by rerunning the query on a reference model), and penalties for misreporting discipline the seller.

## Deterrence and inspection games

Becker's economic model of crime holds that deterrence depends on the product of detection probability and penalty, so rare inspections with high penalties can be efficient [@becker1968crime]. Polinsky and Shavell survey the resulting public-enforcement literature, including limits on penalties and the costs of errors [@polinsky2000enforcement]. *Inspection games* model the strategic interaction between an inspector and an inspectee who may violate an agreement, with applications from arms control to accounting. Equilibria typically involve mixed strategies on both sides [@avenhaus2002inspection]. When the inspector can commit to an audit policy in advance, the problem becomes a Stackelberg game, and optimal commitment strategies can be computed efficiently in many settings [@conitzer2006commit].

These results translate directly to LLM procurement. The buyer chooses an audit rate and a penalty, such as payment clawback or exclusion from routing. A strategic provider chooses a substitution or inflation rate. Deterrence works only if the expected penalty exceeds the gain from cheating. Three features of the LLM setting complicate the classical analysis. First, audits are *imperfect*, with false positives and negatives that depend on the test (Section 5). Second, the penalty a buyer can impose is often bounded by the value of future business, which links audit design to routing. Third, the provider may adapt its cheating to the query distribution, cheating more on queries it expects to go unaudited.

## Learning with sparse and delayed feedback

Routing and auditing are both sequential decisions under uncertainty, so online learning theory applies. Standard stochastic bandits balance exploration and exploitation when only the chosen arm's reward is observed [@auer2002ucb; @lattimore2020bandit]. Three refinements match the procurement setting:

- *Delayed feedback.* Task outcomes (e.g., whether a generated proof checks or code passes integration tests) arrive after a lag. Joulani et al. give black-box reductions showing how delay increases regret in online learning [@joulani2013delayed]. Vernade et al. model delayed, possibly censored conversions in bandits [@vernade2017delayed]. Pike-Burke et al. handle feedback that is both delayed and aggregated anonymously across rounds [@pikeburke2018aggregated], much like a monthly invoice that reports totals but not per-request costs.
- *Sparse or label-efficient feedback.* If quality or honesty is observed only for audited transactions, the learner must decide when to pay for a label. Label-efficient prediction studies exactly this trade-off, with regret depending on the number of queried labels [@cesabianchi2005label].
- *Partial monitoring.* More generally, the buyer's observation (e.g., a noisy audit signal) may not directly reveal its loss. Partial monitoring characterizes when learning is possible and at what rate [@bartok2014partial].

Budget constraints, as in bandits with knapsacks [@badanidiyuru2018bwk], add a further layer when audit and inference spending share a single budget. To our knowledge, no existing analysis combines strategic sellers, imperfect audits, delayed rewards, and budget constraints in one model. Each ingredient is well studied on its own.

# Cross-Border Compliance Constraints

Legal constraints restrict which providers a buyer may route to and which data it may send them. For procurement, regulation acts mainly as a *feasibility constraint* on the routing problem, and secondarily as a source of audit obligations.

## European Union

The General Data Protection Regulation (GDPR) restricts transfers of personal data outside the European Economic Area unless an adequacy decision, appropriate safeguards (such as standard contractual clauses), or a specific derogation applies [@eu2016gdpr]. The Court of Justice's *Schrems II* judgment invalidated the earlier EU–US Privacy Shield and required case-by-case assessment of destination-country law when relying on contractual clauses [@cjeu2020schrems]. The Commission subsequently adopted an adequacy decision for the EU–US Data Privacy Framework, covering certified US organizations [@eu2023dpf]. A buyer routing prompts that contain personal data to a provider abroad must therefore track, per provider, the legal basis for the transfer.

The EU AI Act (Regulation (EU) 2024/1689) adds obligations specific to AI systems [@eu2024aiact]. It classifies systems by risk, imposes requirements on high-risk systems and their deployers, and introduces obligations for providers of general-purpose AI models, including technical documentation and information that downstream providers need. For procurement, two aspects matter. First, a deployer that builds a high-risk system on purchased inference inherits documentation and oversight duties, which depend on information from upstream providers. Second, a provider silently substituting one model for another could undermine the documentation on which the deployer relies. Legal scholarship has analyzed the Act's structure and its treatment of general-purpose and generative models [@veale2021demystifying; @hacker2023regulating].

## China

China's Interim Measures for the Management of Generative Artificial Intelligence Services, effective in August 2023, regulate generative AI services offered to the public in China. They address training-data legality, content requirements, labeling, and, for services with public-opinion attributes, security assessment and algorithm filing [@cac2023genai]. Cross-border data movement is governed by the Personal Information Protection Law [@npc2021pipl] and the Data Security Law [@npc2021dsl], implemented through the Measures for the Security Assessment of Outbound Data Transfers [@cac2022assessment]. The 2024 Provisions on Promoting and Regulating Cross-Border Data Flows relaxed several thresholds and introduced exemptions [@cac2024crossborder]. Overviews of China's AI governance situate these instruments within a broader policy agenda [@roberts2021chinese]. For a buyer, the practical consequence is that the set of permissible providers depends on where the service is offered, what data the prompt contains, and the data volume. These conditions vary per request, so compliance cannot be treated as a one-time vendor-selection step.

## Implications for procurement

Three implications recur across regimes. First, compliance makes the feasible provider set *query-dependent*: a prompt containing personal or "important" data may be routable only to providers in certain locations. Routing algorithms that assume a fixed action set must therefore be extended with per-query constraints. Second, compliance creates *documentation obligations* that depend on provider honesty. Model substitution is not only an economic harm but can also be a compliance failure, which raises the effective penalty for undetected cheating and so changes the audit calculus of Section 6. Third, regulation changes over time, and the cross-border rules discussed here have themselves been revised within a few years. Procurement systems must therefore treat legal constraints as versioned, auditable configuration rather than fixed assumptions.

# Simulators and Benchmarks

Empirical work on reasoning-token markets requires environments in which routing, pricing, and auditing policies can be compared reproducibly. Existing resources fall into three groups (Table 2).

*Routing benchmarks.* RouterBench supplies precomputed outputs and costs for many models across standard tasks, so routers can be evaluated without repeated API calls [@hu2024routerbench]. Router evaluations in RouteLLM and related work similarly rely on fixed preference or correctness datasets [@ong2025routellm; @shnitzer2023routing]. These benchmarks treat providers as honest and prices as static.

*Economic and multi-agent simulators.* Agent-based market simulators predate LLMs. ABIDES simulates exchange microstructure with many interacting agents [@byrd2020abides], and the AI Economist uses multi-agent reinforcement learning to study tax policy in a simulated economy [@zheng2022aieconomist]. More recently, LLMs have been used *as* simulated economic agents [@horton2023homosilicus; @park2023generative; @li2024econagent], and LLM-based pricing agents have been studied for collusive tendencies [@fish2024collusion]. Game-theoretic benchmarks evaluate LLMs' strategic reasoning [@duan2024gtbench].

*Agentic benchmarks.* AgentBench, WebArena, and $\tau$-bench evaluate LLM agents on multi-step tasks in interactive environments [@liu2024agentbench; @zhou2024webarena; @yao2024taubench]. Vending-Bench tests long-horizon coherence in a simulated small-business setting with economic outcomes [@backlund2025vending]. These resources treat the LLM as the agent rather than as a procured good, but they supply realistic task distributions and delayed outcome signals.

*Emerging direction.* Newer, not-yet-published efforts aim to combine these elements in a single environment. One example is a cross-border reasoning-token market benchmark that provides a market simulator, a shared data schema for logging transactions, audits, and compliance attributes, and a task framing for studying procurement, routing, and auditing under compliance constraints and sparse audit feedback. Such environments are at an early stage, and no common evaluation protocol has yet emerged.

: Comparison of representative methods, systems, and benchmarks.

| Work | Inputs | Key assumptions | Outputs | Main limitations for procurement |
|---|---|---|---|---|
| FrugalGPT [@chen2023frugalgpt] | Query; ordered list of APIs; scorer training data | Honest providers; known costs | Cascade policy | No adversarial providers; offline-trained scorer |
| RouteLLM [@ong2025routellm] | Query; strong/weak model pair; preference data | Stationary models; honest billing | Binary routing decision with threshold | Two-model setting; no compliance constraints |
| PILOT [@panda2025pilot] | Query embedding; model pool; budget | Bandit feedback available per query | Online routing and budget allocation | Assumes immediate, truthful feedback |
| RouterBench [@hu2024routerbench] | Cached outputs and costs for many models | Static prices; honest providers | Offline router evaluation | No delays, audits, or strategic sellers |
| Model equality testing [@gao2025equality] | Samples from API and reference model | Reference model accessible | Hypothesis test of distributional equality | Sample cost; no audit-frequency policy |
| Substitution audit study [@cai2025substitution] | API outputs, log-probabilities, benchmarks | Various adversary strengths | Detection rates per method | Quantization hard to detect; per-test, not per-policy |
| zkLLM [@sun2024zkllm] | Committed weights; input | Cryptographic hardness assumptions | Proof of correct inference | Proving cost far exceeds inference |
| TOPLOC [@ong2025toploc] | Activation hashes; verifier recomputation | Verifier can rerun the model | Probabilistic validity check | Needs open weights; not zero-knowledge |
| Inspection games [@avenhaus2002inspection] | Payoffs; detection probabilities | Rational players; known payoffs | Equilibrium inspection strategy | Not instantiated for LLM APIs |
| AI Economist [@zheng2022aieconomist] | Simulated agents and policy levers | Stylized economy | Learned policies and welfare metrics | Not about inference procurement |
| Cross-border reasoning-token market benchmark (emerging, unpublished) | Simulated sellers, buyers, and audit/compliance settings | Simulated market | Logged transactions in a shared schema; task framing | Early stage; no public archival version |

# Open Problems and Outlook

**Joint routing and auditing.** Routing and auditing share one budget and one stream of evidence. An audit outcome is a quality label for the router, and a routing decision changes which providers are exposed to audits. We know of no framework that optimizes both jointly with guarantees under strategic sellers. Combining Stackelberg commitment [@conitzer2006commit], budgeted bandits [@badanidiyuru2018bwk], and partial monitoring [@bartok2014partial] is a natural starting point.

**Billing verification for hidden reasoning.** No standard test exists for whether a reported reasoning-token count is plausible. Useful directions include calibrated per-task token-length models [@han2024tokenbudget], contractual spot disclosure of raw traces, and pricing schemes that remove the incentive to inflate [@velasco2025overcharging].

**Cheap, sound verification.** Cryptographic verifiable inference [@sun2024zkllm; @chen2024zkml] is sound but expensive. Statistical tests [@gao2025equality] are cheap but probabilistic, and hashing-based schemes [@ong2025toploc] sit in between. A theory of *mixed* audit portfolios, which would use cheap tests often and strong proofs rarely, would connect verification research to the random-audit results of Border and Sobel [@border1987samurai].

**Strategic adaptation.** Providers that learn the buyer's audit policy can concentrate cheating on unaudited traffic. Robustness to adaptive adversaries, which is well studied in security games, has not been examined for LLM substitution. The dual-use nature of fingerprinting [@pasquini2025llmmap] means providers can also detect audit queries.

**Delayed and aggregated feedback at scale.** Real outcomes arrive late and in aggregate, as invoices, downstream task metrics, and user complaints. Methods for delayed, anonymous feedback [@pikeburke2018aggregated; @vernade2017delayed] have not been evaluated on LLM procurement workloads.

**Compliance as a first-class constraint.** Query-dependent feasibility sets, versioned legal rules, and documentation obligations [@eu2024aiact; @cac2024crossborder] are rarely modeled in routing research. Formalizing them, and measuring the cost of compliance in routing performance, would make the literature more useful to practitioners.

**Shared benchmarks and data.** Progress on all of the above depends on reproducible environments with honest and dishonest sellers, configurable audit technologies and feedback delays, and explicit compliance attributes. Existing routing benchmarks [@hu2024routerbench] and economic simulators [@zheng2022aieconomist] each cover part of this space. Agreement on common schemas and task definitions would make results comparable.

**Positioning.** This survey argues that reasoning-token procurement is best understood as a mechanism-design problem with learning and legal constraints, not as a pure prediction problem. The emerging benchmark direction described in Section 8 is one attempt to make this framing operational. Its value will depend on community adoption and independent evaluation, not on any single study.

# Conclusion

Buying LLM inference, especially reasoning-heavy inference, means buying a good whose quality is uncertain, whose quantity is reported by the seller, and whose permissible sources depend on law. The routing literature has made substantial progress on cost-quality trade-offs under honest-provider assumptions. The auditing literature has produced statistical and cryptographic tools for checking provider claims. Economics offers mature theory for verification, deterrence, and procurement under asymmetric information. Learning theory handles delayed, sparse, and partial feedback. Regulation in the EU and China increasingly constrains where inference can run. These communities have so far worked largely in isolation. We hope the taxonomy and comparisons offered here help connect them, and that shared environments make it possible to study procurement, auditing, and compliance together.

# References {-}

::: {#refs}
:::
