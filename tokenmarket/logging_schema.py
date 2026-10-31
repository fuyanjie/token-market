"""Unified transaction log schema: exactly one JSONL line per transaction (allowed, blocked or unfilled)."""
from __future__ import annotations

import json
from typing import Dict, List

NUM = (int, float)
STATUSES = ("allowed", "blocked", "unfilled")

# field -> (accepted types, nullable)
SCHEMA: Dict[str, tuple] = {
    "ts": (NUM, False),                 # wall-clock unix time
    "round": (int, False),
    "run_id": (str, False),
    "mechanism": (str, False),
    "policy": (str, False),
    "seed": (int, False),
    "buyer_id": (str, False),
    "buyer_jurisdiction": (str, False),
    "task_id": (str, False),
    "task_type": (str, False),
    "difficulty": (int, False),
    "sensitivity": (str, False),
    "seller_id": (str, True),           # null when unfilled
    "seller_jurisdiction": (str, True),
    "claimed_model": (str, True),
    "actual_model": (str, True),
    "cross_border": (bool, False),
    "price_per_1k": (NUM, False),
    "reasoning_tokens": (int, False),
    "cost": (NUM, False),               # buyer payment to seller = price_per_1k * tokens / 1000
    "fee": (NUM, False),                # gateway corridor fee/tariff, paid by buyer
    "latency_ms": (NUM, False),
    "answer": (int, True),
    "gold": (int, False),
    "correct": (bool, True),            # null when not served
    "status": (str, False),
    "rule_id": (str, True),             # compliance rule (blocked) or MKT-* reason (unfilled); null if allowed
    "buyer_surplus": (NUM, False),
    "seller_profit": (NUM, False),
    "verification_status": (str, False),
}
FIELDS: List[str] = list(SCHEMA)


def validate_record(rec: Dict) -> List[str]:
    errs = []
    for k, (types, nullable) in SCHEMA.items():
        if k not in rec:
            errs.append(f"missing field {k}")
            continue
        v = rec[k]
        if v is None:
            if not nullable:
                errs.append(f"{k} is null")
            continue
        if types is bool:
            ok = isinstance(v, bool)
        else:
            ok = isinstance(v, types) and not isinstance(v, bool)
        if not ok:
            errs.append(f"{k} has type {type(v).__name__}")
    extra = set(rec) - set(SCHEMA)
    if extra:
        errs.append(f"unexpected fields {sorted(extra)}")
    if rec.get("status") not in STATUSES:
        errs.append(f"bad status {rec.get('status')}")
    if rec.get("status") == "allowed" and rec.get("rule_id") is not None:
        errs.append("allowed tx must have rule_id null")
    if rec.get("status") in ("blocked", "unfilled") and rec.get("rule_id") is None:
        errs.append("blocked/unfilled tx must have rule_id")
    return errs


class TransactionLogger:
    def __init__(self, path: str, mode: str = "a"):
        self.path = path
        self._fh = open(path, mode, encoding="utf-8")
        self.count = 0

    def write(self, rec: Dict) -> None:
        errs = validate_record(rec)
        if errs:
            raise ValueError(f"invalid transaction record: {errs}")
        self._fh.write(json.dumps({k: rec[k] for k in FIELDS}, ensure_ascii=False) + "\n")
        self.count += 1

    def close(self) -> None:
        self._fh.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def read_log(path: str) -> List[Dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]
