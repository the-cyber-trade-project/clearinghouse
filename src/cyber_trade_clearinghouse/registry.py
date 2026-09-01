"""
National Cybersecurity Trade Board (NCTB) Practitioner Registry & Public Directory.
"""

from typing import Dict, Optional, List
from cyber_trade_clearinghouse.models import (
    PractitionerRecord,
    SafetyNonConcurrenceRecord,
    RegionalLocalRecord,
    EmployerRecord,
    DispatchRequisition,
    DispatchResult,
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
            candidates = [p for p in candidates if tier.lower() in p.tier.lower()]

        if endorsement:
            candidates = [p for p in candidates if endorsement in p.active_endorsements]

        if modality and modality != "Any Modality":
            if modality == "Remote":
                candidates = [p for p in candidates if p.work_modality_preference in ["Remote Only", "Any Modality"]]
            elif modality == "Hybrid":
                candidates = [p for p in candidates if p.work_modality_preference in ["Hybrid", "Any Modality"]]
            elif modality == "On-Site":
                candidates = [p for p in candidates if p.work_modality_preference in ["On-Site", "Any Modality", "Hybrid"]]

        # Sort FIFO: Longest days seeking placement first (descending days)
        candidates.sort(key=lambda p: (
            0 if "Priority Safe Harbor" in p.dispatch_book else 1,
            -p.days_seeking_placement
        ))
        return candidates

    def dispatch_candidate(self, req: DispatchRequisition) -> DispatchResult:
        """
        Matches and dispatches Candidate #1 from the Out-of-Work List under First-In, First-Out (FIFO) rules.
        """
        queue = self.get_out_of_work_queue(
            local_id=req.target_local_id,
            tier=req.required_tier,
            endorsement=req.required_endorsement,
            modality=req.work_modality,
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

