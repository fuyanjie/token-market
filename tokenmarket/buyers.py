"""Buyer agents: jurisdiction, budget, allowed jurisdictions, value per correct answer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Buyer:
    id: str
    jurisdiction: str
    budget: float
    value_per_correct: float
    allowed_jurisdictions: List[str]
    sensitivity_mix: Dict[str, float]
    consent_rate: float = 0.0
    spent: float = field(default=0.0)

    @classmethod
    def from_config(cls, d: Dict) -> "Buyer":
        return cls(
            id=d["id"],
            jurisdiction=d["jurisdiction"],
            budget=float(d["budget"]),
            value_per_correct=float(d["value_per_correct"]),
            allowed_jurisdictions=list(d["allowed_jurisdictions"]),
            sensitivity_mix=dict(d["sensitivity_mix"]),
            consent_rate=float(d.get("consent_rate", 0.0)),
        )

    @property
    def remaining(self) -> float:
        return self.budget - self.spent

    def can_afford(self, expected_cost: float) -> bool:
        return self.remaining >= expected_cost


def load_buyers(cfg: Dict) -> List[Buyer]:
    return [Buyer.from_config(b) for b in cfg["buyers"]]
