"""Unified transaction log schema (v2 + v3 audit fields + v4 token-theft / imperfect-detection fields
+ v5 outcome-feedback fields).

Exactly ONE JSONL line per transaction = one individual seller purchase attempt (allowed or blocked), or one
`unfilled` line for a task where no purchase was made. Inside a cascade / vote portfolio every seller purchase is
its own line (portfolio_step = 0, 1, 2 ...). The LAST line of every task has final=true and carries the
portfolio's final decision (final_answer / final_correct); all other lines have final=false and null finals.
Summing buyer_surplus over a task's lines gives the task's surplus (value is credited on the final line)."""
from __future__ import annotations

import json
from typing import Dict, List

NUM = (int, float)
STATUSES = ("allowed", "blocked", "unfilled")
ATTACK_MODES = ("none", "swap", "theft", "both")
AUDIT_TYPES = ("none", "identity", "length", "both")

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
    "task_id": (str, False),            # task instance id, unique within a run: t<k>_<pool id>
    "pool_task_id": (str, False),       # id in the fixed task pool (cache key is the prompt hash)
    "portfolio_step": (int, False),     # 0-based index of this purchase within the task's portfolio
    "task_type": (str, False),
    "difficulty": (int, False),
    "sensitivity": (str, False),
    "seller_id": (str, True),           # null when unfilled
    "seller_jurisdiction": (str, True),
    "claimed_model": (str, True),
    "actual_model": (str, True),
    "backend": (str, True),             # seller backend that served it: local_hf | mock | real (null if unfilled)
    "cross_border": (bool, False),
    "price_per_1k": (NUM, False),
    "reasoning_tokens": (int, False),   # tokens ACTUALLY generated (== actual_tokens; 0 if not served)
    "cost": (NUM, False),               # buyer payment to seller = price_per_1k * BILLED tokens / 1000
    "fee": (NUM, False),                # gateway corridor fee/tariff, paid by buyer
    "expected_cost": (NUM, False),      # pre-purchase: price * advertised tokens (claimed model) / 1000 * (1+fee_rate)
    "actual_cost": (NUM, False),        # realised buyer outlay = cost + fee (0 if not served)
    "cost_overrun": (NUM, False),       # actual_cost - expected_cost (0 if not served)
    "budget_remaining": (NUM, False),   # buyer budget - realised spend AFTER this line (may be < 0)
    "budget_overrun": (bool, False),    # realised spend exceeds the buyer's budget after this line
    "latency_ms": (NUM, False),
    "answer": (int, True),
    "gold": (int, False),
    "correct": (bool, True),            # null when not served
    "confidence": (NUM, True),          # seller-side confidence signal of this answer (null if not served)
    "status": (str, False),
    "violation": (bool, False),         # flow crossed a border in breach of a rule (only possible in audit_only mode)
    "rule_id": (str, True),             # blocked: blocking rule; allowed+violation: breached rule; unfilled: MKT-*
    "final": (bool, False),             # last line of the task: carries the portfolio decision
    "final_answer": (int, True),        # final==true only (null if no answer)
    "final_correct": (bool, True),      # final==true only; false if the task got no answer
    "buyer_surplus": (NUM, False),
    "seller_profit": (NUM, False),
    "verification_status": (str, False),
    # v3: buyer audits / strategic model-swap seller
    "audited": (bool, False),           # this purchase was audited (identity check) by the buyer
    "audit_cost": (NUM, False),         # audit fee charged to the buyer budget (0 if not audited)
    "swap_detected": (bool, True),      # audit outcome; null if not audited
    "swap_prob": (NUM, True),           # seller's current swap probability q (0 honest; null if unfilled)
    # v4: token theft + imperfect detection
    "billed_tokens": (int, False),      # tokens the buyer is billed for (== actual unless token theft)
    "actual_tokens": (int, False),      # tokens actually generated (alias of reasoning_tokens)
    "token_inflation": (NUM, True),     # billed / actual (1.0 honest; null if not served)
    "attack_mode": (str, True),         # realised attack on this purchase: none|swap|theft|both (null if not served)
    "theft_prob": (NUM, True),          # seller's current theft probability q_theft (0 honest; null if unfilled)
    "audit_type": (str, False),         # checks run on this purchase: none|identity|length|both
    "theft_detected": (bool, True),     # length-audit outcome; null if no length check ran
    "detect_prob_identity": (NUM, True),  # identity-check detection prob d of the buyer's audit regime (null: no such check)
    "detect_prob_length": (NUM, True),    # length-audit detection prob d_length (null: no such check)
    # v5: outcome (correctness) feedback channel for online learners; audits are independent of it
    "feedback_delay_L": (int, True),      # label delay L of the run's feedback regime (null: L = inf / never)
    "feedback_revealed": (bool, False),   # this purchase's correctness label is ever revealed (prob pi; false if not served)
    "feedback_delivered_at": (int, True),  # step (task index) the label is delivered; n_tasks = end-of-episode flush; null: never
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
    if rec.get("status") == "allowed" and not rec.get("violation") and rec.get("rule_id") is not None:
        errs.append("allowed non-violating tx must have rule_id null")
    if rec.get("violation") and (rec.get("status") != "allowed" or rec.get("rule_id") is None):
        errs.append("violation=true requires status allowed and the breached rule_id")
    if rec.get("status") in ("blocked", "unfilled") and rec.get("rule_id") is None:
        errs.append("blocked/unfilled tx must have rule_id")
    if not rec.get("final") and (rec.get("final_answer") is not None or rec.get("final_correct") is not None):
        errs.append("final_answer/final_correct only allowed on final=true lines")
    if rec.get("attack_mode") is not None and rec["attack_mode"] not in ATTACK_MODES:
        errs.append(f"bad attack_mode {rec['attack_mode']}")
    if rec.get("audit_type") is not None and rec["audit_type"] not in AUDIT_TYPES:
        errs.append(f"bad audit_type {rec['audit_type']}")
    if isinstance(rec.get("billed_tokens"), int) and isinstance(rec.get("actual_tokens"), int) \
            and rec["billed_tokens"] < rec["actual_tokens"]:
        errs.append("billed_tokens < actual_tokens")
    if rec.get("feedback_delivered_at") is not None and not rec.get("feedback_revealed"):
        errs.append("feedback_delivered_at requires feedback_revealed")
    if rec.get("final") and rec.get("final_correct") is None:
        errs.append("final line must set final_correct")
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
