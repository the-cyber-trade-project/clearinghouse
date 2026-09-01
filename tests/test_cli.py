"""
Tests for ctl-clearinghouse CLI tool commands.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from cyber_trade_clearinghouse.cli import main
from cyber_trade_clearinghouse.crypto import compute_entry_hash, compute_merkle_root


def test_cli_evaluate(capsys):
    test_args = ["ctl-clearinghouse", "evaluate", "--hours", "4200", "--practitioner-id", "CTP-APP-2026-0001"]
    with patch("sys.argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["tier_info"]["wage_step_percentage"] == 70
    assert data["elevation_seal"]["practitioner_id"] == "CTP-APP-2026-0001"


def test_cli_ingest_valid(capsys):
    h = compute_entry_hash("LOG-1", None, "CTP-APP-1", "2026-08-30", 5.0, "D1_PERIMETER_CLOUD", "CR-1")
    root = compute_merkle_root([h])
    bundle = {
        "bundle_id": "BUNDLE-1",
        "created_at": "2026-08-30T00:00:00Z",
        "practitioner_id": "CTP-APP-1",
        "practitioner_name": "Test Apprentice",
        "current_tier": "Tier 1 Apprentice",
        "merkle_root_hash": root,
        "entry_count": 1,
        "domain_hours": {"D1_PERIMETER_CLOUD": 5.0},
        "entries": [
            {
                "log_id": "LOG-1",
                "practitioner": {"trade_id": "CTP-APP-1", "name": "Test Apprentice", "tier": "Tier 1 Apprentice"},
                "supervisor": {"trade_id": "CTP-JRN-1", "license_status": "Active", "supervision_ratio_compliant": True},
                "runtime_execution": {"date": "2026-08-30", "hours_logged": 5.0, "core_domain": "D1_PERIMETER_CLOUD"},
                "verification_artifacts": [{"artifact_type": "ticket", "artifact_reference": "CR-1", "sanitized_summary": "task"}]
            }
        ]
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(bundle, tf)
        tmp_path = tf.name

    try:
        test_args = ["ctl-clearinghouse", "ingest", tmp_path]
        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
        captured = capsys.readouterr()
        report = json.loads(captured.out)
        assert report["is_valid"] is True
        assert report["total_hours"] == 5.0
    finally:
        Path(tmp_path).unlink(missing_ok=True)

