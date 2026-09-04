"""
National Cybersecurity Trade Board (NCTB) Practitioner Registry & Public Directory.
"""

from typing import Dict, Optional, List, Tuple
from cyber_trade_clearinghouse.models import (
    PractitionerRecord,
    SafetyNonConcurrenceRecord,
    RegionalLocalRecord,
    EmployerRecord,
    DispatchRequisition,
    DispatchResult,
    DispatchReferralSlip,
)


class TradeRegistry:
    """
    Maintains active license records, public keys, domain runtime balances, evidentiary filings,
    and the Craft Guild Out-of-Work Dispatch Queue.
    """

    def __init__(self):
        self._practitioners: Dict[str, PractitionerRecord] = {}
        self._non_concurrences: Dict[str, SafetyNonConcurrenceRecord] = {}
        self._locals: Dict[str, RegionalLocalRecord] = {}
        self._employers: Dict[str, EmployerRecord] = {}
        self._requisitions: Dict[str, DispatchRequisition] = {}
        self._referral_slips: Dict[str, DispatchReferralSlip] = {}

    def submit_requisition(self, record: DispatchRequisition) -> None:
        self._requisitions[record.requisition_id] = record

    def get_requisition(self, requisition_id: str) -> Optional[DispatchRequisition]:
        return self._requisitions.get(requisition_id)

    def list_requisitions(self, status: Optional[str] = None) -> List[DispatchRequisition]:
        if status:
            return [r for r in self._requisitions.values() if r.status == status]
        return list(self._requisitions.values())

    def list_referral_slips(self) -> List[DispatchReferralSlip]:
        return list(self._referral_slips.values())

    def register_practitioner(self, record: PractitionerRecord) -> None:
        self._practitioners[record.trade_id] = record

    def get_practitioner(self, trade_id: str) -> Optional[PractitionerRecord]:
        return self._practitioners.get(trade_id)

    def list_practitioners(self) -> List[PractitionerRecord]:
        return list(self._practitioners.values())

    def register_local(self, record: RegionalLocalRecord) -> None:
        self._locals[record.local_id] = record

    def get_local(self, local_id: str) -> Optional[RegionalLocalRecord]:
        return self._locals.get(local_id)

    def list_locals(self) -> List[RegionalLocalRecord]:
        return list(self._locals.values())

    def register_employer(self, record: EmployerRecord) -> None:
        self._employers[record.pec_id] = record

    def get_employer(self, pec_id: str) -> Optional[EmployerRecord]:
        return self._employers.get(pec_id)

    def list_employers(self) -> List[EmployerRecord]:
        return list(self._employers.values())

    def record_safety_non_concurrence(self, record: SafetyNonConcurrenceRecord) -> None:
        self._non_concurrences[record.record_id] = record

    def get_safety_non_concurrence(self, record_id: str) -> Optional[SafetyNonConcurrenceRecord]:
        return self._non_concurrences.get(record_id)

    def list_safety_non_concurrences(self) -> List[SafetyNonConcurrenceRecord]:
        return list(self._non_concurrences.values())

    def update_verified_hours(self, trade_id: str, new_hours: Dict[str, float]) -> Optional[PractitionerRecord]:
        prac = self._practitioners.get(trade_id)
        if not prac:
            return None
        for dom, hrs in new_hours.items():
            prac.domain_hours[dom] = prac.domain_hours.get(dom, 0.0) + hrs
        prac.total_verified_hours = sum(prac.domain_hours.values())
        return prac

    def get_out_of_work_queue(
        self,
        local_id: Optional[str] = None,
        tier: Optional[str] = None,
        endorsement: Optional[str] = None,
        modality: Optional[str] = None,
        requires_mor: bool = False,
        mor_engagement_type: Optional[str] = None,
    ) -> List[PractitionerRecord]:
        """
        Returns practitioners on the Out-of-Work List sorted strictly by FIFO chronological
        seniority of availability (longest days seeking placement first).
        """
        candidates = [p for p in self._practitioners.values() if p.is_seeking_placement]

        if local_id and local_id != "ALL":
            candidates = [
                p for p in candidates
                if p.assigned_jatc_local == local_id or p.relocation_willingness == "National / Willing to Relocate"
            ]

        if tier:
            candidates = [p for p in candidates if self._matches_tier(p.tier, tier)]

        if requires_mor:
            candidates = [
                p for p in candidates
                if "master" in p.tier.lower() and p.seeking_mor_role
            ]
            if mor_engagement_type and mor_engagement_type != "Any":
                candidates = [
                    p for p in candidates
                    if mor_engagement_type.lower() in p.mor_availability.lower() or p.mor_availability == "Any"
                ]

        if endorsement and endorsement != "ANY":
            candidates = [p for p in candidates if endorsement in p.active_endorsements]

        if modality and modality != "Any Modality":
            if modality == "Remote":
                candidates = [p for p in candidates if p.work_modality_preference in ["Remote Only", "Any Modality"]]
            elif modality == "Hybrid":
                candidates = [p for p in candidates if p.work_modality_preference in ["Hybrid", "Any Modality"]]
            elif modality == "On-Site":
                candidates = [p for p in candidates if p.work_modality_preference in ["On-Site", "Any Modality", "Hybrid"]]

        # Sort FIFO: Priority Safe Harbor first, then longest days seeking placement (descending days)
        candidates.sort(key=lambda p: (
            0 if "Priority Safe Harbor" in p.dispatch_book else 1,
            -p.days_seeking_placement
        ))
        return candidates

    @staticmethod
    def _matches_tier(practitioner_tier: str, requested_tier: str) -> bool:
        """
        Differentiates tiers precisely so Tier 1 does not mistakenly match Tier 2 or vice versa.
        """
        p_clean = practitioner_tier.lower().strip()
        r_clean = requested_tier.lower().strip()

        for num in ("1", "2", "3", "4"):
            req_marker = f"tier {num}"
            if req_marker in r_clean:
                return req_marker in p_clean

        if "journeyman" in r_clean:
            return "journeyman" in p_clean and "master" not in p_clean

        if "master" in r_clean:
            return "master" in p_clean

        return r_clean in p_clean

    def dispatch_candidate(self, req: DispatchRequisition) -> DispatchResult:
        """
        Matches and dispatches Candidate #1 from the Out-of-Work List under First-In, First-Out (FIFO) rules.
        """
        queue = self.get_out_of_work_queue(
            local_id=req.target_local_id,
            tier=req.required_tier,
            endorsement=req.required_endorsement,
            modality=req.work_modality,
            requires_mor=req.requires_mor,
            mor_engagement_type=req.mor_engagement_type,
        )

        if not queue:
            return DispatchResult(
                matched=False,
                candidate=None,
                queue_position=0,
                message="No qualified practitioner currently available in matching Out-of-Work queue."
            )

        top_candidate = queue[0]
        return DispatchResult(
            matched=True,
            candidate=top_candidate,
            queue_position=1,
            message=f"Dispatched Candidate #1 under FIFO seniority ({top_candidate.days_seeking_placement} days seeking placement)."
        )


    def officer_evaluate_requisition(
        self,
        requisition_id: str
    ) -> Tuple[Optional[DispatchRequisition], List[PractitionerRecord], List[str]]:
        """
        Provides the Talent Clearinghouse Dispatch Officer with the requisition details,
        the FIFO candidate queue, and active queue aging alerts for proactive intervention.
        """
        req = self._requisitions.get(requisition_id)
        if not req:
            return None, [], ["Requisition not found in clearinghouse ledger."]

        queue = self.get_out_of_work_queue(
            local_id=req.target_local_id,
            tier=req.required_tier,
            endorsement=req.required_endorsement,
            modality=req.work_modality,
            requires_mor=req.requires_mor,
            mor_engagement_type=req.mor_engagement_type,
        )

        alerts: List[str] = []
        aging_candidates = [c for c in queue if c.is_queue_aging_alert]
        if aging_candidates:
            names = ", ".join(f"{c.name} ({c.days_seeking_placement}d)" for c in aging_candidates)
            alerts.append(f"AGING QUEUE ALERT: {len(aging_candidates)} candidate(s) waiting 30+ days: {names}")

        if not queue:
            alerts.append("ZERO MATCHES: Requisition exceeds current Out-of-Work inventory; requires regional broadcast.")

        return req, queue, alerts

    def officer_execute_referral(
        self,
        requisition_id: str,
        candidate_trade_id: str,
        dispatching_officer_id: str,
        referral_date: str = "2026-09-03",
        notes: Optional[str] = None,
    ) -> DispatchReferralSlip:
        """
        Executes formal bilateral referral by the Guild Dispatch Officer.
        Transitions requisition to REFERRED and sets candidate as placed.
        """
        req = self._requisitions.get(requisition_id)
        if not req:
            raise ValueError(f"Requisition {requisition_id} not found.")

        candidate = self._practitioners.get(candidate_trade_id)
        if not candidate:
            raise ValueError(f"Practitioner {candidate_trade_id} not found.")

        wage_pct = 100
        if "tier 1" in candidate.tier.lower():
            wage_pct = 50
        elif "tier 2" in candidate.tier.lower():
            wage_pct = 60
        elif "tier 3" in candidate.tier.lower():
            wage_pct = 70
        elif "tier 4" in candidate.tier.lower():
            wage_pct = 80
        elif "master" in candidate.tier.lower():
            wage_pct = 135

        ref_id = f"REF-{requisition_id}-{candidate_trade_id}"
        slip = DispatchReferralSlip(
            referral_id=ref_id,
            requisition_id=req.requisition_id,
            employer_pec_id=req.employer_pec_id,
            candidate_trade_id=candidate.trade_id,
            candidate_name=candidate.name,
            tier=candidate.tier,
            is_mor_designation=req.requires_mor,
            mor_engagement_type=req.mor_engagement_type if req.requires_mor else None,
            dispatching_officer_id=dispatching_officer_id,
            referral_date=referral_date,
            dispatch_book=candidate.dispatch_book,
            days_on_queue=candidate.days_seeking_placement,
            wage_step_percentage=wage_pct,
            anti_wage_arbitrage_applied=(req.work_modality == "Remote"),
            status="ISSUED"
        )

        req.status = "REFERRED"
        req.assigned_officer_id = dispatching_officer_id
        req.dispatched_trade_id = candidate.trade_id
        req.referral_notes = notes

        candidate.is_seeking_placement = False
        candidate.sponsoring_pec_id = req.employer_pec_id
        employer = self._employers.get(req.employer_pec_id)
        if employer:
            candidate.sponsoring_employer = employer.name

        self._referral_slips[ref_id] = slip
        return slip

