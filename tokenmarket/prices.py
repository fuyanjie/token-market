"""v1.0 public API price table loader (configs/v1.0/prices.yaml, protocol §7)."""
from __future__ import annotations

from typing import Dict, List

import yaml


def load_prices(path: str = "configs/v1.0/prices.yaml") -> Dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def verified_rows(table: Dict) -> List[Dict]:
    """Flat list of rows with a published (non-null) output price: provider, model, input/output per 1K, source."""
    out = []
    for prov, p in (table.get("providers") or {}).items():
        for model, r in (p.get("models") or {}).items():
            if r.get("output") is None or r.get("input") is None:
                continue
            out.append({"provider": prov, "model": model, "input_per_1k": float(r["input"]),
                        "output_per_1k": float(r["output"]), "source_url": p["source_url"],
                        "accessed": p["accessed"]})
    return out


def output_price_ratio(table: Dict, strong: str, cheap: str) -> float:
    rows = {r["model"]: r for r in verified_rows(table)}
    return rows[strong]["output_per_1k"] / rows[cheap]["output_per_1k"]
