"""CLI subcommand for inspecting snapshot fields in detail."""

import argparse
import sys

from envforge.serializer import load_snapshot
from envforge.inspector import inspect_snapshot, InspectionReport


def add_inspector_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "inspect",
        help="Inspect individual fields of a snapshot in detail",
    )
    parser.add_argument("snapshot", help="Path to the snapshot JSON file")
    parser.add_argument(
        "--field",
        dest="field",
        default=None,
        help="Show only a specific field (e.g. python_version, env_vars)",
    )
    parser.add_argument(
        "--missing",
        action="store_true",
        default=False,
        help="Show only fields that are missing or empty",
    )
    parser.set_defaults(func=cmd_inspect)


def _print_field(fi, verbose: bool = True) -> None:
    status = "✔" if fi.present else "✘"
    print(f"  [{status}] {fi.name}: {fi.summary}")
    if verbose and fi.details:
        for detail in fi.details:
            print(f"        {detail}")


def cmd_inspect(args: argparse.Namespace) -> int:
    try:
        snapshot = load_snapshot(args.snapshot)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error loading snapshot: {exc}", file=sys.stderr)
        return 1

    report = inspect_snapshot(snapshot)
    print(f"Snapshot: {report.label}")
    print(f"File:     {args.snapshot}")
    print()

    if args.field:
        fi = report.get(args.field)
        if fi is None:
            print(f"Unknown field: {args.field}", file=sys.stderr)
            return 1
        _print_field(fi, verbose=True)
        return 0

    fields_to_show = report.missing_fields() if args.missing else report.fields

    if not fields_to_show:
        print("No fields to display.")
        return 0

    for fi in fields_to_show:
        _print_field(fi, verbose=not args.missing)

    print()
    present_count = len(report.present_fields())
    total = len(report.fields)
    print(f"Summary: {present_count}/{total} fields populated")
    return 0
