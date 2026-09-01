"""
Tests for bundle ingestion, Merkle verification, and fatigue rule monitoring.
"""

from cyber_trade_clearinghouse.ingestion import ClearinghouseIngestionEngine
from cyber_trade_clearinghouse.crypto import compute_entry_hash, compute_merkle_root


def test_ingestion_valid_bundle():
    engine = ClearinghouseIngestionEngine()

    h1 = compute_entry_hash(
        log_id="LOG-001",
        prev_hash=None,
        practitioner_id="CTP-APP-2026-0001",
        date="2026-08-28",
        hours=4.0,
        core_domain="D1_PERIMETER_CLOUD",
        artifact_ref="CR-101"
    )
    h2 = compute_entry_hash(
        log_id="LOG-002",
        prev_hash=h1,
        practitioner_id="CTP-APP-2026-0001",
        date="2026-08-29",
        hours=6.0,
        core_domain="D2_DETECTION_SOC",
        artifact_ref="CR-102"
    )
    root = compute_merkle_root([h1, h2])

    bundle_data = {
        "bundle_id": "BUNDLE-TEST-001",
        "created_at": "2026-08-30T12:00:00Z",
        "practitioner_id": "CTP-APP-2026-0001",
        "practitioner_name": "Test Apprentice",
        "current_tier": "Tier 1 Apprentice",
        "merkle_root_hash": root,
        "entry_count": 2,
        "domain_hours": {
            "D1_PERIMETER_CLOUD": 4.0,
            "D2_DETECTION_SOC": 6.0
        },
        "entries": [
            {
                "log_id": "LOG-001",
                "practitioner": {"trade_id": "CTP-APP-2026-0001", "name": "Test Apprentice", "tier": "Tier 1 Apprentice"},
                "supervisor": {"trade_id": "CTP-JRN-2024-0010", "license_status": "Active", "supervision_ratio_compliant": True},
                "runtime_execution": {"date": "2026-08-28", "hours_logged": 4.0, "core_domain": "D1_PERIMETER_CLOUD"},
                "verification_artifacts": [{"artifact_type": "change_ticket_id", "artifact_reference": "CR-101", "sanitized_summary": "Test task 1"}]
            },
            {
                "log_id": "LOG-002",
                "practitioner": {"trade_id": "CTP-APP-2026-0001", "name": "Test Apprentice", "tier": "Tier 1 Apprentice"},
                "supervisor": {"trade_id": "CTP-JRN-2024-0010", "license_status": "Active", "supervision_ratio_compliant": True},
                "runtime_execution": {"date": "2026-08-29", "hours_logged": 6.0, "core_domain": "D2_DETECTION_SOC"},
                "verification_artifacts": [{"artifact_type": "change_ticket_id", "artifact_reference": "CR-102", "sanitized_summary": "Test task 2"}]
            }
        ]
    }

    report = engine.process_bundle(bundle_data)
    assert report.is_valid is True
    assert report.entry_count == 2
    assert report.total_hours == 10.0
    assert len(report.errors) == 0


def test_ingestion_merkle_mismatch_fails():
    engine = ClearinghouseIngestionEngine()
    bundle_data = {
        "bundle_id": "BUNDLE-TEST-002",
        "created_at": "2026-08-30T12:00:00Z",
        "practitioner_id": "CTP-APP-2026-0001",
        "practitioner_name": "Test Apprentice",
        "current_tier": "Tier 1 Apprentice",
        "merkle_root_hash": "0000000000000000000000000000000000000000000000000000000000000000",
        "entry_count": 1,
        "domain_hours": {"D1_PERIMETER_CLOUD": 4.0},
        "entries": [
            {
                "log_id": "LOG-001",
                "practitioner": {"trade_id": "CTP-APP-2026-0001", "name": "Test Apprentice", "tier": "Tier 1 Apprentice"},
                "supervisor": {"trade_id": "CTP-JRN-2024-0010", "license_status": "Active", "supervision_ratio_compliant": True},
                "runtime_execution": {"date": "2026-08-28", "hours_logged": 4.0, "core_domain": "D1_PERIMETER_CLOUD"},
                "verification_artifacts": [{"artifact_type": "change_ticket_id", "artifact_reference": "CR-101", "sanitized_summary": "Test task 1"}]
            }
        ]
    }
    report = engine.process_bundle(bundle_data)
    assert report.is_valid is False
    assert len(report.errors) > 0


def test_ingestion_fatigue_warning_and_duplicate_artifacts():
    engine = ClearinghouseIngestionEngine()
    h = compute_entry_hash("LOG-FATIGUE", None, "CTP-APP-1", "2026-08-30", 15.5, "D1_PERIMETER_CLOUD", "DUP-ART-1")
    root = compute_merkle_root([h])
    bundle = {
        "bundle_id": "BUNDLE-FATIGUE",
        "created_at": "2026-08-30T00:00:00Z",
        "practitioner_id": "CTP-APP-1",
        "practitioner_name": "Test Apprentice",
        "current_tier": "Tier 1 Apprentice",
        "merkle_root_hash": root,
        "entry_count": 1,
        "domain_hours": {"D1_PERIMETER_CLOUD": 15.5},
        "entries": [
            {
                "log_id": "LOG-FATIGUE",
                "practitioner": {"trade_id": "CTP-APP-1", "name": "Test Apprentice", "tier": "Tier 1 Apprentice"},
                "supervisor": {"trade_id": "CTP-JRN-1", "license_status": "Active", "supervision_ratio_compliant": True},
                "runtime_execution": {"date": "2026-08-30", "hours_logged": 15.5, "core_domain": "D1_PERIMETER_CLOUD"},
                "verification_artifacts": [{"artifact_type": "ticket", "artifact_reference": "DUP-ART-1", "sanitized_summary": "long shift"}]
            }
        ]
    }
    report = engine.process_bundle(bundle)
    assert report.is_valid is True
    assert any("14-Hour Incident Operational Ceiling" in w for w in report.warnings)

