"""CLI subcommand for linting snapshots."""

import argparse
import sys
from envforge.serializer import load_snapshot
from envforge.linter import lint_snapshot, SEVERITY_ERROR, SEVERITY_WARNING, SEVERITY_INFO

SEVERITY_ICONS = {
    SEVERITY_ERROR: "[ERROR]",
    SEVERITY_WARNING: "[WARN] ",
    SEVERITY_INFO: "[INFO] ",
}


def add_linter_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "lint",
        help="Lint a snapshot file for common issues and best practices.",
    )
    parser.add_argument("snapshot", help="Path to the snapshot JSON file.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status on warnings as well as errors.",
    )
    parser.add_argument(
        "--min-severity",
        choices=[SEVERITY_ERROR, SEVERITY_WARNING, SEVERITY_INFO],
        default=SEVERITY_INFO,
        help="Minimum severity level to display (default: info).",
    )
    parser.set_defaults(func=cmd_lint)


def cmd_lint(args: argparse.Namespace) -> int:
    try:
        snapshot = load_snapshot(args.snapshot)
    except FileNotFoundError:
        print(f"Error: snapshot file not found: {args.snapshot}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error loading snapshot: {exc}", file=sys.stderr)
        return 1

    result = lint_snapshot(snapshot)

    severity_order = [SEVERITY_ERROR, SEVERITY_WARNING, SEVERITY_INFO]
    min_idx = severity_order.index(args.min_severity)
    visible = [i for i in result.issues if severity_order.index(i.severity) <= min_idx]

    if not visible:
        print("No issues found.")
    else:
        for issue in visible:
            icon = SEVERITY_ICONS.get(issue.severity, "[?]   ")
            print(f"{icon} {issue.code}: {issue.message}")

    errors = result.errors()
    warnings = result.warnings()
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s).")

    if errors:
        return 2
    if args.strict and warnings:
        return 1
    return 0
