"""Benchmark one batch of long prompts (background job): python scripts/bench_long.py MODEL DTYPE MNT"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tokenmarket.backends import LocalHFRunner, render_task_prompt
from tokenmarket.tasks import load_long_tasks
model, dtype, mnt = sys.argv[1], sys.argv[2], int(sys.argv[3])
pool = load_long_tasks("data/long_tasks.jsonl")
pool.sort(key=lambda t: len(t.question))
r = LocalHFRunner(model, 8, dtype).load()
outs, dt = r.generate([render_task_prompt(t) for t in pool[16:32]], mnt)
print(model, dtype, mnt, f"{dt:.1f}s", f"{dt / max(n for _, n in outs):.3f} s/step", [n for _, n in outs], flush=True)
