"""Cross-border gateway: enforces compliance, applies corridor latency penalty and fee/tariff."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, Optional

from .compliance import ComplianceEngine, Decision


@dataclass
class GatewayResult:
    allowed: bool
    rule_id: Optional[str]
    cross_border: bool
    corridor: str
    latency_penalty_ms: float
    fee_rate: float
    violation: bool = False          # audit_only mode: flow breaches a rule but was let through


class CrossBorderGateway:
    """mode='enforce': violating flows are BLOCKED. mode='audit_only': violating flows pass (status allowed)
    but are flagged violation=True with the breached rule_id - used for the compliance-unaware baseline to
    count what would happen without hard constraints."""

    MODES = ("enforce", "audit_only")

    def __init__(self, engine: ComplianceEngine, cfg: Dict, mode: str = "enforce"):
        if mode not in self.MODES:
            raise ValueError(f"unknown gateway mode {mode}")
        g = cfg.get("gateway", {})
        self.mode = mode
        self.engine = engine
        self.default = g.get("default_cross_border", {"latency_penalty_ms": 0, "fee_rate": 0.0})
        self.corridors = g.get("corridors", {})
        self.allowed_counts: Counter = Counter()
        self.blocked_counts: Counter = Counter()
        self.violation_counts: Counter = Counter()

    def corridor_params(self, origin: str, dest: str):
        if origin == dest:
            return 0.0, 0.0
        c = self.corridors.get(f"{origin}->{dest}", self.default)
        return float(c["latency_penalty_ms"]), float(c["fee_rate"])

    def would_allow(self, buyer, seller, task) -> Decision:
        """Side-effect-free pre-check (hard-constraint filter used by *_compliant policies)."""
        return self.engine.evaluate_flow(buyer, seller, task)

    def route(self, buyer, seller, task) -> GatewayResult:
        corridor = f"{buyer.jurisdiction}->{seller.jurisdiction}"
        d = self.engine.evaluate_flow(buyer, seller, task)
        pen, fee = self.corridor_params(buyer.jurisdiction, seller.jurisdiction)
        cb = buyer.jurisdiction != seller.jurisdiction
        if d.allowed:
            self.allowed_counts[corridor] += 1
            return GatewayResult(True, None, cb, corridor, pen, fee)
        if self.mode == "audit_only":
            self.allowed_counts[corridor] += 1
            self.violation_counts[corridor] += 1
            return GatewayResult(True, d.rule_id, cb, corridor, pen, fee, violation=True)
        self.blocked_counts[corridor] += 1
        return GatewayResult(False, d.rule_id, cb, corridor, pen, fee)

    def stats(self) -> Dict:
        return {"allowed": dict(self.allowed_counts), "blocked": dict(self.blocked_counts),
                "allowed_total": sum(self.allowed_counts.values()),
                "blocked_total": sum(self.blocked_counts.values()),
                "violations": dict(self.violation_counts),
                "violations_total": sum(self.violation_counts.values())}
