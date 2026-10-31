"""Precompute stage: run every distinct ACTUAL local_hf model over the fixed task pool once and store
outputs in the output cache. One model is loaded at a time and freed before the next one."""
from __future__ import annotations

import gc
import statistics
import time
from typing import Callable, Dict, List, Optional

from .backends import LocalHFRunner, parse_answer, prompt_sha256, render_task_prompt, task_max_new_tokens
from .cache import OutputCache


def local_cfg(cfg: Dict) -> Dict:
    return cfg.get("backends", {}).get("local_hf", {})


def local_models(cfg: Dict) -> List[str]:
    """Distinct actual models of sellers whose backend is local_hf."""
    return sorted({s["actual_model"] for s in cfg["sellers"] if s.get("backend", "mock") == "local_hf"})


def mnt_of(cfg: Dict, task) -> int:
    lc = local_cfg(cfg)
    mnt = int(lc.get("max_new_tokens", 256))
    return task_max_new_tokens(task, mnt, int(lc.get("long_max_new_tokens", mnt)))


def dtype_of(cfg: Dict, task) -> str:
    """fp32 for the synthetic pool (v2); long tasks use backends.local_hf.long_dtype (bf16 by default: halves
    memory and uses the CPU's AMX/AVX512-bf16 units, which made the long precompute feasible on this box)."""
    lc = local_cfg(cfg)
    return str(lc.get("long_dtype", "float32")) if task.is_long else str(lc.get("dtype", "float32"))


def precompute(cfg: Dict, cache: OutputCache, pool, runner_factory: Optional[Callable] = None,
               log: Callable = print) -> Dict[str, Dict]:
    lc = local_cfg(cfg)
    mnt = int(lc.get("max_new_tokens", 256))
    bs = int(lc.get("batch_size", 16))
    threads = int(lc.get("num_threads", 8))
    custom = runner_factory      # tests inject a fake runner factory(model_name); dtype is ignored then
    report = {}
    for model in local_models(cfg):
        missing = [t for t in pool if cache.get(model, render_task_prompt(t), mnt_of(cfg, t)) is None]
        report[model] = {"n_new": len(missing), "elapsed_s": 0.0}
        if not missing:
            log(f"[precompute] {model}: all {len(pool)} tasks cached")
            continue
        # similar-length prompts together: a batch runs until its longest generation finishes
        # (v3: batches never mix max_new_tokens, i.e. short synthetic and long math tasks)
        missing.sort(key=lambda t: (mnt_of(cfg, t), t.difficulty, len(t.question), t.task_id))
        t0 = time.time()
        groups = {}
        for t in missing:
            groups.setdefault((dtype_of(cfg, t), mnt_of(cfg, t)), []).append(t)
        batches = [(dt_, m, grp[i:i + bs]) for (dt_, m), grp in sorted(groups.items()) for i in range(0, len(grp), bs)]
        runner, runner_dtype = None, None
        for bi, (bdtype, bmnt, batch) in enumerate(batches):
            if runner is None or runner_dtype != bdtype:
                if runner is not None:
                    runner.unload()
                    del runner
                    gc.collect()
                runner = custom(model) if custom else LocalHFRunner(model, threads, bdtype)
                runner_dtype = bdtype
                runner.load()
                log(f"[precompute] {model} ({bdtype}): loaded at {time.time() - t0:.1f}s, generating "
                    f"{len(missing)} tasks (batch {bs})")
            prompts = [render_task_prompt(t) for t in batch]
            outs, dt = runner.generate(prompts, bmnt)
            tot = sum(max(1, n) for _, n in outs)
            for t, p, (text, n) in zip(batch, prompts, outs):
                ans, explicit, _ = parse_answer(text)
                cache.put({"model_name": model, "prompt_sha256": prompt_sha256(p), "max_new_tokens": bmnt,
                           "pool_task_id": t.task_id, "difficulty": t.difficulty, "gold": t.gold,
                           "raw_text": text, "parsed_answer": ans, "explicit_answer": explicit,
                           "correct": ans is not None and ans == t.gold, "reasoning_tokens": int(n),
                           "gen_time_s": round(dt * max(1, n) / tot, 4), "batch_size": len(batch),
                           "batch_time_s": round(dt, 3), "created_ts": time.time(), "dtype": bdtype,
                           "source": t.source})
            log(f"[precompute] {model}: batch {bi + 1}/{len(batches)} ({len(batch)} items, "
                f"max_new_tokens {bmnt}, {bdtype}) in {dt:.1f}s")
        runner.unload()
        del runner
        gc.collect()
        report[model]["elapsed_s"] = round(time.time() - t0, 1)
        log(f"[precompute] {model}: done in {report[model]['elapsed_s']}s")
    return report


def _ms(xs):
    return (statistics.fmean(xs), statistics.stdev(xs) if len(xs) > 1 else 0.0) if xs else (0.0, 0.0)


def _pct(xs, q):
    s = sorted(xs)
    return float(s[min(len(s) - 1, int(round(q * (len(s) - 1))))]) if s else 0.0


def model_stats(cache: OutputCache, pool, model: str, max_new_tokens: int,
                long_max_new_tokens: Optional[int] = None) -> Optional[Dict]:
    """Measured stats of a model on the pool; None unless every pool task is cached.
    Long tasks (v3) are looked up with long_max_new_tokens (default = max_new_tokens)."""
    lm = int(long_max_new_tokens or max_new_tokens)
    mnts = [task_max_new_tokens(t, max_new_tokens, lm) for t in pool]
    recs = [cache.get(model, render_task_prompt(t), m) for t, m in zip(pool, mnts)]
    if not recs or any(r is None for r in recs):
        return None
    by_d = {}
    for d in sorted({t.difficulty for t in pool}):
        rs = [r for r, t in zip(recs, pool) if t.difficulty == d]
        by_d[d] = {"n": len(rs), "accuracy": statistics.fmean(1.0 if r["correct"] else 0.0 for r in rs),
                   "tokens_mean": _ms([r["reasoning_tokens"] for r in rs])[0]}
    tm, ts = _ms([r["reasoning_tokens"] for r in recs])
    gm, gs = _ms([r["gen_time_s"] for r in recs])
    toks = [r["reasoning_tokens"] for r in recs]
    return {"model": model, "n": len(recs), "max_new_tokens": max_new_tokens, "long_max_new_tokens": lm,
            "tokens_p95": _pct(toks, 0.95), "tokens_max": max(toks),
            "accuracy": statistics.fmean(1.0 if r["correct"] else 0.0 for r in recs),
            "by_difficulty": by_d, "tokens_mean": tm, "tokens_std": ts,
            "gen_time_mean_s": gm, "gen_time_std_s": gs,
            "gen_time_total_s": sum(r["gen_time_s"] for r in recs),
            "explicit_answer_rate": statistics.fmean(1.0 if r["explicit_answer"] else 0.0 for r in recs),
            "truncated_rate": statistics.fmean(1.0 if r["reasoning_tokens"] >= m else 0.0
                                               for r, m in zip(recs, mnts))}


def render_model_accuracy_md(stats: Dict[str, Dict], header: bool = True) -> str:
    L = []
    if header:
        L += ["# Measured local model accuracy (task pool, greedy, CPU fp32)", ""]
    if not stats:
        return "\n".join(L + ["_no local_hf models measured (mock-only run)_", ""])
    diffs = sorted({d for s in stats.values() for d in s["by_difficulty"]})
    L.append("| model | n | acc overall | " + " | ".join(f"acc d{d} (n)" for d in diffs)
             + " | reasoning tokens mean ± std | gen time/item (s) mean ± std | total gen time (s) "
               "| explicit 'Answer:' rate | truncated rate |")
    L.append("|---|---|---|" + "---|" * len(diffs) + "---|---|---|---|---|")
    for m, s in stats.items():
        cells = [f"{s['by_difficulty'][d]['accuracy']:.3f} ({s['by_difficulty'][d]['n']})" for d in diffs]
        L.append(f"| {m} | {s['n']} | {s['accuracy']:.3f} | " + " | ".join(cells)
                 + f" | {s['tokens_mean']:.1f} ± {s['tokens_std']:.1f} | {s['gen_time_mean_s']:.2f} ± "
                   f"{s['gen_time_std_s']:.2f} | {s['gen_time_total_s']:.1f} | {s['explicit_answer_rate']:.3f} "
                   f"| {s['truncated_rate']:.3f} |")
    mnt = next(iter(stats.values()))["max_new_tokens"]
    L += ["", f"Greedy decoding, chat template, max_new_tokens={mnt}, batched (left padding). "
              "reasoning tokens = generated tokens excluding EOS/padding; gen time/item = amortised share of "
              "batch wall time proportional to generated tokens (8 CPU threads). Correct = parsed answer "
              "(last 'Answer:' number, else last number) == gold.", ""]
    return "\n".join(L)
