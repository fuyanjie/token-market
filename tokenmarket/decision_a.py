"""Frozen Decision A design and output guards; no simulations on import."""
from pathlib import Path

from .wp1 import enumerate_wp1, run_cell, summarize_cells

PROTOCOL_SHA256 = "daddac6c0dddb22b08701caff5715e77215ae13a588512af176ff4933430b102"
LEARNERS = ("egreedy", "fictitious_play", "exp3")
N_ROUNDS = 1000
N_TASKS = 10000
BUDGET_MULTIPLIER = 2 * N_TASKS / 480
PROTECTED = (
    "wp1", "wp1_eval", "wp2", "wp2_eval", "v1.2_wp1", "v1.2_wp2",
    "v1.2_wp2_r1000", "v1.2_wp2_eval_r1000",
)


def cells():
    return [c for c in enumerate_wp1()
            if c.router in ("pilot", "strongest") and c.pi == 1
            and c.arm == "factorial"]


def fresh_output(root, value, run=None):
    """Resolve symlinks before checks; never nest outputs in an existing readout."""
    out = Path(value).resolve()
    results = (root / "results/v1.1").resolve()
    if not out.is_relative_to(results) or out == results:
        raise ValueError("outputs must be under results/v1.1/")
    for name in PROTECTED:
        protected = (results / name).resolve()
        if out == protected or out.is_relative_to(protected) or protected.is_relative_to(out):
            raise ValueError("protected official output path")
    if run is not None:
        run = Path(run).resolve()
        if out == run or out.is_relative_to(run) or run.is_relative_to(out):
            raise ValueError("analysis output must be isolated from the run directory")
    for parent in out.parents:
        if parent == results:
            break
        if parent.exists() and any(p.is_file() for p in parent.iterdir()):
            raise ValueError("cannot nest outputs inside a run or published evaluation")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError("output directory must be fresh/empty")
    return out


def summarize(rows):
    """Keep cell IDs unchanged, but never pool different learning rules."""
    result = []
    for learner in LEARNERS:
        result.extend(dict(c, learner=learner) for c in summarize_cells(
            [r for r in rows if r["learner"] == learner]))
    return result


def run_job(job):
    # Delegate unchanged to WP1's configuration/RNG path. Separate only disk logs.
    if job.get("log_dir"):
        job = dict(job, log_dir=job["log_dir"] / job["learner"])
    return run_cell(job)
