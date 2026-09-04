"""
National Cybersecurity Trade Board (NCTB) Practitioner Registry & Public Directory.
"""

from typing import Dict, Optional, List, Tuple, Any
from cyber_trade_clearinghouse.models import (
    PractitionerRecord,
    SafetyNonConcurrenceRecord,
    RegionalLocalRecord,
    EmployerRecord,
)


class TradeRegistry:
    """
    Maintains active license records, public keys, domain runtime balances,
    sponsoring employer registrations, and Form FORM-001/002 evidentiary filings.
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

    def get_employer_compliance_manifest(self, pec_id: str) -> Optional[Dict[str, Any]]:
        """
        Exports the NCTB authoritative registry state for an employer.
        Consumed by external telemetry gateways and actuarial auditing engines.
        """
        emp = self._employers.get(pec_id)
        if not emp:
            return None
        non_concurrences = [
            nc for nc in self._non_concurrences.values()
            if nc.employer_pec_id == pec_id
        ]
        return {
            "pec_id": emp.pec_id,
            "name": emp.name,
            "division": emp.division,
            "operating_hubs": emp.operating_hubs,
            "designated_mor": emp.designated_mor,
            "designated_mor_id": emp.designated_mor_id,
            "mor_status": emp.mor_status,
            "active_mor": bool(emp.designated_mor_id),
            "supervisory_ratio_compliance_score": emp.ratio_compliance_score,
            "total_verified_hours": emp.total_verified_hours,
            "unresolved_safety_non_concurrences": len([nc for nc in non_concurrences if nc.status != "RESOLVED"]),
            "underwriter_tier": emp.underwriter_tier,
        }

    def update_verified_hours(self, trade_id: str, new_hours: Dict[str, float]) -> Optional[PractitionerRecord]:
        prac = self._practitioners.get(trade_id)
        if not prac:
            return None
        for dom, hrs in new_hours.items():
            prac.domain_hours[dom] = prac.domain_hours.get(dom, 0.0) + hrs
        prac.total_verified_hours = sum(prac.domain_hours.values())
        return prac
