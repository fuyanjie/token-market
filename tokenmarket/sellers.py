"""Seller agents: jurisdiction, claimed vs. actual model, pricing, latency, capacity."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Seller:
    id: str
    jurisdiction: str
    claimed_model: str
    actual_model: str
    price_per_1k: float
    cost_per_1k: float
    latency_mean_ms: float
    latency_std_ms: float
    capacity_per_round: int
    advertised_accuracy: float
    reasoning_effort: float = 1.0
    flags: List[str] = field(default_factory=list)
    used_this_round: int = 0

    @classmethod
    def from_config(cls, d: Dict) -> "Seller":
        qp = d.get("quality_profile", {})
        return cls(
            id=d["id"],
            jurisdiction=d["jurisdiction"],
            claimed_model=d["claimed_model"],
            actual_model=d["actual_model"],
            price_per_1k=float(d["price_per_1k"]),
            cost_per_1k=float(d["cost_per_1k"]),
            latency_mean_ms=float(d["latency"]["mean_ms"]),
            latency_std_ms=float(d["latency"]["std_ms"]),
            capacity_per_round=int(d["capacity_per_round"]),
            advertised_accuracy=float(qp.get("advertised_accuracy", 0.5)),
            reasoning_effort=float(qp.get("reasoning_effort", 1.0)),
            flags=list(d.get("flags", [])),
        )

    @property
    def is_model_swap(self) -> bool:
        return self.claimed_model != self.actual_model

    def has_capacity(self) -> bool:
        return self.used_this_round < self.capacity_per_round

    def reset_round(self) -> None:
        self.used_this_round = 0

    def sample_latency(self, rng: random.Random) -> float:
        return max(50.0, rng.gauss(self.latency_mean_ms, self.latency_std_ms))

    def sample_bid(self, rng: random.Random, markup_low: float, markup_high: float) -> float:
        """Sealed bid per 1K tokens = cost * random markup."""
        return self.cost_per_1k * rng.uniform(markup_low, markup_high)


def load_sellers(cfg: Dict) -> List[Seller]:
    return [Seller.from_config(s) for s in cfg["sellers"]]
