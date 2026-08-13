"""Command-line entrypoint for reproducible AttackPath AI workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import (
    DEFAULT_THRESHOLD,
    analyze_events,
    generate_synthetic_events,
    public_analysis,
    write_analysis_json,
    write_events_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AttackPath AI defensive simulation lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="write deterministic synthetic events")
    generate.add_argument("--output", default="attackpath-ai/data/synthetic_events.csv")
    generate.add_argument("--seed", type=int, default=42)

    analyze = subparsers.add_parser("analyze", help="score events and write evaluation evidence")
    analyze.add_argument("--output", default="attackpath-ai/artifacts/evaluation.json")
    analyze.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)

    subparsers.add_parser("self-test", help="run dependency-free release gates")
    return parser


def self_test() -> dict[str, object]:
    first = generate_synthetic_events()
    second = generate_synthetic_events()
    assert first == second, "generator must be deterministic"
    analysis = analyze_events(first)
    metrics = analysis["test_metrics"]
    operations = analysis["operational_metrics"]
    assert metrics["recall"] >= 0.90
    assert metrics["precision"] >= 0.85
    assert operations["path_prevention_rate"] >= 0.90
    assert operations["mean_minutes_to_detect"] <= 25
    assert all("@" not in event.identity for event in first)
    return {
        "status": "PASS",
        "events": len(first),
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "path_prevention_rate": operations["path_prevention_rate"],
        "mean_minutes_to_detect": operations["mean_minutes_to_detect"],
    }


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "generate":
        events = generate_synthetic_events(seed=args.seed)
        write_events_csv(events, args.output)
        print(json.dumps({"events": len(events), "output": str(Path(args.output))}, indent=2))
    elif args.command == "analyze":
        analysis = analyze_events(generate_synthetic_events(), threshold=args.threshold)
        write_analysis_json(analysis, args.output)
        summary = public_analysis(analysis)
        print(json.dumps({"test_metrics": summary["test_metrics"], "operational_metrics": summary["operational_metrics"], "output": str(Path(args.output))}, indent=2))
    else:
        print(json.dumps(self_test(), indent=2))


if __name__ == "__main__":
    main()
