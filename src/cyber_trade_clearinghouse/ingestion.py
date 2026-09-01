"""
Ingestion & Verification Engine for Logbook Submission Bundles and Vault Envelopes.
"""

from typing import Dict, Any, List, Tuple
from cyber_trade_clearinghouse.models import SubmissionBundle, LogbookEntry
from cyber_trade_clearinghouse.crypto import compute_entry_hash, compute_merkle_root


class IngestionReport:
    def __init__(self, bundle_id: str, practitioner_id: str):
        self.bundle_id = bundle_id
        self.practitioner_id = practitioner_id
        self.is_valid = True
        self.entry_count = 0
        self.total_hours = 0.0
        self.domain_hours: Dict[str, float] = {
            "D1_PERIMETER_CLOUD": 0.0,
            "D2_DETECTION_SOC": 0.0,
            "D3_IDENTITY_IAM": 0.0,
            "D4_VULN_ATTACK": 0.0,
            "D5_DEFENSIVE_GRC": 0.0,
        }
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.computed_merkle_root: str = ""
        self.declared_merkle_root: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "practitioner_id": self.practitioner_id,
            "is_valid": self.is_valid,
            "entry_count": self.entry_count,
            "total_hours": round(self.total_hours, 2),
            "domain_hours": {k: round(v, 2) for k, v in self.domain_hours.items()},
            "declared_merkle_root": self.declared_merkle_root,
            "computed_merkle_root": self.computed_merkle_root,
            "merkle_match": self.declared_merkle_root == self.computed_merkle_root,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class ClearinghouseIngestionEngine:
    """
    Ingests and audits client submission bundles against the National Cybersecurity Trade Board standards.
    """

    CORE_DOMAINS = {
        "D1_PERIMETER_CLOUD",
        "D2_DETECTION_SOC",
        "D3_IDENTITY_IAM",
        "D4_VULN_ATTACK",
        "D5_DEFENSIVE_GRC",
        "D1_DEFENSIVE_SECURITY_ENGINEERING",
        "D2_SYSTEM_HYGIENE",
        "D3_AUDIT_ASSESSMENT",
        "D4_INCIDENT_HANDLING",
        "D5_IDENTITY_SYSTEMS",
    }

    @staticmethod
    def map_domain_key(domain: str) -> str:
        d = domain.upper()
        if "D1" in d:
            return "D1_PERIMETER_CLOUD"
        elif "D2" in d:
            return "D2_DETECTION_SOC"
        elif "D3" in d:
            return "D3_IDENTITY_IAM"
        elif "D4" in d:
            return "D4_VULN_ATTACK"
        elif "D5" in d:
            return "D5_DEFENSIVE_GRC"
        return "D1_PERIMETER_CLOUD"

    def process_bundle(self, bundle_data: Dict[str, Any]) -> IngestionReport:
        """
        Parses, traverses Merkle chains, and verifies unbroken integrity of a submission bundle.
        """
        bundle = SubmissionBundle(**bundle_data)
        report = IngestionReport(bundle.bundle_id, bundle.practitioner_id)
        report.declared_merkle_root = bundle.merkle_root_hash

        if not bundle.entries:
            report.is_valid = False
            report.errors.append("Bundle contains zero logbook entries.")
            return report

        entry_hashes = []
        prev_hash = None
        seen_artifacts = set()

        for idx, entry in enumerate(bundle.entries):
            report.entry_count += 1
            hrs = entry.runtime_execution.hours_logged
            report.total_hours += hrs

            dom_key = self.map_domain_key(entry.runtime_execution.core_domain)
            report.domain_hours[dom_key] = report.domain_hours.get(dom_key, 0.0) + hrs

            # 1. Check Fatigue Rules
            if hrs > 14.0:
                report.warnings.append(f"Entry {entry.log_id}: Logged hours ({hrs}h) exceed 14-Hour Incident Operational Ceiling.")

            # 2. Extract primary artifact
            art_ref = entry.verification_artifacts[0].artifact_reference if entry.verification_artifacts else "NO_ARTIFACT"
            if art_ref in seen_artifacts and art_ref != "NO_ARTIFACT":
                report.warnings.append(f"Entry {entry.log_id}: Duplicate artifact reference detected ({art_ref}).")
            seen_artifacts.add(art_ref)

            # 3. Compute canonical chained hash
            calculated_hash = compute_entry_hash(
                log_id=entry.log_id,
                prev_hash=prev_hash,
                practitioner_id=entry.practitioner.trade_id,
                date=entry.runtime_execution.date,
                hours=hrs,
                core_domain=dom_key,
                artifact_ref=art_ref
            )
            entry_hashes.append(calculated_hash)
            prev_hash = calculated_hash

        # 4. Compute Merkle Root
        computed_root = compute_merkle_root(entry_hashes)
        report.computed_merkle_root = computed_root

        # 5. Check Merkle Consistency
        clean_declared = bundle.merkle_root_hash[7:] if bundle.merkle_root_hash.startswith("sha256:") else bundle.merkle_root_hash
        if clean_declared != computed_root:
            report.is_valid = False
            report.errors.append(f"Merkle root mismatch! Declared: {clean_declared}, Computed: {computed_root}")

        return report
