"""
Tests for Regional Locals, Employer Directory, and Practitioner Registration in the NCTB Registry.
"""

from cyber_trade_clearinghouse.registry import TradeRegistry
from cyber_trade_clearinghouse.models import (
    PractitionerRecord,
    RegionalLocalRecord,
    EmployerRecord,
)


def test_locals_and_employers_registration():
    reg = TradeRegistry()

    loc = RegionalLocalRecord(
        local_id="LOCAL-101",
        name="Local 101 - Mid-Atlantic Hub",
        jurisdiction_territory="District 1",
        coli_zone_tier="Tier A (High COLI)",
        zone_1_rate=85.00,
        active_apprentice_count=10,
        active_journeyman_count=20
    )
    reg.register_local(loc)
    assert reg.get_local("LOCAL-101").rjpb_hourly_base == 85.00

    emp = EmployerRecord(
        pec_id="PEC-EMP-2026-0001",
        name="Arasaka Defense Systems",
        division="Tier-I Critical Infrastructure",
        operating_hubs="Multi-District (Locals 101, 204, 302)",
        designated_mor="Alt Cunningham",
        designated_mor_id="CTP-MST-2024-0004",
        mor_status="Full-Time MoR",
        master_count=2,
        journeyman_count=6,
        apprentice_count=12,
        ratio_compliance_score=0.984,
        underwriter_tier="Tier A Preferred Risk",
        total_verified_hours=38400.0
    )
    reg.register_employer(emp)
    assert reg.get_employer("PEC-EMP-2026-0001").ratio_compliance_score == 0.984


def test_get_employer_compliance_manifest():
    reg = TradeRegistry()

    emp = EmployerRecord(
        pec_id="PEC-EMP-2026-0001",
        name="Apex Defense Systems",
        division="Tier-I Critical Infrastructure",
        designated_mor="Dade Murphy",
        designated_mor_id="CTP-MST-2024-0001",
        mor_status="Full-Time MoR",
        master_count=2,
        journeyman_count=8,
        apprentice_count=14,
        ratio_compliance_score=0.985,
        underwriter_tier="Tier A Preferred Risk (35% Credit)",
        total_verified_hours=42000.0,
    )
    reg.register_employer(emp)

    manifest = reg.get_employer_compliance_manifest("PEC-EMP-2026-0001")
    assert manifest is not None
    assert manifest["pec_id"] == "PEC-EMP-2026-0001"
    assert manifest["active_mor"] is True
    assert manifest["designated_mor"] == "Dade Murphy"
    assert manifest["supervisory_ratio_compliance_score"] == 0.985
    assert manifest["unresolved_safety_non_concurrences"] == 0
