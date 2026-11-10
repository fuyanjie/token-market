#!/usr/bin/env python3
"""Run v6 delist + adaptive-audit ablations; write results/v6_*.{md,json} and v6_SUMMARY_zh.txt."""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tokenmarket.config import load_config
from tokenmarket.experiments import (Context, experiment_V6_adaptive, experiment_V6_delist,
                                     render_V6_adaptive, render_V6_delist)


def main():
    cfg = load_config(os.path.join(ROOT, "configs", "experiments.yaml"))
    rd = os.path.join(ROOT, "results")
    os.makedirs(rd, exist_ok=True)
    seeds = cfg["experiments"].get("seeds", [0, 1, 2])
    log = lambda *a: print(*a, flush=True)  # noqa: E731
    t0 = time.time()
    ctx = Context(cfg, None, None, log)

    delist = experiment_V6_delist(ctx, seeds, log)
    with open(os.path.join(rd, "v6_delist.json"), "w", encoding="utf-8") as fh:
        json.dump(delist, fh, indent=1, default=str)
    with open(os.path.join(rd, "v6_delist.md"), "w", encoding="utf-8") as fh:
        fh.write(render_V6_delist(delist))

    adaptive = experiment_V6_adaptive(ctx, seeds, log)
    with open(os.path.join(rd, "v6_adaptive_audit.json"), "w", encoding="utf-8") as fh:
        json.dump(adaptive, fh, indent=1, default=str)
    with open(os.path.join(rd, "v6_adaptive_audit.md"), "w", encoding="utf-8") as fh:
        fh.write(render_V6_adaptive(adaptive))

    # Chinese summary
    d0 = next(r for r in delist["rows"] if r["reputation_rounds"] == 0)
    d5 = next(r for r in delist["rows"] if r["reputation_rounds"] == 5)
    d20 = next(r for r in delist["rows"] if r["reputation_rounds"] == 20)
    fixed = next(r for r in adaptive["rows"] if r["arm"] == "fixed")
    adap = next(r for r in adaptive["rows"] if r["arm"] == "adaptive")
    lines = [
        "token-market v6 小结（主张安全读法）",
        "=" * 40,
        "",
        "改动：",
        "1. 抓到欺诈后停牌（market.audited.reputation_rounds；默认 0 以保持旧 F/J 可复现；消融测 0/5/20）。",
        "2. 固定审计预算下的自适应抽检（adaptive_audit；默认 false）：按风险分把 a·N 预算优先花在可疑卖方，剩余随机。",
        "3. 货款托管（escrow；默认 false）：审计决定前冻结卖方货款，罚没从托管扣，再放行余额；与标签延迟 L 正交。",
        "4. 结构化 audit trail（purchase_id / checks / detected / slash / ban_until），供自适应打分读历史。",
        "",
        "未做：订单簿/CLOB、多买方。主张不变：威慑压低卖方 q*；自适应审计只是降成本改进；不跟即时反馈下的 PILOT/StageRoute 比 J。",
        "",
        "停牌消融（D3, a=0.1, seeds=%s）：" % seeds,
        f"  rounds=0 : q_swap={d0['learned_q_swap']:.3f}  J={d0['joint_objective']:.3f}  fraud={d0['fraud_share']:.3f}",
        f"  rounds=5 : q_swap={d5['learned_q_swap']:.3f}  J={d5['joint_objective']:.3f}  fraud={d5['fraud_share']:.3f}",
        f"  rounds=20: q_swap={d20['learned_q_swap']:.3f}  J={d20['joint_objective']:.3f}  fraud={d20['fraud_share']:.3f}",
        "",
        "自适应审计（同预期预算 a=0.1, escrow=on）：",
        f"  fixed   : q_swap={fixed['learned_q_swap']:.3f}  J={fixed['joint_objective']:.3f}  "
        f"fraud={fixed['fraud_share']:.3f}  audits={fixed['n_audits']:.1f}  realized_a={fixed['audit_rate_realized']:.3f}",
        f"  adaptive: q_swap={adap['learned_q_swap']:.3f}  J={adap['joint_objective']:.3f}  "
        f"fraud={adap['fraud_share']:.3f}  audits={adap['n_audits']:.1f}  realized_a={adap['audit_rate_realized']:.3f}",
        f"  escrow fixed  held/slashed/released = {fixed['escrow_held']:.2f}/{fixed['escrow_slashed']:.2f}/{fixed['escrow_released']:.2f}",
        f"  escrow adap   held/slashed/released = {adap['escrow_held']:.2f}/{adap['escrow_slashed']:.2f}/{adap['escrow_released']:.2f}",
        "",
        "读法：看 q*（威慑）与在同等审计次数下的 fraud/J；不要把相对 bandit 的 J 写成全面更优。",
        f"耗时 {time.time() - t0:.1f}s。产物：results/v6_delist.{{md,json}}、results/v6_adaptive_audit.{{md,json}}、本文件。",
        "",
    ]
    with open(os.path.join(rd, "v6_SUMMARY_zh.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    log("\n".join(lines))


if __name__ == "__main__":
    main()
