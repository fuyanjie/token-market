#!/usr/bin/env python3
"""v3 + v4 experiments on cached model outputs (no model is loaded):

  python run_experiments.py                       # C, I, T, A, D, J, F (+ B if the long-math cache is complete)
  python run_experiments.py --only C D            # subset
  python run_experiments.py --backend-override mock --seeds 0   # fast all-mock run (CI)

Writes results/fraud_audit_threshold.{md,json}, results/baselines.{md,json}, results/cost_curves.{md,json,png},
results/long_math.{md,json} (+ results/long_math*/summary.md), v4: results/imperfect_detection.{md,json,png},
results/token_theft.{md,json}, results/joint_objective.{md,json}, v5: results/feedback_ablation.{md,json,png},
and results/experiments_summary.md.
"""
import argparse
import json
import os
import sys
import time

from tokenmarket.config import load_config
from tokenmarket.experiments import (REAL_VS_SIM, Context, experiment_A, experiment_B, experiment_C, experiment_D,
                                     experiment_F, experiment_I, experiment_J, experiment_T, plot_A, plot_C, plot_F,
                                     plot_I, render_A, render_B, render_C, render_D, render_F, render_I, render_J,
                                     render_T)


def _dump(results_dir, name, obj, md):
    with open(os.path.join(results_dir, f"{name}.json"), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, default=str)
    with open(os.path.join(results_dir, f"{name}.md"), "w", encoding="utf-8") as fh:
        fh.write(md)


def main(argv=None):
    ap = argparse.ArgumentParser(description="token-market v3 + v4 experiments")
    ap.add_argument("--config", default="configs/experiments.yaml")
    ap.add_argument("--only", nargs="+", choices=["A", "B", "C", "D", "I", "T", "J", "F"],
                    default=["C", "I", "T", "D", "A", "J", "F", "B"])
    ap.add_argument("--seeds", type=int, nargs="+", default=None)
    ap.add_argument("--backend-override", choices=["mock", "local_hf"], default=None)
    ap.add_argument("--results-dir", default=None)
    ap.add_argument("--cache-file", default=None)
    args = ap.parse_args(argv)

    t0 = time.time()
    cfg = load_config(args.config)
    ex = cfg["experiments"]
    seeds = args.seeds or ex.get("seeds", [0, 1, 2])
    rd = args.results_dir or cfg["run"].get("results_dir", "results")
    os.makedirs(rd, exist_ok=True)
    log_dir = os.path.join(rd, "experiments")
    log = lambda *a: print(*a, flush=True)  # noqa: E731
    ctx = Context(cfg, args.backend_override, args.cache_file, log)
    md_parts = ["# token-market v5 — experiment summary", "",
                "Novelty framing: compliance-constrained portfolio purchasing + strategic fraud (model swap AND token "
                "theft) under IMPERFECT audits, compared with PILOT-style / StageRoute-style baselines on the JOINT "
                "objective J = accuracy − λ·violation rate − μ·fraud share (headline: section J). v5 (section F): the setting "
                "where audits matter is DELAYED / SPARSE outcome feedback - audits are a separate, immediate signal, "
                "while the bandits' correctness labels are delayed by L steps or revealed w.p. π. Reasoning-token "
                "length uncertainty is NOT claimed as a contribution: the expected-vs-actual cost logging is "
                "infrastructure and its finding is negative (overruns ≈ 0 under normal budgets, they only bind under "
                "tight budgets; section B).", "",
                f"config `{args.config}`, seeds={seeds}, backend override={args.backend_override}, "
                f"reputation source: " + ", ".join(f"{m}: {ctx.rep.source(m)}" for m in sorted(
                    {s['claimed_model'] for s in cfg['sellers']})), ""]
    out = {}
    head = len(md_parts)
    if "C" in args.only:
        out["C"] = experiment_C(ctx, seeds, log_dir, log)
        md = render_C(out["C"])
        _dump(rd, "fraud_audit_threshold", out["C"], md)
        plot_C(out["C"], os.path.join(rd, "fraud_audit_threshold.png"))
        md_parts += [md.replace("# C —", "## C —", 1)]
    jpart = None
    if "J" in args.only:   # v4 headline first in the summary
        out["J"] = experiment_J(ctx, seeds, log_dir, log)
        md = render_J(out["J"])
        _dump(rd, "joint_objective", out["J"], md)
        jpart = md.split("## Appendix")[0].replace("# Joint objective —", "## J — Joint objective —", 1)
    fpart = None
    if "F" in args.only:   # v5: delayed / sparse outcome feedback; placed right after J in the summary
        out["F"] = experiment_F(ctx, seeds, log)
        md = render_F(out["F"])
        _dump(rd, "feedback_ablation", out["F"], md)
        if plot_F(out["F"], os.path.join(rd, "feedback_ablation.png")):
            log(f"[F] wrote {rd}/feedback_ablation.png")
        fpart = md.replace("# F —", "## F —", 1).replace("\n## ", "\n### ")
    if "I" in args.only:
        out["I"] = experiment_I(ctx, seeds, log)
        md = render_I(out["I"])
        _dump(rd, "imperfect_detection", out["I"], md)
        if plot_I(out["I"], os.path.join(rd, "imperfect_detection.png")):
            log(f"[I] wrote {rd}/imperfect_detection.png")
        hp = out["I"]["heatmap_penalty"]
        secs = md.split("\n## ")
        keep = [secs[0].replace("# Imperfect detection —", "## I — Imperfect detection —", 1)] + \
            ["### " + x for x in secs[1:] if x.startswith(("Thresholds", f"learned swap rate q (P = {hp})"))]
        md_parts += ["\n".join(keep)]
    if "T" in args.only:
        out["T"] = experiment_T(ctx, seeds, log)
        md = render_T(out["T"])
        _dump(rd, "token_theft", out["T"], md)
        md_parts += [md.split("## Sweep")[0].replace("# Token theft —", "## T — Token theft —", 1)]
    if "A" in args.only:
        out["A"] = experiment_A(ctx, seeds, log)
        md = render_A(out["A"])
        _dump(rd, "cost_curves", out["A"], md)
        if plot_A(out["A"], os.path.join(rd, "cost_curves.png")):
            log(f"[A] wrote {rd}/cost_curves.png")
    if "D" in args.only:
        out["D"] = experiment_D(ctx, seeds, log_dir, out.get("A"), log)
        md = render_D(out["D"])
        _dump(rd, "baselines", out["D"], md)
        md_parts += [md.replace("# D —", "## D —", 1)]
    if "A" in args.only:   # after D in the summary, but computed first so D can quote equal-cost accuracy
        md_parts += [render_A(out["A"]).split("## All points")[0].replace("# A —", "## A —", 1)]
    if "B" in args.only:
        out["B"] = experiment_B(ex["B"]["config"], seeds, float(ex["B"]["tight_budget_multiplier"]),
                                args.backend_override, args.cache_file, log)
        if out["B"]:
            md = render_B(out["B"])
            _dump(rd, "long_math", out["B"], md)
            md_parts += [md.replace("# B —", "## B —", 1)]
    md_parts[head:head] = [p for p in (jpart, fpart) if p]
    md_parts += REAL_VS_SIM + [f"_total experiment time {time.time() - t0:.1f}s_", ""]
    with open(os.path.join(rd, "experiments_summary.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md_parts))
    log(f"done in {time.time() - t0:.1f}s -> {rd}/experiments_summary.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
