"""CLI subcommand for snapshot normalization."""

from __future__ import annotations

import argparse
import sys

from envforge.normalizer import normalize_snapshot
from envforge.serializer import load_snapshot, save_snapshot


def add_normalizer_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "normalize",
        help="Normalize snapshot fields (key casing, package names, etc.)",
    )
    p.add_argument("snapshot", help="Path to snapshot JSON file")
    p.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write normalized snapshot to this path (default: overwrite input)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing",
    )
    p.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress change output",
    )
    p.set_defaults(func=cmd_normalize)


def cmd_normalize(args: argparse.Namespace) -> int:
    try:
        snap = load_snapshot(args.snapshot)
    except FileNotFoundError:
        print(f"error: file not found: {args.snapshot}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not load snapshot: {exc}", file=sys.stderr)
        return 1

    result = normalize_snapshot(snap)

    if not args.quiet:
        if result.changes:
            print(f"Normalization changes ({len(result.changes)}):")
            for change in result.changes:
                print(f"  - {change}")
        else:
            print("No changes needed — snapshot already normalized.")

    if args.dry_run:
        return 0

    out_path = args.output or args.snapshot
    try:
        save_snapshot(result.snapshot, out_path)
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not save snapshot: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Saved normalized snapshot to {out_path}")
    return 0
