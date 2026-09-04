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

def test_all_tiers_dispatch_and_mor_requirements():
    reg = TradeRegistry()

    t1 = PractitionerRecord(
        trade_id="CTP-APP-T1",
        name="Tier 1 Candidate",
        tier="Tier 1 Apprentice",
        is_seeking_placement=True,
        days_seeking_placement=10,
    )
    t3 = PractitionerRecord(
        trade_id="CTP-APP-T3",
        name="Tier 3 Candidate",
        tier="Tier 3 Apprentice",
        is_seeking_placement=True,
        days_seeking_placement=15,
    )
    t4 = PractitionerRecord(
        trade_id="CTP-APP-T4",
        name="Tier 4 Candidate",
        tier="Tier 4 Apprentice",
        is_seeking_placement=True,
        days_seeking_placement=20,
    )
    mst_adv = PractitionerRecord(
        trade_id="CTP-MST-ADV",
        name="Master Advisory Only",
        tier="Master Practitioner",
        is_seeking_placement=True,
        days_seeking_placement=60,
        seeking_mor_role=False,
        mor_availability="Not Seeking MoR",
    )
    mst_mor_ft = PractitionerRecord(
        trade_id="CTP-MST-MOR-FT",
        name="Master Full-Time MoR",
        tier="Master Practitioner",
        is_seeking_placement=True,
        days_seeking_placement=35,
        seeking_mor_role=True,
        mor_availability="Full-Time MoR",
    )

    for p in [t1, t3, t4, mst_adv, mst_mor_ft]:
        reg.register_practitioner(p)

    # Requisition for Tier 3: must match t3
    req_t3 = DispatchRequisition(
        requisition_id="REQ-T3",
        employer_pec_id="PEC-EMP-001",
        required_tier="Tier 3 Apprentice",
    )
    res_t3 = reg.dispatch_candidate(req_t3)
    assert res_t3.matched is True
    assert res_t3.candidate.trade_id == "CTP-APP-T3"

    # Requisition for Tier 4: must match t4
    req_t4 = DispatchRequisition(
        requisition_id="REQ-T4",
        employer_pec_id="PEC-EMP-001",
        required_tier="Tier 4 Apprentice",
    )
    res_t4 = reg.dispatch_candidate(req_t4)
    assert res_t4.matched is True
    assert res_t4.candidate.trade_id == "CTP-APP-T4"

    # Requisition for Master without MoR flag: FIFO matches mst_adv (60 days)
    req_mst = DispatchRequisition(
        requisition_id="REQ-MST-GEN",
        employer_pec_id="PEC-EMP-001",
        required_tier="Master Practitioner",
        requires_mor=False,
    )
    res_mst = reg.dispatch_candidate(req_mst)
    assert res_mst.matched is True
    assert res_mst.candidate.trade_id == "CTP-MST-ADV"

    # Requisition for Full-Time MoR: ignores mst_adv
    req_mor_ft = DispatchRequisition(
        requisition_id="REQ-MOR-FT",
        employer_pec_id="PEC-EMP-001",
        required_tier="Master Practitioner",
        requires_mor=True,
        mor_engagement_type="Full-Time MoR",
    )
    res_mor_ft = reg.dispatch_candidate(req_mor_ft)
    assert res_mor_ft.matched is True
    assert res_mor_ft.candidate.trade_id == "CTP-MST-MOR-FT"


def test_dispatch_officer_intermediary_workflow():
    reg = TradeRegistry()

    emp = EmployerRecord(
        pec_id="PEC-EMP-2026-0042",
        name="Ellingson Mineral Corp",
        division="Tier-II Regulated Enterprise",
        designated_mor="Vacant",
        mor_status="Vacant",
        master_count=0,
        journeyman_count=4,
        apprentice_count=6,
        ratio_compliance_score=0.92,
        underwriter_tier="Tier B Standard",
    )
    reg.register_employer(emp)

    mor_candidate = PractitionerRecord(
        trade_id="CTP-MST-2024-0099",
        name="Kip Dawson",
        tier="Master Practitioner",
        is_seeking_placement=True,
        days_seeking_placement=45,
        seeking_mor_role=True,
        mor_availability="Full-Time MoR",
        assigned_jatc_local="LOCAL-101",
        dispatch_book="Book 1 (Resident)",
    )
    reg.register_practitioner(mor_candidate)
    assert mor_candidate.is_queue_aging_alert is True

    # Employer submits requisition to the Hall
    req = DispatchRequisition(
        requisition_id="REQ-2026-089",
        employer_pec_id="PEC-EMP-2026-0042",
        requisition_title="Master of Record for Multi-Cloud Operations",
        required_tier="Master Practitioner",
        requires_mor=True,
        mor_engagement_type="Full-Time MoR",
        target_local_id="LOCAL-101",
        status="PENDING_REVIEW",
    )
    reg.submit_requisition(req)

    # Dispatch Officer reviews the incoming requisition
    retrieved_req, matches, alerts = reg.officer_evaluate_requisition("REQ-2026-089")
    assert retrieved_req is not None
    assert len(matches) == 1
    assert matches[0].trade_id == "CTP-MST-2024-0099"
    assert any("AGING QUEUE ALERT" in a for a in alerts)

    # Dispatch Officer executes formal bilateral referral
    slip = reg.officer_execute_referral(
        requisition_id="REQ-2026-089",
        candidate_trade_id="CTP-MST-2024-0099",
        dispatching_officer_id="DISPATCH-OFFICER-LOCAL-101",
        referral_date="2026-09-03",
        notes="Bilateral call confirmed candidate accepted referral under standard JATC accord.",
    )

    assert slip.status == "ISSUED"
    assert slip.is_mor_designation is True
    assert slip.candidate_name == "Kip Dawson"
    assert slip.wage_step_percentage == 135

    assert req.status == "REFERRED"
    assert req.dispatched_trade_id == "CTP-MST-2024-0099"
    assert mor_candidate.is_seeking_placement is False
    assert mor_candidate.sponsoring_pec_id == "PEC-EMP-2026-0042"
    assert mor_candidate.sponsoring_employer == "Ellingson Mineral Corp"

