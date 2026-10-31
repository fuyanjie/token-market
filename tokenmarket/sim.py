"""Simulation driver (v2): precompute real local model outputs, then run every policy x mechanism over seeds
and write the unified transaction log + summaries."""
from __future__ import annotations

import copy
import json
import os
import random
import time
from typing import Dict, List, Optional

from .backends import CachedLocalBackend, MockLLM, make_backend
from .buyers import load_buyers
from .cache import OutputCache
from .compliance import ComplianceEngine, DISCLAIMER
from .gateway import CrossBorderGateway
from .logging_schema import TransactionLogger
from .matching import candidate_sellers, sealed_bid_select
from .metrics import aggregate, run_metrics
from .portfolio import SINGLE_POLICIES, Purchase, is_hard, run_policy
from .precompute import local_cfg, local_models, model_stats, precompute, render_model_accuracy_md
from .sellers import Reputation, load_sellers
from .tasks import build_task_pool, sample_run_tasks
from .verification import TrustingVerifier


def _base_record(run_id, mechanism, policy, seed, rnd, buyer, task) -> Dict:
    return {"ts": time.time(), "round": rnd, "run_id": run_id, "mechanism": mechanism, "policy": policy,
            "seed": seed, "buyer_id": buyer.id, "buyer_jurisdiction": buyer.jurisdiction,
            "task_id": task.task_id, "pool_task_id": task.task_id.split("_", 1)[-1], "portfolio_step": 0,
            "task_type": task.task_type, "difficulty": task.difficulty, "sensitivity": task.sensitivity,
            "seller_id": None, "seller_jurisdiction": None, "claimed_model": None, "actual_model": None,
            "backend": None, "cross_border": False, "price_per_1k": 0.0, "reasoning_tokens": 0,
            "cost": 0.0, "fee": 0.0, "expected_cost": 0.0, "actual_cost": 0.0, "cost_overrun": 0.0,
            "budget_remaining": buyer.remaining, "budget_overrun": buyer.spent > buyer.budget + 1e-12,
            "latency_ms": 0.0, "answer": None, "gold": task.gold, "correct": None, "confidence": None,
            "status": "unfilled", "violation": False, "rule_id": None, "final": False, "final_answer": None,
            "final_correct": None, "buyer_surplus": 0.0, "seller_profit": 0.0,
            "verification_status": "unverified"}


def run_single(cfg: Dict, mechanism: str, policy: str, seed: int, backends: Dict, rep: Reputation,
               logger: TransactionLogger, pool, n_tasks: Optional[int] = None,
               backend_override: Optional[str] = None) -> Dict:
    run_cfg, mcfg = cfg["run"], cfg["market"]
    n_tasks = int(n_tasks or run_cfg["n_tasks"])
    n_rounds = max(1, int(run_cfg.get("n_rounds", 1)))
    sellers, buyers = load_sellers(cfg, backend_override), load_buyers(cfg)
    buyer_by_id = {b.id: b for b in buyers}
    engine = ComplianceEngine.from_config(cfg)
    hard = is_hard(policy)
    gw_mode = "enforce" if hard else mcfg.get("unaware_gateway_mode", "audit_only")
    gateway = CrossBorderGateway(engine, cfg, mode=gw_mode)
    verifier = TrustingVerifier()
    models = cfg["models"]
    auction_cfg = mcfg["auction"]
    lat_scale = float(local_cfg(cfg).get("latency_scale", 1.0))
    run_id = f"{mechanism}__{policy}__seed{seed}"
    rng_backend = random.Random(f"backend-{seed}")
    rng_market = random.Random(f"market-{seed}")
    rng_latency = random.Random(f"latency-{seed}")

    tasks = sample_run_tasks(pool, buyers, n_tasks, seed)
    per_round = -(-n_tasks // n_rounds)
    records: List[Dict] = []
    filtered_total, filtered_by_rule, audit_violations = 0, {}, 0
    stop_reasons: Dict[str, int] = {}

    for i, task in enumerate(tasks):
        rnd = i // per_round
        if i % per_round == 0:
            for s in sellers:
                s.reset_round()
        buyer = buyer_by_id[task.buyer_id]
        base = _base_record(run_id, mechanism, policy, seed, rnd, buyer, task)
        lines: List[Dict] = []

        def fee_rate(s):
            return gateway.corridor_params(buyer.jurisdiction, s.jurisdiction)[1]

        def quality(s):
            return rep.accuracy(s.claimed_model, task.difficulty)

        cands = candidate_sellers(buyer, sellers, task, hard, gateway.would_allow)
        filtered_total += cands.filtered
        for k, v in cands.filtered_by_rule.items():
            filtered_by_rule[k] = filtered_by_rule.get(k, 0) + v
        prices = {s.id: s.price_per_1k for s in cands.sellers}
        reason = cands.reason
        if not reason and mechanism == "sealed_bid":
            if policy not in SINGLE_POLICIES:
                raise ValueError(f"sealed_bid supports only single-seller policies, not {policy}")
            sel = sealed_bid_select(cands.sellers, quality if policy == "single_best_compliant" else (lambda s: 1.0),
                                    rng_market, auction_cfg)
            if sel is None:
                reason = "MKT-NO-BID-BELOW-RESERVE"
            else:
                cands.sellers, prices = [sel[0]], {sel[0].id: sel[1]}
        elif mechanism not in ("posted_price", "sealed_bid"):
            raise ValueError(f"unknown mechanism {mechanism}")

        def exp_cost(s, price=None):
            p = prices[s.id] if price is None else price
            return p * rep.tokens_mean(s.claimed_model) / 1000.0 * (1 + fee_rate(s))

        def buy(s, price, step):
            nonlocal audit_violations
            expected = exp_cost(s, price)
            if buyer.remaining < expected:          # hard budget constraint on EXPECTED cost
                return None
            rec = dict(base, portfolio_step=step, seller_id=s.id, seller_jurisdiction=s.jurisdiction,
                       claimed_model=s.claimed_model, actual_model=s.actual_model, backend=s.backend,
                       cross_border=s.jurisdiction != buyer.jurisdiction, price_per_1k=price,
                       expected_cost=expected, ts=time.time())
            gw = gateway.route(buyer, s, task)
            if not gw.allowed:
                rec.update(status="blocked", rule_id=gw.rule_id, budget_remaining=buyer.remaining,
                           budget_overrun=buyer.spent > buyer.budget + 1e-12)
                lines.append(rec)
                return Purchase(s, None, None, quality(s), served=False)
            s.used_this_round += 1
            res = backends[s.backend].solve(task, s.actual_model, models[s.actual_model], s.reasoning_effort,
                                            rng_backend)
            tx = dict(rec, reasoning_tokens=res.reasoning_tokens, fee_rate=gw.fee_rate)
            st = verifier.settle(tx)
            actual = st.buyer_pays + st.fee
            buyer.spent += actual
            correct = res.answer is not None and int(res.answer) == task.gold
            if res.gen_time_s is not None:   # real model: measured gen time + jurisdiction overhead/noise
                lat = s.latency_mean_ms + res.gen_time_s * 1000.0 * lat_scale + rng_latency.gauss(0, s.latency_std_ms)
            else:
                lat = s.sample_latency(rng_latency)
            # independent post-hoc audit of every flow that went through
            violation = not engine.evaluate_flow(buyer, s, task).allowed
            audit_violations += int(violation and gw_mode == "enforce")
            rec.update(reasoning_tokens=int(res.reasoning_tokens), cost=st.buyer_pays, fee=st.fee,
                       actual_cost=actual, cost_overrun=actual - expected, budget_remaining=buyer.remaining,
                       budget_overrun=buyer.spent > buyer.budget + 1e-12,
                       latency_ms=max(50.0, lat) + gw.latency_penalty_ms,
                       answer=None if res.answer is None else int(res.answer), correct=bool(correct),
                       confidence=None if res.confidence is None else round(float(res.confidence), 4),
                       status="allowed", violation=violation, rule_id=gw.rule_id if violation else None,
                       buyer_surplus=-actual,
                       seller_profit=st.seller_receives - s.cost_per_1k * res.reasoning_tokens / 1000.0,
                       verification_status=verifier.verify_model_identity(tx))
            lines.append(rec)
            return Purchase(s, rec["answer"], res.confidence, quality(s))

        if reason:
            dec = None
        else:
            dec = run_policy(policy, cands.sellers, lambda s: prices[s.id], exp_cost, quality, buy, mcfg)
            if policy.startswith(("cascade", "vote")):
                stop_reasons[dec.stop_reason] = stop_reasons.get(dec.stop_reason, 0) + 1
            if not lines:
                reason = "MKT-BUDGET-EXHAUSTED"
        if not lines:   # no purchase attempted: one unfilled line
            lines.append(dict(base, rule_id=reason, budget_remaining=buyer.remaining,
                              budget_overrun=buyer.spent > buyer.budget + 1e-12))
        final_answer = dec.final_answer if dec else None
        last = lines[-1]
        last.update(final=True, final_answer=final_answer,
                    final_correct=final_answer is not None and final_answer == task.gold)
        last["buyer_surplus"] += buyer.value_per_correct * last["final_correct"]
        for rec in lines:
            logger.write(rec)
        records.extend(lines)

    m = run_metrics(records, buyers, [s.id for s in sellers], rep, policy)
    m.update(filtered_candidates=filtered_total, filtered_by_rule=filtered_by_rule,
             blocked_or_filtered=filtered_total + m["blocked_at_gateway"],
             audit_violations_enforced=audit_violations, stop_reasons=stop_reasons)
    m["gateway"] = gateway.stats()
    return m


def build_backends(cfg: Dict, sellers_cfg_backends, cache: Optional[OutputCache]) -> Dict:
    out = {"mock": MockLLM(cfg["market"].get("mock_confidence"))}
    if "local_hf" in sellers_cfg_backends:
        out["local_hf"] = CachedLocalBackend(cache, int(local_cfg(cfg).get("max_new_tokens", 256)))
    if "real" in sellers_cfg_backends:
        out["real"] = make_backend("real", cfg)
    return out


def prepare(cfg: Dict, backend_override: Optional[str] = None, cache_path: Optional[str] = None,
            runner_factory=None, log=print):
    """Precompute stage. Returns (pool, cache|None, measured stats per local model, precompute report)."""
    pool = build_task_pool(cfg)
    if backend_override and backend_override != "local_hf":
        return pool, None, {}, {}
    if not local_models(cfg):
        return pool, None, {}, {}
    cache = OutputCache(cache_path or cfg["run"].get("cache_file", "cache/llm_outputs.jsonl"))
    report = precompute(cfg, cache, pool, runner_factory=runner_factory, log=log)
    mnt = int(local_cfg(cfg).get("max_new_tokens", 256))
    stats = {m: model_stats(cache, pool, m, mnt) for m in local_models(cfg)}
    return pool, cache, {m: s for m, s in stats.items() if s}, report


def write_model_accuracy(results_dir: str, stats: Dict) -> str:
    md = render_model_accuracy_md(stats)
    os.makedirs(results_dir, exist_ok=True)
    with open(os.path.join(results_dir, "model_accuracy.md"), "w", encoding="utf-8") as fh:
        fh.write(md)
    return md


def run_all(cfg: Dict, seeds: Optional[List[int]] = None, backend_name: Optional[str] = None,
            n_tasks: Optional[int] = None, results_dir: Optional[str] = None, cache_path: Optional[str] = None,
            precompute_only: bool = False, runner_factory=None, log=None) -> Dict:
    """backend_name = backend override for ALL sellers (e.g. 'mock' for CI); None = per-seller backends."""
    log = log or (lambda *a: print(*a, flush=True))
    cfg = copy.deepcopy(cfg)
    seeds = list(seeds if seeds is not None else cfg["run"].get("seeds", [0]))
    results_dir = results_dir or cfg["run"].get("results_dir", "results")
    os.makedirs(results_dir, exist_ok=True)
    t0 = time.time()
    pool, cache, stats, pre_report = prepare(cfg, backend_name, cache_path, runner_factory, log)
    t_pre = time.time() - t0
    model_md = write_model_accuracy(results_dir, stats)
    if precompute_only:
        return {"precompute": pre_report, "model_stats": stats, "precompute_s": round(t_pre, 2)}

    rep = Reputation(cfg["models"], stats)
    seller_backends = {backend_name} if backend_name else {s.get("backend", "mock") for s in cfg["sellers"]}
    backends = build_backends(cfg, seller_backends, cache)
    log_path = os.path.join(results_dir, cfg["run"].get("log_file", "transactions.jsonl"))
    mcfg = cfg["market"]
    combos_plan = [("posted_price", p) for p in mcfg["policies"]]
    if "sealed_bid" in mcfg.get("mechanisms", []):
        combos_plan += [("sealed_bid", p) for p in mcfg.get("auction_policies", []) if p in mcfg["policies"]]

    t1 = time.time()
    combos = {}
    with TransactionLogger(log_path, mode="w") as logger:
        for mech, pol in combos_plan:
            per_seed = [run_single(cfg, mech, pol, seed, backends, rep, logger, pool, n_tasks, backend_name)
                        for seed in seeds]
            gw = [m.pop("gateway") for m in per_seed]
            combos[f"{mech}/{pol}"] = {"mechanism": mech, "policy": pol, "aggregate": aggregate(per_seed),
                                       "per_seed": per_seed, "gateway_per_seed": gw}
        n_lines = logger.count

    summary = {
        "disclaimer": DISCLAIMER,
        "backend_override": backend_name,
        "seller_backends": {s["id"]: (backend_name or s.get("backend", "mock")) for s in cfg["sellers"]},
        "seeds": seeds,
        "n_tasks_per_run": int(n_tasks or cfg["run"]["n_tasks"]),
        "task_pool": {"size": len(pool), "task_seed": cfg.get("task_pool", {}).get("task_seed", 1234)},
        "auction_format": mcfg["auction"].get("format", "second_price"),
        "log_file": log_path,
        "log_lines": n_lines,
        "precompute_s": round(t_pre, 2),
        "precompute": pre_report,
        "market_sim_s": round(time.time() - t1, 3),
        "elapsed_s": round(time.time() - t0, 3),
        "reputation": {m: {"source": rep.source(m), "tokens_mean": rep.tokens_mean(m),
                           "accuracy": {d: rep.accuracy(m, d) for d in (1, 2, 3)}}
                       for m in sorted({s["claimed_model"] for s in cfg["sellers"]})},
        "model_stats": stats,
        "combos": combos,
    }
    with open(os.path.join(results_dir, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False, default=str)
    with open(os.path.join(results_dir, "summary.md"), "w", encoding="utf-8") as fh:
        fh.write(render_markdown(summary, cfg, model_md))
    return summary


def _f(a: Dict, k: str, fmt: str = "{:.3f}") -> str:
    return f"{fmt.format(a[k]['mean'])} ± {fmt.format(a[k]['std'])}"


def render_markdown(summary: Dict, cfg: Dict, model_md: str = "") -> str:
    combos = summary["combos"]
    L = ["# token-market v2 — C2 compliance-constrained portfolio purchasing", "",
         f"> {summary['disclaimer']}", "",
         f"seller backends={summary['seller_backends']}, seeds={summary['seeds']}, "
         f"tasks/run={summary['n_tasks_per_run']} (drawn from fixed pool of {summary['task_pool']['size']}, "
         f"task_seed={summary['task_pool']['task_seed']}), auction=`{summary['auction_format']}`, "
         f"log lines={summary['log_lines']}, precompute={summary['precompute_s']}s, "
         f"market sim={summary['market_sim_s']}s. Values are mean ± std over seeds.", "",
         "## C2 baseline comparison (posted price)", "",
         "| policy | task accuracy | total cost | mean cost/task | purchases/task | expected→actual cost gap "
         "| budget violations | compliance violations | blocked/filtered | cross-border share | fraud-seller share "
         "| buyer surplus | mean task latency (ms) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in combos.values():
        if c["mechanism"] != "posted_price":
            continue
        a = c["aggregate"]
        L.append(f"| {c['policy']} | {_f(a, 'task_accuracy')} | {_f(a, 'total_cost')} "
                 f"| {_f(a, 'mean_cost_per_task', '{:.4f}')} | {_f(a, 'purchases_per_task', '{:.2f}')} "
                 f"| {_f(a, 'total_cost_gap', '{:+.3f}')} ({_f(a, 'cost_gap_rel', '{:+.1%}')}) "
                 f"| {_f(a, 'budget_violations', '{:.1f}')} ({_f(a, 'budget_violation_rate', '{:.1%}')}) "
                 f"| {_f(a, 'compliance_violations', '{:.1f}')} | {_f(a, 'blocked_or_filtered', '{:.1f}')} "
                 f"| {_f(a, 'cross_border_share')} | {_f(a, 'fraud_seller_share')} "
                 f"| {_f(a, 'total_buyer_surplus')} | {_f(a, 'mean_task_latency_ms', '{:.0f}')} |")

    L += ["", "## Mechanism comparison (single-seller policies: posted price vs sealed-bid "
          f"{summary['auction_format']} auction)", "",
          "| mechanism | policy | task accuracy | fill rate | total cost | mean price/1K | compliance violations "
          "| budget violations | cross-border share | fraud-seller share | buyer surplus | seller profit |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    auction_pols = {c["policy"] for c in combos.values() if c["mechanism"] == "sealed_bid"}
    for c in sorted(combos.values(), key=lambda c: (c["policy"], c["mechanism"])):
        if c["policy"] not in auction_pols:
            continue
        a = c["aggregate"]
        L.append(f"| {c['mechanism']} | {c['policy']} | {_f(a, 'task_accuracy')} | {_f(a, 'fill_rate')} "
                 f"| {_f(a, 'total_cost')} | {_f(a, 'mean_price_per_1k', '{:.4f}')} "
                 f"| {_f(a, 'compliance_violations', '{:.1f}')} | {_f(a, 'budget_violations', '{:.1f}')} "
                 f"| {_f(a, 'cross_border_share')} | {_f(a, 'fraud_seller_share')} "
                 f"| {_f(a, 'total_buyer_surplus')} | {_f(a, 'total_seller_profit')} |")

    L += ["", "## Accuracy by seller (purchases) and fraud gap", "",
          "| combo | " + " | ".join(s["id"] for s in cfg["sellers"]) + " | fraud acc gap (claimed rep − realised) |",
          "|---|" + "---|" * len(cfg["sellers"]) + "---|"]
    for name, c in combos.items():
        a = c["aggregate"]
        cells = [f"{a['seller_accuracy'][s['id']]['mean']:.3f}" if s["id"] in a["seller_accuracy"] else "–"
                 for s in cfg["sellers"]]
        L.append(f"| {name} | " + " | ".join(cells) + f" | {_f(a, 'fraud_accuracy_gap')} |")

    for title, key in (("Buyer surplus per buyer", "buyer_surplus"), ("Seller profit per seller", "seller_profit"),
                       ("Realised spend / budget per buyer", "budget_utilisation"),
                       ("Compliance violations by rule (audit-only baseline)", "violations_by_rule"),
                       ("Hard-filtered seller candidates by rule", "filtered_by_rule"),
                       ("Cascade / vote stop reasons", "stop_reasons")):
        agents = sorted({k for c in combos.values() for k in c["aggregate"].get(key, {})})
        L += ["", f"## {title}", ""]
        if not agents:
            L.append("_none_")
            continue
        L.append("| combo | " + " | ".join(agents) + " |")
        L.append("|---|" + "---|" * len(agents))
        for name, c in combos.items():
            d = c["aggregate"].get(key, {})
            if not d:
                continue
            cells = [f"{d[a]['mean']:.3f} ± {d[a]['std']:.3f}" if a in d else "0" for a in agents]
            L.append(f"| {name} | " + " | ".join(cells) + " |")

    L += ["", "## Model reputation used for routing (by CLAIMED model)", "",
          "| claimed model | source | advertised tokens | acc d1 | acc d2 | acc d3 |", "|---|---|---|---|---|---|"]
    for m, r in summary["reputation"].items():
        L.append(f"| {m} | {r['source']} | {r['tokens_mean']:.1f} | " +
                 " | ".join(f"{r['accuracy'][d]:.3f}" for d in (1, 2, 3)) + " |")

    L += ["", "## Measured local model accuracy", "", model_md.split("\n", 2)[-1] if model_md else "_n/a_"]

    swap = [s for s in cfg["sellers"] if s["claimed_model"] != s["actual_model"]]
    L += ["## Metric definitions", "",
          "- task accuracy = share of tasks whose FINAL portfolio answer equals gold (tasks with no answer count as wrong).",
          "- total cost = Σ actual_cost over purchases (actual_cost = price × actual reasoning tokens / 1000 × (1 + corridor fee rate)); "
          "mean cost/task = total cost / tasks.",
          "- expected→actual cost gap = Σ(actual_cost − expected_cost) over served purchases (relative to Σ expected); "
          "expected_cost uses the CLAIMED model's advertised mean tokens.",
          "- budget violations = purchases after which the buyer's realised spend exceeds its budget (budget_overrun=true); "
          "rate = / purchases. Purchases are only made if expected cost ≤ remaining budget, so overruns come only from "
          "token-length uncertainty.",
          "- compliance violations = purchases whose data flow breached a rule but went through (violation=true). "
          "Hard-constraint policies filter infeasible sellers before purchase and go through an enforcing gateway "
          "(must be 0); the compliance_unaware_cheapest baseline goes through the gateway in audit_only mode, so its "
          "breaches are counted rather than blocked.",
          "- blocked/filtered = seller candidates removed by the hard compliance filter + attempts blocked at the gateway.",
          "- cross-border share / fraud-seller share = share of purchases that are cross-border / served by a "
          f"model-swap seller ({', '.join(s['id'] + ': claims ' + s['claimed_model'] + ', serves ' + s['actual_model'] for s in swap) or 'none'}).",
          "- buyer surplus = Σ value_per_correct × final_correct − Σ actual_cost; seller profit = revenue − serving cost of the ACTUAL model.",
          "- task latency: single = purchase latency; cascade = sum (sequential); vote = max (parallel).", ""]
    return "\n".join(L)
