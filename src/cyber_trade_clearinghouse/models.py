"""
Data models conforming to the Universal Logbook Schema (v1.1.0) and NCTB Clearinghouse Registry Standards.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Practitioner(BaseModel):
    trade_id: str
    name: str
    tier: str


class Supervisor(BaseModel):
    trade_id: str
    license_status: str = "Active"
    supervision_ratio_compliant: bool = True


class RuntimeExecution(BaseModel):
    date: str
    hours_logged: float = Field(gt=0, le=24)
    core_domain: str
    sub_domain: Optional[str] = None
    environment_type: str = "Enterprise_Production"


class CompetencyMilestone(BaseModel):
    code: str
    description: str


class VerificationArtifact(BaseModel):
    artifact_type: str
    artifact_reference: str
    sanitized_summary: str


class Attestation(BaseModel):
    supervisor_signature: Optional[str] = None
    signed_timestamp: Optional[str] = None
    attestation_statement: Optional[str] = None
    modality: Optional[str] = "Modality A: WebAuthn / Passkey"


class LogbookEntry(BaseModel):
    schema_url: str = Field(default="https://cybertrade.org/schemas/v1/logbook-entry.json", alias="$schema")
    log_id: str
    version: str = "1.1.0"
    practitioner: Practitioner
    supervisor: Supervisor
    runtime_execution: RuntimeExecution
    competency_milestone: Optional[CompetencyMilestone] = None
    verification_artifacts: List[VerificationArtifact] = Field(default_factory=list)
    attestation: Optional[Attestation] = None
    prev_entry_hash: Optional[str] = None
    entry_hash: Optional[str] = None


class VaultMetadata(BaseModel):
    schema_version: str = "1.1.0"
    encryption_timestamp: str
    entry_count: int
    merkle_root_hash: str
    practitioner_id: Optional[str] = None


class EncryptedVaultEnvelope(BaseModel):
    schema_url: str = Field(default="https://cybertrade.org/schemas/v1/encrypted-vault.json", alias="$schema")
    format: str = "AES-256-GCM"
    kdf: str = "PBKDF2-SHA256"
    iterations: int = 100000
    salt: List[int]
    iv: List[int]
    ciphertext: List[int]
    metadata: VaultMetadata


class SubmissionBundle(BaseModel):
    schema_url: str = Field(default="https://cybertrade.org/schemas/v1/submission-bundle.json", alias="$schema")
    bundle_id: str
    created_at: str
    practitioner_id: str
    practitioner_name: str
    current_tier: str
    merkle_root_hash: str
    entry_count: int
    domain_hours: Dict[str, float]
    entries: List[LogbookEntry] = Field(default_factory=list)


class PractitionerRecord(BaseModel):
    trade_id: str
    name: str
    tier: str
    license_status: str = "Active"
    public_key_pem: Optional[str] = None
    total_verified_hours: float = 0.0
    domain_hours: Dict[str, float] = Field(default_factory=dict)
    active_endorsements: List[str] = Field(default_factory=list)
    standing: str = "Good Standing"
    assigned_jatc_local: str = "LOCAL-101"
    sponsoring_employer: Optional[str] = None
    sponsoring_pec_id: Optional[str] = None
    work_modality_preference: str = "Any Modality"
    relocation_willingness: str = "Resident Local Only"
    security_clearance: str = "Public Trust / Commercial Unclassified"
    is_seeking_placement: bool = False
    days_seeking_placement: int = 0
    dispatch_book: str = "Book 1 (Resident)"
    last_audit_date: Optional[str] = None
    seeking_mor_role: bool = False
    mor_availability: str = "Not Seeking MoR"

    @property
    def is_queue_aging_alert(self) -> bool:
        """Flags candidate waiting 30+ days for Dispatch Officer proactive intervention."""
        return self.is_seeking_placement and self.days_seeking_placement >= 30


class RegionalLocalRecord(BaseModel):
    local_id: str
    name: str
    jurisdiction_territory: str
    zone_1_rate: float = 85.0
    zone_2_rate: float = 74.0
    zone_3_rate: float = 62.0
    coli_zone_tier: str = "Tier A (High COLI)"
    active_master_count: int = 0
    active_apprentice_count: int = 0
    active_journeyman_count: int = 0

    @property
    def rjpb_hourly_base(self) -> float:
        return self.zone_1_rate


class EmployerRecord(BaseModel):
    pec_id: str
    name: str
    division: str
    operating_hubs: str = "District 1 (Local 101)"
    designated_mor: str
    designated_mor_id: Optional[str] = None
    mor_status: str = "Full-Time MoR"
    master_count: int = 1
    journeyman_count: int
    apprentice_count: int
    ratio_compliance_score: float
    underwriter_tier: str
    total_verified_hours: float = 0.0


class DispatchRequisition(BaseModel):
    requisition_id: str
    employer_pec_id: str
    required_tier: str
    required_endorsement: Optional[str] = None
    target_local_id: str = "LOCAL-101"
    work_modality: str = "Any Modality"
    requires_clearance: Optional[str] = None
    requisition_title: Optional[str] = None
    status: str = "PENDING_REVIEW"
    requires_mor: bool = False
    mor_engagement_type: Optional[str] = "Any"
    assigned_officer_id: Optional[str] = None
    dispatched_trade_id: Optional[str] = None
    referral_notes: Optional[str] = None


class DispatchReferralSlip(BaseModel):
    referral_id: str
    requisition_id: str
    employer_pec_id: str
    candidate_trade_id: str
    candidate_name: str
    tier: str
    is_mor_designation: bool = False
    mor_engagement_type: Optional[str] = None
    dispatching_officer_id: str
    referral_date: str
    dispatch_book: str
    days_on_queue: int
    wage_step_percentage: int
    anti_wage_arbitrage_applied: bool = False
    status: str = "ISSUED"


class DispatchResult(BaseModel):
    matched: bool
    candidate: Optional[PractitionerRecord] = None
    queue_position: int = 0
    message: str = ""



class WageElevationSeal(BaseModel):
    seal_id: str
    issued_at: str
    practitioner_id: str
    elevated_tier: str
    wage_step_percentage: int
    total_verified_hours: float
    domain_breakdown: Dict[str, float]
    jatc_director_signature: str
    status: str = "ISSUED"


class SafetyNonConcurrenceRecord(BaseModel):
    record_id: str
    form_type: str = "FORM-001"
    timestamp: str
    submitting_mor_id: str
    enterprise_name: str
    criticality_tier: str
    payload_hash: str
    refusal_summary: str
    executive_override_received: bool = False
    override_hash: Optional[str] = None
