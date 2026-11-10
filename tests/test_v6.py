"""v6 tests: delisting via market.audited.reputation_rounds, adaptive audit, escrow, audit trail."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tokenmarket.audit_v6 import (AdaptiveAuditAllocator, EscrowBook, d3_adaptive_audit,  # noqa: E402
                                  d3_escrow, d3_reputation_rounds)
from tokenmarket.config import load_config  # noqa: E402
from tokenmarket.logging_schema import FIELDS, validate_record  # noqa: E402
from tokenmarket.portfolio import AUDITED_POLICIES  # noqa: E402

from test_v3 import _run  # noqa: E402

SG = "seller_sg"


@pytest.fixture(scope="module")
def cfg():
    return load_config(os.path.join(ROOT, "configs", "default.yaml"))


def test_d3_config_helpers(cfg):
    assert d3_reputation_rounds(cfg, "audited_compliance_cascade", AUDITED_POLICIES) == 0
    assert d3_reputation_rounds(cfg, "single_best_compliant", AUDITED_POLICIES) == 0
    over = {"market": {"audited": {"reputation_rounds": 5, "adaptive_audit": True, "escrow": True}}}
    from tokenmarket.config import deep_merge
    c = deep_merge(cfg, over)
    assert d3_reputation_rounds(c, "audited_compliance_cascade", AUDITED_POLICIES) == 5
    assert d3_reputation_rounds(c, "single_best_compliant", AUDITED_POLICIES) == 0  # non-D3 ignores audited
    assert d3_adaptive_audit(c, "audited_compliance_cascade", AUDITED_POLICIES) is True
    assert d3_adaptive_audit(c, "pilot_compliant", AUDITED_POLICIES) is False
    assert d3_escrow(c, "audited_compliance_cascade", AUDITED_POLICIES) is True


def test_adaptive_allocator_budget():
    import random
    rng = random.Random(0)
    a = AdaptiveAuditAllocator(0.1, rng)
    n_audit = 0
    for i in range(1000):
        sid = f"s{i % 3}"
        score = a.score(sid, None, billed=200 if i % 3 == 0 else 100, actual=100)
        if a.decide(sid, score):
            n_audit += 1
            a.note_outcome(sid, detected_any=(i % 7 == 0))
    # long-run audit rate near target (credit tracks a·N)
    assert 0.05 < n_audit / 1000 < 0.18
    assert a.n_audits == n_audit


def test_escrow_slash_then_release():
    book = EscrowBook()
    h, r, s, cash = book.settle(1.0, audited=False, slash_amount=0.5)
    assert (h, r, s, cash) == (1.0, 1.0, 0.0, 1.0)
    h, r, s, cash = book.settle(1.0, audited=True, slash_amount=0.25)
    assert s == pytest.approx(0.25) and r == pytest.approx(0.75) and cash == pytest.approx(0.75)
    h, r, s, cash = book.settle(0.1, audited=True, slash_amount=0.5)
    assert s == pytest.approx(0.1) and r == pytest.approx(0.0) and cash == 0.0
    assert book.slashed == pytest.approx(0.35)


def test_schema_has_v6_fields():
    for k in ("purchase_id", "escrow_held", "escrow_released", "escrow_slashed", "ban_until"):
        assert k in FIELDS


def test_d3_delist_skips_banned(cfg):
    over = {"fraud": {"strategy": "static", "q_static": 1.0, "penalty": 0.3, "detect_prob": 1.0,
                      "attack_modes_enabled": ["swap"]},
            "market": {"budget_multiplier": 10.0,
                       "audited": {"audit_rate": 1.0, "reputation_rounds": 2,
                                   "adaptive_audit": False, "escrow": False,
                                   "audit_types": ["identity"]}}}
    m, recs, _ = _run(cfg, "audited_compliance_cascade", over, n_tasks=120, n_rounds=12)
    det = [r for r in recs if r.get("swap_detected")]
    assert det and m["n_bans"] > 0
    rounds = {r["round"] for r in det}
    for r in recs:
        if r["seller_id"] == SG and r["status"] == "allowed":
            assert not any(c < r["round"] <= c + 2 for c in rounds)
        if r.get("ban_until") is not None:
            assert r["ban_until"] == r["round"] + 1 + 2


def test_adaptive_and_escrow_plumbing(cfg):
    over = {"fraud": {"strategy": "learning", "attack_modes_enabled": ["swap", "theft"]},
            "market": {"budget_multiplier": 4.0,
                       "audited": {"audit_rate": 0.1, "adaptive_audit": True, "escrow": True,
                                   "reputation_rounds": 0}}}
    m, recs, _ = _run(cfg, "audited_compliance_cascade", over, n_tasks=240, n_rounds=24)
    served = [r for r in recs if r["status"] == "allowed"]
    assert served and all(validate_record(r) == [] for r in served[:5])
    assert m["adaptive_audit"] is True and m["escrow_enabled"] is True
    assert m["escrow_held_total"] > 0 and m["escrow_released_total"] > 0
    assert m["n_audits"] > 0 and len(m["audit_trail"]) == m["n_audits"]
    audited = [r for r in served if r["audited"]]
    assert audited and all(r["purchase_id"] for r in audited)
    # realized audit rate roughly near 0.1
    assert 0.03 < m["n_audits"] / max(1, m["n_purchases"]) < 0.25


def test_flags_off_backward_compatible_fields(cfg):
    """Defaults off: escrow zeros, no adaptive, schema still validates."""
    over = {"fraud": {"strategy": "static", "attack_modes_enabled": ["swap"]},
            "market": {"budget_multiplier": 4.0}}
    m, recs, _ = _run(cfg, "audited_compliance_cascade", over, n_tasks=80, n_rounds=8)
    assert m["adaptive_audit"] is False and m["escrow_enabled"] is False
    assert m["reputation_rounds"] == 0
    served = [r for r in recs if r["status"] == "allowed"]
    assert all(r["escrow_held"] == 0 and r["escrow_released"] == 0 for r in served)
    assert all(validate_record(r) == [] for r in served[:3])
