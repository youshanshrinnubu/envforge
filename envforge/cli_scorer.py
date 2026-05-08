"""CLI subcommand for snapshot quality scoring."""

import argparse
import sys
from envforge.serializer import load_snapshot
from envforge.scorer import score_snapshot


def add_scorer_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "score",
        help="Score a snapshot for completeness and reproducibility quality.",
    )
    parser.add_argument("snapshot", help="Path to snapshot JSON file.")
    parser.add_argument(
        "--min-score",
        type=int,
        default=0,
        metavar="N",
        help="Exit with non-zero status if score is below N (default: 0).",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only print the numeric score.",
    )
    parser.set_defaults(func=cmd_score)


def cmd_score(args: argparse.Namespace) -> int:
    try:
        snapshot = load_snapshot(args.snapshot)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error loading snapshot: {exc}", file=sys.stderr)
        return 2

    result = score_snapshot(snapshot)

    if args.quiet:
        print(result.score)
        return 0 if result.score >= args.min_score else 1

    print(f"Score : {result.score}/{result.max_score} ({result.percentage}%) — Grade {result.grade}")
    print("\nBreakdown:")
    for key, pts in result.breakdown.items():
        print(f"  {key:<20} {pts} pts")

    if result.suggestions:
        print("\nSuggestions:")
        for s in result.suggestions:
            print(f"  • {s}")
    else:
        print("\n✓ No suggestions — snapshot looks great!")

    if result.score < args.min_score:
        print(
            f"\n✗ Score {result.score} is below required minimum {args.min_score}.",
            file=sys.stderr,
        )
        return 1

    return 0
