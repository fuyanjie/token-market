"""Data-driven cross-border data-transfer rules.

!!! SIMPLIFIED SIMULATION — NOT LEGAL ADVICE !!!
Rule IDs reference real statutes (CN PIPL / DSL, SG PDPA, BR LGPD) only as labels; the
conditions are stylised abstractions for research on market design, not legal analysis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

DISCLAIMER = "Simplified simulation of data-transfer rules; NOT legal advice."


@dataclass
class Rule:
    rule_id: str
    description: str
    origin: str                      # buyer jurisdiction or "ANY"
    sensitivity: List[str]
    type: str                        # "allow" | "require"
    allow_if: Dict = field(default_factory=dict)
    scope: str = "cross_border"      # "cross_border" | "all"

    def matches(self, origin: str, sensitivity: str, cross_border: bool) -> bool:
        if self.scope == "cross_border" and not cross_border:
            return False
        return (self.origin in ("ANY", origin)) and sensitivity in self.sensitivity


@dataclass
class Decision:
    allowed: bool
    rule_id: Optional[str]           # blocking rule; None if allowed
    matched: List[str] = field(default_factory=list)


class ComplianceEngine:
    def __init__(self, rules: List[Rule], adequacy: Dict[str, List[str]]):
        self.rules = rules
        self.adequacy = adequacy

    @classmethod
    def from_config(cls, cfg: Dict) -> "ComplianceEngine":
        c = cfg["compliance"]
        rules = [Rule(rule_id=r["rule_id"], description=r.get("description", ""),
                      origin=r["origin"], sensitivity=list(r["sensitivity"]), type=r["type"],
                      allow_if=dict(r.get("allow_if", {})), scope=r.get("scope", "cross_border"))
                 for r in c["rules"]]
        return cls(rules, {k: list(v) for k, v in c.get("adequacy", {}).items()})

    def _condition_holds(self, rule: Rule, origin: str, dest: str,
                         seller_flags: List[str], task_flags: List[str]) -> bool:
        cond = rule.allow_if
        if cond.get("dest_in_adequacy") and dest in self.adequacy.get(origin, []):
            return True
        if set(cond.get("seller_flags_any", [])) & set(seller_flags):
            return True
        need = cond.get("task_flags_all")
        if need and set(need) <= set(task_flags):
            return True
        return False

    def evaluate(self, origin: str, dest: str, sensitivity: str,
                 seller_flags: List[str], task_flags: List[str]) -> Decision:
        cross_border = origin != dest
        matched = []
        for rule in self.rules:
            if not rule.matches(origin, sensitivity, cross_border):
                continue
            matched.append(rule.rule_id)
            if rule.type == "allow":
                return Decision(True, None, matched)
            if rule.type == "require" and not self._condition_holds(rule, origin, dest, seller_flags, task_flags):
                return Decision(False, rule.rule_id, matched)
        return Decision(True, None, matched)

    def evaluate_flow(self, buyer, seller, task) -> Decision:
        return self.evaluate(buyer.jurisdiction, seller.jurisdiction, task.sensitivity,
                             seller.flags, task.flags)

    def rule_table(self) -> List[Dict]:
        return [{"rule_id": r.rule_id, "origin": r.origin, "sensitivity": r.sensitivity,
                 "type": r.type, "allow_if": r.allow_if, "description": r.description}
                for r in self.rules]
