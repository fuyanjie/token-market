#!/usr/bin/env python3
"""WP0 read-only fact dump for docs/v1.1/SIM_NOTES.md. Loads the v1.0 config exactly as scripts/run_v1.py does
(point_config + prepare), changes NO simulator state, and writes results/v1.1/wp0_sim_facts/facts.json + facts.md.

  /workspace/tmvenv/bin/python scripts/v1.1/sim_facts.py
"""
import collections
import csv
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from run_v1 import point_config  # noqa: E402
from tokenmarket.config import load_config  # noqa: E402
from tokenmarket.sellers import Reputation  # noqa: E402
from tokenmarket.sim import prepare  # noqa: E402
from tokenmarket.strategic import make_strategy  # noqa: E402
from tokenmarket.tasks import load_long_tasks  # noqa: E402

OUT = os.path.join(ROOT, "results", "v1.1", "wp0_sim_facts")
os.makedirs(OUT, exist_ok=True)
base = load_config(os.path.join(ROOT, "configs", "v1.0", "scale.yaml"))
cfg = point_config(base, "fixed_audit_a0.10", 1.0, 0)
pool, cache, stats, _ = prepare(cfg, None, os.path.join(ROOT, "cache", "llm_outputs.jsonl"), None, lambda *a: None)
rep = Reputation(cfg["models"], stats)
f, m = cfg["fraud"], cfg["market"]
H, L = cfg["roster"]["strategic"]["claimed_model"], cfg["roster"]["strategic"]["cheap_model"]
facts = {"fraud": {k: f.get(k) for k in ("strategy", "penalty", "detect_prob", "detect_prob_length", "reputation_rounds",
                                          "reputation_loss", "billed_token_policy", "theft_max_new_tokens",
                                          "length_audit_tol", "cost_gap_per_1k", "downgrade_min_difficulty", "learning")},
         "market_audit": m.get("audit"), "market_audited": m.get("audited"), "cascade": m.get("cascade"),
         "n_tasks": cfg["run"]["n_tasks"], "n_rounds": cfg["run"]["n_rounds"],
         "per_round": -(-cfg["run"]["n_tasks"] // cfg["run"]["n_rounds"])}
facts["pool"] = {"kind": cfg.get("task_pool", {}).get("kind"), "size": len(pool),
                 "by_difficulty": dict(collections.Counter(t.difficulty for t in pool))}
facts["models"] = {mod: {"source": rep.source(mod), "tokens_mean": rep.tokens_mean(mod),
                         "acc_by_d": {d: rep.accuracy(mod, d) for d in (1, 2, 3)}}
                   for mod in sorted({s["claimed_model"] for s in cfg["sellers"]} | {L})}
# per-pool-item tokens for H and L (served-token reality, not the advertised mean)
from tokenmarket.precompute import render_task_prompt  # noqa: E402
tokH = [cache.get(H, render_task_prompt(t), 256)["reasoning_tokens"] for t in pool]
tokL = [cache.get(L, render_task_prompt(t), 256)["reasoning_tokens"] for t in pool]
facts["tokens_pool"] = {"H_mean": statistics.fmean(tokH), "L_mean": statistics.fmean(tokL),
                        "H_le_48_share": sum(x <= 48 for x in tokH) / len(tokH)}
# roster + cost ranking (exp_cost without corridor fee: price * tokens_mean(claimed) / 1000)
sellers = []
for s in cfg["sellers"]:
    ec = s["price_per_1k"] * rep.tokens_mean(s["claimed_model"]) / 1000
    kind = "strategic:" + "+".join(s["strategy"]["attack_modes"]) if s["claimed_model"] != s["actual_model"] else "honest"
    sellers.append({"id": s["id"], "kind": kind, "claimed": s["claimed_model"], "price_per_1k": s["price_per_1k"],
                    "cost_per_1k": s["cost_per_1k"], "jurisdiction": s["jurisdiction"], "exp_cost_nofee": ec})
sellers.sort(key=lambda r: r["exp_cost_nofee"])
for i, r in enumerate(sellers):
    r["cost_rank"] = i + 1
facts["sellers_by_exp_cost"] = sellers
# break-even per strategic seller
P, d, dl = float(f["penalty"]), float(f["detect_prob"]), float(f["detect_prob_length"])
cH, cL = float(cfg["roster"]["strategic"]["honest_cost_per_1k"]), float(cfg["roster"]["strategic"]["cheap_cost_per_1k"])
tmH, tmL = rep.tokens_mean(H), rep.tokens_mean(L)
be = []
for s in cfg["sellers"]:
    if s["claimed_model"] == s["actual_model"]:
        continue
    st = make_strategy(s, cfg, 0.1, rep, ["identity", "length"])
    p = s["price_per_1k"]
    swap_code = st.cost_saving                             # code's analytic: cost_gap * tokens_mean(H)/1000
    swap_real = ((p - cL) * tmL - (p - cH) * tmH) / 1000  # realised: revenue AND cost on served tokens
    theft_code = st.theft_saving
    be.append({"id": s["id"], "modes": s["strategy"]["attack_modes"], "price": p,
               "swap_saving_code": swap_code, "swap_saving_realised_mean": swap_real,
               "a_star_swap_code": swap_code / (d * P), "a_star_swap_realised": swap_real / (d * P),
               "theft_saving_code": theft_code, "a_star_theft_code": theft_code / (dl * P),
               "scale": st.scale})
facts["break_even"] = be
facts["break_even_note"] = "a* = saving / (d * P); attack profitable iff a < a*. Risk-adaptive a in [0.05, 0.5]."
# cache inventory
cnt = collections.Counter()
with open(os.path.join(ROOT, "cache", "llm_outputs.jsonl"), encoding="utf-8") as fh:
    for line in fh:
        r = json.loads(line)
        pid = str(r.get("pool_task_id"))
        src = "gsm8k" if pid.startswith("gsm8k") else "math500" if pid.startswith("math500") else "synthetic"
        cnt[(r["model_name"], src, int(r["max_new_tokens"]))] += 1
facts["cache_inventory"] = [{"model": k[0], "source": k[1], "max_new_tokens": k[2], "n": v} for k, v in sorted(cnt.items())]
lt = load_long_tasks(os.path.join(ROOT, "data", "long_tasks.jsonl"))
facts["long_tasks_file"] = dict(collections.Counter(t.source for t in lt))
# v1.0 main table, read-only: tail_trade_rate and Q by method (all pi pooled) -> explains Q~0.5
rows = list(csv.DictReader(open(os.path.join(ROOT, "results", "v1.0", "main", "per_seed.csv"), encoding="utf-8")))
agg = collections.defaultdict(list)
for r in rows:
    agg[r["method"]].append(r)
facts["v1_main_by_method"] = {
    k: {"n": len(v), "tail_trade_rate": sum(r["tail_trade"] == "True" for r in v) / len(v),
        "mean_tail_sales": statistics.fmean(float(r["tail_sales"]) for r in v),
        "E": statistics.fmean(float(r["E"]) for r in v), "Q": statistics.fmean(float(r["Q"]) for r in v),
        "n_audits": statistics.fmean(float(r["n_audits"]) for r in v)} for k, v in agg.items()}
with open(os.path.join(OUT, "facts.json"), "w", encoding="utf-8") as fh:
    json.dump(facts, fh, indent=1, default=str)
Lm = ["# WP0 simulator facts (generated by scripts/v1.1/sim_facts.py; config configs/v1.0/scale.yaml, roster seed fixed)", ""]
Lm += ["## Economics", "", "```", json.dumps({k: facts[k] for k in ("fraud", "market_audit", "market_audited", "n_tasks",
                                                                   "n_rounds", "per_round", "pool", "models", "tokens_pool")},
                                             indent=1, default=str), "```", ""]
Lm += ["## Sellers by expected cost (price x advertised tokens of claimed model / 1000, before corridor fee)", "",
       "| rank | id | kind | claimed | price/1k | exp cost |", "|---|---|---|---|---|---|"]
Lm += [f"| {r['cost_rank']} | {r['id']} | {r['kind']} | {r['claimed'].split('/')[-1]} | {r['price_per_1k']} | {r['exp_cost_nofee']:.5f} |"
       for r in sellers]
Lm += ["", "## Break-even audit rate a* = saving / (d·P)  (P=%g, d=%g, d_len=%g)" % (P, d, dl), "",
       "| id | modes | price | swap saving (code) | a*_swap (code) | swap saving (realised mean tokens) | a*_swap (realised) | theft saving (code) | a*_theft |",
       "|---|---|---|---|---|---|---|---|---|"]
Lm += [f"| {b['id']} | {'+'.join(b['modes'])} | {b['price']} | {b['swap_saving_code']:.5f} | {b['a_star_swap_code']:.4f} | "
       f"{b['swap_saving_realised_mean']:.5f} | {b['a_star_swap_realised']:.4f} | {b['theft_saving_code']:.5f} | {b['a_star_theft_code']:.4f} |"
       for b in be]
Lm += ["", "## Cache inventory (cache/llm_outputs.jsonl)", "", "| model | source | max_new_tokens | n |", "|---|---|---|---|"]
Lm += [f"| {c['model']} | {c['source']} | {c['max_new_tokens']} | {c['n']} |" for c in facts["cache_inventory"]]
Lm += ["", f"data/long_tasks.jsonl: {facts['long_tasks_file']}", "",
       "## v1.0 main table by method (read-only from results/v1.0/main/per_seed.csv, all π and seeds pooled)", "",
       "| method | n | tail_trade_rate | mean tail_sales | E | Q | n_audits |", "|---|---|---|---|---|---|---|"]
Lm += [f"| {k} | {v['n']} | {v['tail_trade_rate']:.3f} | {v['mean_tail_sales']:.2f} | {v['E']:.4f} | {v['Q']:.4f} | {v['n_audits']:.1f} |"
       for k, v in facts["v1_main_by_method"].items()]
with open(os.path.join(OUT, "facts.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(Lm) + "\n")
print("wrote", OUT)
