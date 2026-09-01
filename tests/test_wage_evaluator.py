"""
Tests for 8,000-hour domain math, wage steps, and statutory elevation seals.
"""

from cyber_trade_clearinghouse.wage_evaluator import WageStepEvaluator


def test_wage_step_tiers():
    t1 = WageStepEvaluator.determine_tier(1500.0)
    assert t1["tier_level"] == 1
    assert t1["wage_step_percentage"] == 50
    assert t1["is_journeyman_eligible"] is False

    t2 = WageStepEvaluator.determine_tier(2500.0)
    assert t2["tier_level"] == 2
    assert t2["wage_step_percentage"] == 60
    assert t2["tier_name"] == "Progressing Registered Apprentice (Tier 2)"

    t3 = WageStepEvaluator.determine_tier(4500.0)
    assert t3["tier_level"] == 3
    assert t3["wage_step_percentage"] == 70
    assert t3["tier_name"] == "Intermediate Registered Apprentice (Tier 3)"

    t4 = WageStepEvaluator.determine_tier(6500.0)
    assert t4["tier_level"] == 4
    assert t4["wage_step_percentage"] == 80
    assert t4["tier_name"] == "Advanced Registered Apprentice (Tier 4)"

    t5 = WageStepEvaluator.determine_tier(8050.0)
    assert t5["tier_level"] == 5
    assert t5["wage_step_percentage"] == 100
    assert t5["is_journeyman_eligible"] is True
    assert t5["tier_name"] == "Licensed Journeyman"

    t6 = WageStepEvaluator.determine_tier(12500.0)
    assert t6["tier_level"] == 6
    assert t6["wage_step_percentage"] == 135
    assert t6["is_journeyman_eligible"] is True
    assert "Master Practitioner" in t6["tier_name"]


def test_issue_elevation_seal():
    seal = WageStepEvaluator.issue_elevation_seal(
        practitioner_id="CTP-APP-2026-0001",
        total_hours=4200.0,
        domain_breakdown={"D1_PERIMETER_CLOUD": 1200.0, "D2_DETECTION_SOC": 3000.0}
    )
    assert seal.elevated_tier == "Intermediate Registered Apprentice (Tier 3)"
    assert seal.wage_step_percentage == 70
    assert seal.total_verified_hours == 4200.0
    assert seal.seal_id.startswith("SEAL-")
