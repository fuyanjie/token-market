"""Seller agents (jurisdiction, claimed vs. actual model, backend, pricing, latency, capacity) and model reputation."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
    backend: str = "mock"            # mock | local_hf | real
    reasoning_effort: float = 1.0
    flags: List[str] = field(default_factory=list)
    used_this_round: int = 0
    # v3 strategic model-swap seller: serves honest_model (= claimed) with prob 1-q, actual_model with prob q
    honest_model: Optional[str] = None
    honest_cost_per_1k: Optional[float] = None
    strategy: Optional[object] = None          # strategic.SwapStrategy (None for honest sellers)
    banned_until_round: int = 0               # delisted (no demand) before this round after being caught
    stake_slashed: float = 0.0

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
            backend=str(d.get("backend", "mock")),
            reasoning_effort=float(qp.get("reasoning_effort", 1.0)),
            flags=list(d.get("flags", [])),
            honest_model=d.get("strategy", {}).get("honest_model", d["claimed_model"]),
            honest_cost_per_1k=float(d.get("strategy", {}).get("honest_cost_per_1k", d["cost_per_1k"])),
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


def load_sellers(cfg: Dict, backend_override: Optional[str] = None) -> List[Seller]:
    sellers = [Seller.from_config(s) for s in cfg["sellers"]]
    if backend_override:
        for s in sellers:
            s.backend = backend_override
    return sellers


class Reputation:
    """Public model reputation used by buyers for routing and expected-cost estimates. Indexed by the
    CLAIMED model, so a model-swap seller inherits the claimed model's reputation (links C2 to B2).
    Measured stats (from the precompute stage) override config priors when available."""

    def __init__(self, models: Dict, measured: Optional[Dict[str, Dict]] = None):
        self.models = models
        self.measured = measured or {}

    def accuracy(self, model: str, difficulty: int) -> float:
        m = self.measured.get(model)
        if m and difficulty in m.get("by_difficulty", {}):
            return float(m["by_difficulty"][difficulty]["accuracy"])
        return float(self.models[model]["accuracy"][difficulty])

    def tokens_mean(self, model: str) -> float:
        """Advertised expected reasoning tokens per request (difficulty-agnostic)."""
        m = self.measured.get(model)
        if m:
            return float(m["tokens_mean"])
        p = self.models[model]
        return float(p.get("advertised_tokens", p["tokens_mean"]))

    def source(self, model: str) -> str:
        return "measured" if model in self.measured else "config_prior"
