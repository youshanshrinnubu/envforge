"""CLI subcommand for snapshot redaction."""

from __future__ import annotations

import argparse
import sys

from envforge.redactor import DEFAULT_SENSITIVE_PATTERNS, redact_snapshot
from envforge.serializer import load_snapshot, save_snapshot


def add_redactor_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "redact",
        help="Mask sensitive environment variable values in a snapshot.",
    )
    parser.add_argument("snapshot", help="Path to the input snapshot JSON file.")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Path for the redacted output snapshot (default: overwrite input).",
    )
    parser.add_argument(
        "--pattern",
        dest="patterns",
        action="append",
        metavar="REGEX",
        help="Additional regex pattern to mark as sensitive (may be repeated). "
             "Replaces default patterns when provided.",
    )
    parser.add_argument(
        "--placeholder",
        default="**REDACTED**",
        help="Replacement text for redacted values (default: **REDACTED**).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print which keys would be redacted without writing output.",
    )
    parser.set_defaults(func=cmd_redact)


def cmd_redact(args: argparse.Namespace) -> int:
    try:
        snapshot = load_snapshot(args.snapshot)
    except FileNotFoundError:
        print(f"error: snapshot file not found: {args.snapshot}", file=sys.stderr)
        return 1

    patterns = args.patterns if args.patterns else DEFAULT_SENSITIVE_PATTERNS
    result = redact_snapshot(snapshot, patterns=patterns, placeholder=args.placeholder)

    if args.dry_run:
        if result.redacted_keys:
            print("Keys that would be redacted:")
            for key in result.redacted_keys:
                print(f"  - {key}")
        else:
            print("No sensitive keys detected.")
        return 0

    output_path = args.output or args.snapshot
    save_snapshot(result.snapshot, output_path)

    if result.redacted_keys:
        print(f"Redacted {len(result.redacted_keys)} key(s): {', '.join(result.redacted_keys)}")
    else:
        print("No sensitive keys found; snapshot unchanged.")

    print(f"Saved to: {output_path}")
    return 0
