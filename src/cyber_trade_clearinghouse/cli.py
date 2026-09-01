"""
Command-Line Interface for the National Cybersecurity Trade Board Clearinghouse (`ctl-clearinghouse`).
"""

import sys
import json
import argparse
from pathlib import Path
from cyber_trade_clearinghouse.ingestion import ClearinghouseIngestionEngine
from cyber_trade_clearinghouse.wage_evaluator import WageStepEvaluator


def main():
    parser = argparse.ArgumentParser(
        prog="ctl-clearinghouse",
        description="National Cybersecurity Trade Board Clearinghouse & Registry Engine"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingest bundle
    ingest_parser = subparsers.add_parser("ingest", help="Ingest and verify a logbook submission bundle JSON")
    ingest_parser.add_argument("file", help="Path to submission bundle JSON file")

    # Evaluate hours
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate total hours and compute statutory Wage Step elevation")
    eval_parser.add_argument("--hours", type=float, required=True, help="Total verified operational runtime hours")
    eval_parser.add_argument("--practitioner-id", type=str, default="CTP-APP-DEMO", help="Practitioner Trade ID")

    args = parser.parse_args()

    if args.command == "ingest":
        path = Path(args.file)
        if not path.exists():
            print(f"[FAIL] File not found: {path}", file=sys.stderr)
            sys.exit(1)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        engine = ClearinghouseIngestionEngine()
        report = engine.process_bundle(data)
        print(json.dumps(report.to_dict(), indent=2))
        sys.exit(0 if report.is_valid else 1)

    elif args.command == "evaluate":
        tier_info = WageStepEvaluator.determine_tier(args.hours)
        seal = WageStepEvaluator.issue_elevation_seal(args.practitioner_id, args.hours, {})
        output = {
            "tier_info": tier_info,
            "elevation_seal": seal.model_dump()
        }
        print(json.dumps(output, indent=2))
        sys.exit(0)

    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
