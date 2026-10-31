"""Simulation driver: runs every mechanism x policy combo over seeds and writes logs + summaries."""
from __future__ import annotations

import copy
import json
import os
import random
import time
from typing import Dict, List, Optional

from .backends import make_backend
from .buyers import load_buyers
from .compliance import ComplianceEngine, DISCLAIMER
from .gateway import CrossBorderGateway
from .logging_schema import TransactionLogger
from .matching import posted_price, sealed_bid
from .metrics import aggregate, run_metrics
from .sellers import load_sellers
from .tasks import generate_stream
from .verification import TrustingVerifier


def _unserved_record(base: Dict, status: str, rule_id: str) -> Dict:
    base.update(cross_border=base.get("cross_border", False), price_per_1k=base.get("price_per_1k", 0.0),
                reasoning_tokens=0, cost=0.0, fee=0.0, latency_ms=0.0, answer=None, correct=None,
                status=status, rule_id=rule_id, buyer_surplus=0.0, seller_profit=0.0)
    return base


def run_single(cfg: Dict, mechanism: str, policy: str, seed: int, backend, logger: TransactionLogger,
               n_tasks: Optional[int] = None) -> Dict:
    run_cfg = cfg["run"]
    n_tasks = int(n_tasks or run_cfg["n_tasks"])
    n_rounds = max(1, int(run_cfg.get("n_rounds", 1)))
    sellers, buyers = load_sellers(cfg), load_buyers(cfg)
    buyer_by_id = {b.id: b for b in buyers}
    engine = ComplianceEngine.from_config(cfg)
    gateway = CrossBorderGateway(engine, cfg)
    verifier = TrustingVerifier()
    models = cfg["models"]
    auction_cfg = cfg["market"]["auction"]
    run_id = f"{mechanism}__{policy}__seed{seed}"
    rng_backend = random.Random(f"backend-{seed}")
    rng_market = random.Random(f"market-{seed}")
    rng_latency = random.Random(f"latency-{seed}")

    tasks = generate_stream(cfg, buyers, n_tasks, seed)
    per_round = -(-n_tasks // n_rounds)
    records: List[Dict] = []
    audit_violations = 0

    for i, task in enumerate(tasks):
        rnd = i // per_round
        if i % per_round == 0:
            for s in sellers:
                s.reset_round()
        buyer = buyer_by_id[task.buyer_id]
        rec = {"ts": time.time(), "round": rnd, "run_id": run_id, "mechanism": mechanism, "policy": policy,
               "seed": seed, "buyer_id": buyer.id, "buyer_jurisdiction": buyer.jurisdiction,
               "task_id": task.task_id, "task_type": task.task_type, "difficulty": task.difficulty,
               "sensitivity": task.sensitivity, "seller_id": None, "seller_jurisdiction": None,
               "claimed_model": None, "actual_model": None, "gold": task.gold,
               "verification_status": "unverified"}

        if mechanism == "posted_price":
            match = posted_price(buyer, sellers, task, policy, gateway.would_allow)
        elif mechanism == "sealed_bid":
            match = sealed_bid(buyer, sellers, task, policy, gateway.would_allow, rng_market, auction_cfg)
        else:
            raise ValueError(f"unknown mechanism {mechanism}")

        if match.seller is None:
            records.append(_unserved_record(rec, "unfilled", match.reason))
            logger.write(records[-1])
            continue

        s = match.seller
        rec.update(seller_id=s.id, seller_jurisdiction=s.jurisdiction, claimed_model=s.claimed_model,
                   actual_model=s.actual_model, cross_border=s.jurisdiction != buyer.jurisdiction,
                   price_per_1k=match.price_per_1k)

        # budget check on expected cost (buyer uses claimed model's token profile)
        exp_tokens = models[s.claimed_model]["tokens_mean"] * (0.6 + 0.3 * task.difficulty)
        _, fee_rate = gateway.corridor_params(buyer.jurisdiction, s.jurisdiction)
        if not buyer.can_afford(match.price_per_1k * exp_tokens / 1000.0 * (1 + fee_rate)):
            records.append(_unserved_record(rec, "unfilled", "MKT-BUDGET-EXHAUSTED"))
            logger.write(records[-1])
            continue

        gw = gateway.route(buyer, s, task)
        if not gw.allowed:
            records.append(_unserved_record(rec, "blocked", gw.rule_id))
            logger.write(records[-1])
            continue

        s.used_this_round += 1
        res = backend.solve(task, s.actual_model, models[s.actual_model], s.reasoning_effort, rng_backend)
        tx = dict(rec, reasoning_tokens=res.reasoning_tokens, fee_rate=gw.fee_rate)
        settle = verifier.settle(tx)
        correct = res.answer is not None and int(res.answer) == task.gold
        buyer.spent += settle.buyer_pays + settle.fee
        latency = s.sample_latency(rng_latency) + gw.latency_penalty_ms
        rec.update(reasoning_tokens=int(res.reasoning_tokens), cost=settle.buyer_pays, fee=settle.fee,
                   latency_ms=latency, answer=None if res.answer is None else int(res.answer),
                   correct=bool(correct), status="allowed", rule_id=None,
                   buyer_surplus=buyer.value_per_correct * correct - settle.buyer_pays - settle.fee,
                   seller_profit=settle.seller_receives - s.cost_per_1k * res.reasoning_tokens / 1000.0,
                   verification_status=verifier.verify_model_identity(tx))
        # independent post-hoc audit: any allowed flow that violates the rules counts as a violation
        if not engine.evaluate_flow(buyer, s, task).allowed:
            audit_violations += 1
        records.append(rec)
        logger.write(rec)

    m = run_metrics(records, [b.id for b in buyers], [s.id for s in sellers], models, audit_violations)
    m["gateway"] = gateway.stats()
    return m


def run_all(cfg: Dict, seeds: Optional[List[int]] = None, backend_name: Optional[str] = None,
            n_tasks: Optional[int] = None, results_dir: Optional[str] = None) -> Dict:
    cfg = copy.deepcopy(cfg)
    seeds = list(seeds if seeds is not None else cfg["run"].get("seeds", [0]))
    backend_name = backend_name or cfg["run"].get("backend", "mock")
    results_dir = results_dir or cfg["run"].get("results_dir", "results")
    os.makedirs(results_dir, exist_ok=True)
    log_path = os.path.join(results_dir, cfg["run"].get("log_file", "transactions.jsonl"))
    backend = make_backend(backend_name, cfg)
    mechs, pols = cfg["market"]["mechanisms"], cfg["market"]["policies"]

    t0 = time.time()
    combos = {}
    with TransactionLogger(log_path, mode="w") as logger:
        for mech in mechs:
            for pol in pols:
                per_seed = []
                for seed in seeds:
                    per_seed.append(run_single(cfg, mech, pol, seed, backend, logger, n_tasks))
                gw = [m.pop("gateway") for m in per_seed]
                combos[f"{mech}/{pol}"] = {"mechanism": mech, "policy": pol,
                                           "aggregate": aggregate(per_seed),
                                           "per_seed": per_seed, "gateway_per_seed": gw}
        n_lines = logger.count

    summary = {
        "disclaimer": DISCLAIMER,
        "backend": backend_name,
        "seeds": seeds,
        "n_tasks_per_run": int(n_tasks or cfg["run"]["n_tasks"]),
        "auction_format": cfg["market"]["auction"].get("format", "second_price"),
        "log_file": log_path,
        "log_lines": n_lines,
        "elapsed_s": round(time.time() - t0, 3),
        "combos": combos,
    }
    with open(os.path.join(results_dir, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(results_dir, "summary.md"), "w", encoding="utf-8") as fh:
        fh.write(render_markdown(summary, cfg))
    return summary


def _f(a: Dict, k: str, fmt: str = "{:.3f}") -> str:
    return f"{fmt.format(a[k]['mean'])} ± {fmt.format(a[k]['std'])}"


def render_markdown(summary: Dict, cfg: Dict) -> str:
    L = ["# token-market v1 — simulation summary", "",
         f"> {summary['disclaimer']}", "",
         f"backend=`{summary['backend']}`, seeds={summary['seeds']}, tasks/run={summary['n_tasks_per_run']}, "
         f"auction=`{summary['auction_format']}`, log lines={summary['log_lines']}, "
         f"elapsed={summary['elapsed_s']}s. Values are mean ± std over seeds.", "",
         "## Mechanism × policy", "",
         "| mechanism | policy | fill rate | accuracy | total cost | fees | mean lat (ms) | p95 lat (ms) "
         "| blocked | violations through | cross-border share | fraud exposure | fraud acc gap | buyer surplus | seller profit |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in summary["combos"].values():
        a = c["aggregate"]
        L.append(f"| {c['mechanism']} | {c['policy']} | {_f(a, 'fill_rate')} | {_f(a, 'accuracy')} "
                 f"| {_f(a, 'total_cost')} | {_f(a, 'total_fee', '{:.4f}')} | {_f(a, 'mean_latency_ms', '{:.0f}')} "
                 f"| {_f(a, 'p95_latency_ms', '{:.0f}')} | {_f(a, 'blocked_attempts', '{:.1f}')} "
                 f"| {_f(a, 'violating_flows_through', '{:.0f}')} | {_f(a, 'cross_border_share')} "
                 f"| {_f(a, 'fraud_exposure')} | {_f(a, 'fraud_accuracy_gap')} "
                 f"| {_f(a, 'total_buyer_surplus')} | {_f(a, 'total_seller_profit')} |")

    for title, key in (("Buyer surplus per buyer", "buyer_surplus"), ("Seller profit per seller", "seller_profit"),
                       ("Blocked attempts by rule", "blocked_by_rule")):
        agents = sorted({k for c in summary["combos"].values() for k in c["aggregate"][key]})
        L += ["", f"## {title}", ""]
        if not agents:
            L.append("_none_")
            continue
        L.append("| combo | " + " | ".join(agents) + " |")
        L.append("|---|" + "---|" * len(agents))
        for name, c in summary["combos"].items():
            d = c["aggregate"][key]
            cells = [f"{d[a]['mean']:.3f} ± {d[a]['std']:.3f}" if a in d else "0" for a in agents]
            L.append(f"| {name} | " + " | ".join(cells) + " |")

    swap = [s for s in cfg["sellers"] if s["claimed_model"] != s["actual_model"]]
    L += ["", "## Notes", "",
          "- fraud exposure = share of allowed tx served by a seller whose actual_model != claimed_model "
          f"({', '.join(s['id'] + ': ' + s['claimed_model'] + ' -> ' + s['actual_model'] for s in swap) or 'none'}).",
          "- fraud acc gap = expected accuracy of the claimed model on those tasks minus realised accuracy.",
          "- blocked = attempts stopped by the gateway's compliance rules; violations through = allowed flows that "
          "fail an independent re-audit (should be 0).",
          "- buyer surplus = value_per_correct * correct - cost - fee; seller profit = revenue - actual serving cost.", ""]
    return "\n".join(L)
