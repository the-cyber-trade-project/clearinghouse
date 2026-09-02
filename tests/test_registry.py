"""
Tests for TradeRegistry storage and Form FORM-001 evidentiary tracking.
"""

from cyber_trade_clearinghouse.registry import TradeRegistry
from cyber_trade_clearinghouse.models import PractitionerRecord, SafetyNonConcurrenceRecord


def test_practitioner_registration_and_lookup():
    reg = TradeRegistry()
    p = PractitionerRecord(
        trade_id="CTP-APP-2026-0884",
        name="Angela Moss",
        tier="Tier 2 Apprentice",
        license_status="Active",
        total_verified_hours=2100.0,
        active_endorsements=["SE-APP"]
    )
    reg.register_practitioner(p)

    retrieved = reg.get_practitioner("CTP-APP-2026-0884")
    assert retrieved is not None
    assert retrieved.name == "Angela Moss"
    assert retrieved.tier == "Tier 2 Apprentice"
    assert "SE-APP" in retrieved.active_endorsements


def test_safety_non_concurrence_recording():
    reg = TradeRegistry()
    rec = SafetyNonConcurrenceRecord(
        record_id="NSNC-2026-0001",
        timestamp="2026-08-20T10:00:00Z",
        submitting_mor_id="CTP-MST-2024-0004",
        enterprise_name="Apex Defense Systems",
        criticality_tier="Tier-I Critical Infrastructure",
        payload_hash="sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
        refusal_summary="Bypassed required air-gapped cryptographic validation in SCIF enclave.",
        executive_override_received=True,
        override_hash="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    reg.record_safety_non_concurrence(rec)

    item = reg.get_safety_non_concurrence("NSNC-2026-0001")
    assert item is not None
    assert item.submitting_mor_id == "CTP-MST-2024-0004"
    assert item.executive_override_received is True
