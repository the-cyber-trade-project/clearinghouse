"""
Tests for Regional Locals, Employer Directory, and FIFO Out-of-Work Dispatch matching.
"""

from cyber_trade_clearinghouse.registry import TradeRegistry
from cyber_trade_clearinghouse.models import (
    PractitionerRecord,
    RegionalLocalRecord,
    EmployerRecord,
    DispatchRequisition,
)


def test_locals_and_employers_registration():
    reg = TradeRegistry()

    loc = RegionalLocalRecord(
        local_id="LOCAL-101",
        name="Local 101 - Mid-Atlantic Hub",
        jurisdiction_territory="District 1",
        coli_zone_tier="Tier A (High COLI)",
        rjpb_hourly_base=85.00,
        active_apprentice_count=10,
        active_journeyman_count=20
    )
    reg.register_local(loc)
    assert reg.get_local("LOCAL-101").rjpb_hourly_base == 85.00

    emp = EmployerRecord(
        pec_id="PEC-EMP-2026-0001",
        name="Arasaka Defense Systems",
        division="Tier-I Critical Infrastructure",
        local_chapter_id="LOCAL-302",
        designated_mor="Alt Cunningham",
        journeyman_count=6,
        apprentice_count=12,
        ratio_compliance_score=0.984,
        underwriter_tier="Tier A Preferred Risk",
        total_verified_hours=38400.0
    )
    reg.register_employer(emp)
    assert reg.get_employer("PEC-EMP-2026-0001").ratio_compliance_score == 0.984


def test_fifo_dispatch_seniority():
    reg = TradeRegistry()

    # Candidate A: Waiting 14 days
    p_a = PractitionerRecord(
        trade_id="CTP-APP-A",
        name="Dade Murphy",
        tier="Tier 2 Apprentice",
        assigned_jatc_local="LOCAL-101",
        active_endorsements=["SE-APP"],
        is_seeking_placement=True,
        days_seeking_placement=14,
        work_modality_preference="Hybrid"
    )

    # Candidate B: Waiting 42 days (Senior FIFO candidate)
    p_b = PractitionerRecord(
        trade_id="CTP-APP-B",
        name="Senior Candidate",
        tier="Tier 2 Apprentice",
        assigned_jatc_local="LOCAL-101",
        active_endorsements=["SE-APP"],
        is_seeking_placement=True,
        days_seeking_placement=42,
        work_modality_preference="Hybrid"
    )

    reg.register_practitioner(p_a)
    reg.register_practitioner(p_b)

    # Requisition for Tier 2 Apprentice with SE-APP
    req = DispatchRequisition(
        requisition_id="REQ-001",
        employer_pec_id="PEC-EMP-2026-0042",
        required_tier="Tier 2 Apprentice",
        required_endorsement="SE-APP",
        target_local_id="LOCAL-101",
        work_modality="Hybrid"
    )

    res = reg.dispatch_candidate(req)
    assert res.matched is True
    # Verify that Candidate B (42 days) was dispatched before Candidate A (14 days)
    assert res.candidate.trade_id == "CTP-APP-B"
    assert res.candidate.days_seeking_placement == 42
