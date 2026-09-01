"""
Wage Step Elevation & 8,000-Hour Apprenticeship Domain Math Evaluator.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from cyber_trade_clearinghouse.models import WageElevationSeal


class WageStepEvaluator:
    """
    Evaluates verified operational runtime hours against the 8,000-hour statutory baseline:
    - Domain 1: Perimeter, Cloud & Network Defense (1,500 hrs)
    - Domain 2: Detection Engineering & Incident Triage (2,000 hrs)
    - Domain 3: Identity, Credential & Access Management (1,500 hrs)
    - Domain 4: Vulnerability & Attack Surface Management (1,500 hrs)
    - Domain 5: Defensive Governance, Risk & Audit (1,500 hrs)

    Wage Step Percentage Floors:
    - Tier 1 (0 to 1,999 hrs): 50% of RJPB
    - Tier 2 (2,000 to 3,999 hrs): 60% of RJPB
    - Tier 3 (4,000 to 5,999 hrs): 70% of RJPB
    - Tier 4 (6,000 to 7,999 hrs): 80% of RJPB
    - Journeyman Licensure (8,000+ hrs): 100% of RJPB
    """

    DOMAIN_BENCHMARKS = {
        "D1_PERIMETER_CLOUD": 1500.0,
        "D2_DETECTION_SOC": 2000.0,
        "D3_IDENTITY_IAM": 1500.0,
        "D4_VULN_ATTACK": 1500.0,
        "D5_DEFENSIVE_GRC": 1500.0,
    }

    PLA_CAP_HOURS = 2000.0

    @classmethod
    def determine_tier(cls, total_hours: float) -> Dict[str, Any]:
        if total_hours >= 8000.0:
            return {
                "tier_name": "Licensed Journeyman",
                "wage_step_percentage": 100,
                "tier_level": 5,
                "is_journeyman_eligible": True,
                "hours_to_next": 0.0
            }
        elif total_hours >= 6000.0:
            return {
                "tier_name": "Senior Apprentice (Tier 4)",
                "wage_step_percentage": 80,
                "tier_level": 4,
                "is_journeyman_eligible": False,
                "hours_to_next": 8000.0 - total_hours
            }
        elif total_hours >= 4000.0:
            return {
                "tier_name": "Intermediate Apprentice (Tier 3)",
                "wage_step_percentage": 70,
                "tier_level": 3,
                "is_journeyman_eligible": False,
                "hours_to_next": 6000.0 - total_hours
            }
        elif total_hours >= 2000.0:
            return {
                "tier_name": "Developing Apprentice (Tier 2)",
                "wage_step_percentage": 60,
                "tier_level": 2,
                "is_journeyman_eligible": False,
                "hours_to_next": 4000.0 - total_hours
            }
        else:
            return {
                "tier_name": "Entry Registered Apprentice (Tier 1)",
                "wage_step_percentage": 50,
                "tier_level": 1,
                "is_journeyman_eligible": False,
                "hours_to_next": 2000.0 - total_hours
            }

    @classmethod
    def issue_elevation_seal(
        cls,
        practitioner_id: str,
        total_hours: float,
        domain_breakdown: Dict[str, float],
        jatc_signer_id: str = "JATC-DIR-101-WASH"
    ) -> WageElevationSeal:
        tier_info = cls.determine_tier(total_hours)
        now_iso = datetime.now(timezone.utc).isoformat()
        seal_id = f"SEAL-{uuid.uuid4().hex[:12].upper()}"

        return WageElevationSeal(
            seal_id=seal_id,
            issued_at=now_iso,
            practitioner_id=practitioner_id,
            elevated_tier=tier_info["tier_name"],
            wage_step_percentage=tier_info["wage_step_percentage"],
            total_verified_hours=round(total_hours, 2),
            domain_breakdown={k: round(v, 2) for k, v in domain_breakdown.items()},
            jatc_director_signature=f"SIG_{jatc_signer_id}_{seal_id}"
        )
