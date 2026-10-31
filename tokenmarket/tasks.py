"""Reasoning task stream with checkable integer gold answers."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List

SENSITIVITIES = ("public", "personal", "sensitive_personal", "important_data")
NAMES = ["Li Wei", "Tan Mei", "Ana Souza", "Chen Jun", "Lim Hui", "Joao Silva"]
ITEMS = ["apples", "batteries", "books", "tickets", "boxes", "coins"]


@dataclass
class Task:
    task_id: str
    task_type: str
    difficulty: int
    question: str
    gold: int
    buyer_id: str = ""
    sensitivity: str = "public"
    flags: List[str] = field(default_factory=list)


def _arithmetic(rng: random.Random, d: int):
    if d == 1:
        a, b, c = rng.randint(2, 30), rng.randint(2, 12), rng.randint(2, 12)
        return f"Compute {a} + {b} * {c}.", a + b * c
    if d == 2:
        a, b, c, e = rng.randint(2, 30), rng.randint(2, 30), rng.randint(2, 9), rng.randint(1, 50)
        return f"Compute ({a} + {b}) * {c} - {e}.", (a + b) * c - e
    a, b, c, e, f = (rng.randint(2, 20) for _ in range(5))
    return f"Compute (({a} * {b}) - {c}) * {e} + {f} * {a}.", ((a * b) - c) * e + f * a


def _word_problem(rng: random.Random, d: int):
    n, item = rng.choice(NAMES), rng.choice(ITEMS)
    x, y, z = rng.randint(3, 40), rng.randint(2, 9), rng.randint(2, 12)
    if d == 1:
        return f"{n} has {x} {item} and buys {y} more. How many {item} does {n} have?", x + y
    w = rng.randint(1, x)
    if d == 2:
        return (f"{n} has {x} {item}, buys {y} packs of {z} {item}, then gives away {w}. "
                f"How many {item} remain?", x + y * z - w)
    k = rng.randint(2, 4)
    total = (x + y * z - w) * k
    return (f"{n} has {x} {item}, buys {y} packs of {z}, gives away {w}, and then the remaining "
            f"stock is multiplied by {k} at a second store. How many {item} are there in total?", total)


def _sequence(rng: random.Random, d: int):
    if d == 1:
        a, s = rng.randint(1, 20), rng.randint(2, 9)
        seq = [a + i * s for i in range(5)]
        return f"What is the next number: {', '.join(map(str, seq))}, ?", a + 5 * s
    if d == 2:
        a, r = rng.randint(1, 5), rng.randint(2, 3)
        seq = [a * r ** i for i in range(5)]
        return f"What is the next number: {', '.join(map(str, seq))}, ?", a * r ** 5
    a, b, c = rng.randint(1, 3), rng.randint(0, 5), rng.randint(0, 9)
    seq = [a * i * i + b * i + c for i in range(1, 6)]
    return f"What is the next number: {', '.join(map(str, seq))}, ?", a * 36 + b * 6 + c


def _logic(rng: random.Random, d: int):
    c = rng.randint(3, 15)
    if d == 1:
        k = rng.randint(1, 10)
        return f"B is {c} years old. A is {k} years older than B. How old is A?", c + k
    m, k = rng.randint(2, 3), rng.randint(1, 10)
    if d == 2:
        return (f"C is {c} years old. B is {m} times as old as C. A is {k} years older than B. "
                f"How old is A?", c * m + k)
    j = rng.randint(1, 5)
    return (f"C is {c} years old. B is {m} times as old as C. A is {k} years older than B. "
            f"D is {j} years younger than the sum of A and C. How old is D?", (c * m + k) + c - j)


GENERATORS = {"arithmetic": _arithmetic, "word_problem": _word_problem,
              "sequence": _sequence, "logic": _logic}


def _weighted(rng: random.Random, mix: Dict) -> str:
    keys = list(mix.keys())
    return rng.choices(keys, weights=[float(mix[k]) for k in keys], k=1)[0]


def generate_task(rng: random.Random, idx: int, cfg: Dict) -> Task:
    tcfg = cfg.get("tasks", {})
    types = tcfg.get("types", list(GENERATORS))
    ttype = rng.choice(types)
    difficulty = int(_weighted(rng, tcfg.get("difficulty_mix", {1: 1, 2: 1, 3: 1})))
    q, gold = GENERATORS[ttype](rng, difficulty)
    return Task(task_id=f"t{idx:05d}", task_type=ttype, difficulty=difficulty, question=q, gold=int(gold))


def generate_stream(cfg: Dict, buyers, n_tasks: int, seed: int) -> List[Task]:
    """Deterministic task stream for a seed: identical across mechanism/policy combos."""
    rng = random.Random(f"tasks-{seed}")
    out = []
    for i in range(n_tasks):
        t = generate_task(rng, i, cfg)
        b = buyers[i % len(buyers)]
        t.buyer_id = b.id
        t.sensitivity = _weighted(rng, b.sensitivity_mix)
        if rng.random() < b.consent_rate:
            t.flags.append("specific_consent")
        out.append(t)
    return out


# ---------------------------------------------------------------------------
# v2: FIXED task pool for real (local_hf) models.
# The pool depends only on `task_pool.task_seed`, never on the run seed, so cached model outputs
# (keyed by prompt hash) always hit. Run seeds only change which pool items are drawn, in which
# order, for which buyer, and with which sensitivity / consent flags.
# ---------------------------------------------------------------------------

def build_task_pool(cfg: Dict) -> List[Task]:
    """Balanced pool: types cycle, difficulty cycles 1..3 -> ~equal cells per (type, difficulty)."""
    pcfg = cfg.get("task_pool", {})
    size = int(pcfg.get("size", 80))
    rng = random.Random(f"task-pool-{pcfg.get('task_seed', 1234)}")
    types = cfg.get("tasks", {}).get("types", list(GENERATORS))
    pool = []
    for i in range(size):
        ttype = types[i % len(types)]
        difficulty = 1 + (i // len(types)) % 3
        q, gold = GENERATORS[ttype](rng, difficulty)
        pool.append(Task(task_id=f"p{i:03d}", task_type=ttype, difficulty=difficulty, question=q, gold=int(gold)))
    return pool


def sample_run_tasks(pool: List[Task], buyers, n_tasks: int, seed: int) -> List[Task]:
    """Per-seed task instances drawn from the fixed pool: concatenated independent permutations
    (each pool item appears ~n_tasks/len(pool) times), with seed-dependent buyer, sensitivity, consent.
    Instance task_id = 't<k>_<pool id>'."""
    rng = random.Random(f"tasks-{seed}")
    order: List[Task] = []
    while len(order) < n_tasks:
        perm = list(pool)
        rng.shuffle(perm)
        order.extend(perm)
    out = []
    for i, p in enumerate(order[:n_tasks]):
        b = buyers[i % len(buyers)]
        t = Task(task_id=f"t{i:04d}_{p.task_id}", task_type=p.task_type, difficulty=p.difficulty,
                 question=p.question, gold=p.gold, buyer_id=b.id)
        t.sensitivity = _weighted(rng, b.sensitivity_mix)
        if rng.random() < b.consent_rate:
            t.flags.append("specific_consent")
        out.append(t)
    return out
