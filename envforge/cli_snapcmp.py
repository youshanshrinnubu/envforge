"""CLI subcommand: envforge snapcmp — compare two snapshot files."""
import argparse
import sys

from envforge.serializer import load_snapshot
from envforge.snapcmp import compare_snapshots_report


def add_snapcmp_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "snapcmp",
        help="Compare two snapshot files side-by-side",
    )
    p.add_argument("left", help="Path to the first (base) snapshot file")
    p.add_argument("right", help="Path to the second snapshot file")
    p.add_argument(
        "--left-label",
        default=None,
        metavar="LABEL",
        help="Override display label for the left snapshot",
    )
    p.add_argument(
        "--right-label",
        default=None,
        metavar="LABEL",
        help="Override display label for the right snapshot",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 when differences are found",
    )
    p.set_defaults(func=cmd_snapcmp)


def cmd_snapcmp(args: argparse.Namespace) -> int:
    try:
        left = load_snapshot(args.left)
    except Exception as exc:  # pragma: no cover
        print(f"Error loading left snapshot '{args.left}': {exc}", file=sys.stderr)
        return 2

    try:
        right = load_snapshot(args.right)
    except Exception as exc:  # pragma: no cover
        print(f"Error loading right snapshot '{args.right}': {exc}", file=sys.stderr)
        return 2

    report = compare_snapshots_report(
        left,
        right,
        left_label=args.left_label,
        right_label=args.right_label,
    )
    print(report)

    if args.exit_code and not report:
        return 1
    return 0
