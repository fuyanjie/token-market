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


class CrossBorderGateway:
    def __init__(self, engine: ComplianceEngine, cfg: Dict):
        g = cfg.get("gateway", {})
        self.engine = engine
        self.default = g.get("default_cross_border", {"latency_penalty_ms": 0, "fee_rate": 0.0})
        self.corridors = g.get("corridors", {})
        self.allowed_counts: Counter = Counter()
        self.blocked_counts: Counter = Counter()

    def corridor_params(self, origin: str, dest: str):
        if origin == dest:
            return 0.0, 0.0
        c = self.corridors.get(f"{origin}->{dest}", self.default)
        return float(c["latency_penalty_ms"]), float(c["fee_rate"])

    def would_allow(self, buyer, seller, task) -> Decision:
        """Side-effect-free pre-check (used by compliance_aware routing)."""
        return self.engine.evaluate_flow(buyer, seller, task)

    def route(self, buyer, seller, task) -> GatewayResult:
        corridor = f"{buyer.jurisdiction}->{seller.jurisdiction}"
        d = self.engine.evaluate_flow(buyer, seller, task)
        pen, fee = self.corridor_params(buyer.jurisdiction, seller.jurisdiction)
        (self.allowed_counts if d.allowed else self.blocked_counts)[corridor] += 1
        return GatewayResult(d.allowed, d.rule_id, buyer.jurisdiction != seller.jurisdiction,
                             corridor, pen, fee)

    def stats(self) -> Dict:
        return {"allowed": dict(self.allowed_counts), "blocked": dict(self.blocked_counts),
                "allowed_total": sum(self.allowed_counts.values()),
                "blocked_total": sum(self.blocked_counts.values())}
