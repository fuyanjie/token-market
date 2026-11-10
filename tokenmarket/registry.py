"""v1.0 method registry (protocol §3): every buyer-side method is a name -> (policy id, config overrides, label).

Labels follow the protocol: D3 is reported as the "fixed-rate audit reference baseline", never as "our method"; the
old ids (d3, audited_compliance_cascade) are kept as ALIASES of fixed_audit_a0.10. See docs/BASELINES_v1.0.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .config import deep_merge


@dataclass(frozen=True)
class Method:
    name: str
    policy: str
    label: str
    over: Dict = field(default_factory=dict)
    family: str = "router"          # router | fixed_router | audit
    note: str = ""


def _audit(rate: float, rule: str = "fixed") -> Dict:
    return {"market": {"audited": {"audit_rate": float(rate), "audit_rule": rule, "adaptive_audit": False,
                                   "escrow": False}}}


_METHODS: List[Method] = [
    Method("pilot", "pilot_v1_compliant", "PILOT (Panda et al. 2025), faithful reimpl.",
           note="LinUCB + preference prior + ZCL ON-MCKP binning (Alg. 3); compliance filter on"),
    Method("stageroute", "stageroute_v1_compliant", "StageRoute (Li & Li 2025), faithful reimpl. incl. MIP",
           note="stage-wise DeployOPT MIP + per-query RouteOPT LP; compliance filter on"),
    Method("pilot_v01", "pilot_compliant", "PILOT, v0.1 simplified reimpl.", note="v0.1 numbers"),
    Method("stageroute_v01", "stageroute_compliant", "StageRoute, v0.1 simplified reimpl. (no MIP)",
           note="v0.1 numbers"),
    Method("cheapest_fixed", "single_cheapest_compliant", "cheapest fixed router", family="fixed_router"),
    Method("strongest_fixed", "single_best_compliant", "strongest fixed router (highest listed quality)",
           family="fixed_router"),
    Method("random_audit", "audited_compliance_cascade", "random-intensity audit (a_t ~ U(0, 0.2))",
           _audit(0.1, "random"), family="audit"),
    Method("fixed_audit_a0.05", "audited_compliance_cascade", "fixed-rate audit reference baseline (a=0.05)",
           _audit(0.05), family="audit"),
    Method("fixed_audit_a0.10", "audited_compliance_cascade", "fixed-rate audit reference baseline (a=0.10)",
           _audit(0.10), family="audit"),
    Method("fixed_audit_a0.20", "audited_compliance_cascade", "fixed-rate audit reference baseline (a=0.20)",
           _audit(0.20), family="audit"),
    Method("audited_cascade_unfiltered", "audited_cascade_unfiltered",
           "fixed-rate audit reference baseline (a=0.10) WITHOUT the compliance hard filter (A2)",
           _audit(0.10), family="audit",
           note="D3 control flow, no hard compliance filter; gateway in market.unaware_gateway_mode (protocol §6)"),
    Method("risk_adaptive_audit", "audited_compliance_cascade",
           "risk-adaptive audit (a_s = 0.05 + 0.45 q_hat_s)", _audit(0.1, "risk_adaptive"), family="audit"),
]
METHODS: Dict[str, Method] = {m.name: m for m in _METHODS}
ALIASES: Dict[str, str] = {"d3": "fixed_audit_a0.10", "D3": "fixed_audit_a0.10",
                           "audited_compliance_cascade": "fixed_audit_a0.10",
                           "fixed_audit": "fixed_audit_a0.10",
                           "d3_unfiltered": "audited_cascade_unfiltered"}
DEFAULT_MAIN_TABLE = ["pilot", "stageroute", "cheapest_fixed", "strongest_fixed", "random_audit",
                      "fixed_audit_a0.05", "fixed_audit_a0.10", "fixed_audit_a0.20", "risk_adaptive_audit"]


def resolve(name: str) -> Method:
    key = ALIASES.get(name, name)
    if key not in METHODS:
        raise KeyError(f"unknown method {name!r}; known: {sorted(METHODS)} (aliases {sorted(ALIASES)})")
    return METHODS[key]


def method_config(cfg: Dict, name: str) -> Dict:
    return deep_merge(cfg, resolve(name).over)


def list_methods() -> List[str]:
    return list(METHODS)
