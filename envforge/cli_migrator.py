"""CLI sub-commands for snapshot migration."""

from __future__ import annotations

import argparse
import sys

from envforge.migrator import CURRENT_SCHEMA_VERSION, detect_version, migrate_dict
from envforge.serializer import load_snapshot, save_snapshot, snapshot_to_dict


def add_migrator_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *migrate* sub-command."""
    parser = subparsers.add_parser(
        "migrate",
        help="Upgrade a snapshot file to the current schema version.",
    )
    parser.add_argument("snapshot", help="Path to the snapshot JSON file.")
    parser.add_argument(
        "--target-version",
        type=int,
        default=CURRENT_SCHEMA_VERSION,
        help=f"Target schema version (default: {CURRENT_SCHEMA_VERSION}).",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite the source file with the migrated snapshot.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write migrated snapshot to this path (ignored with --in-place).",
    )
    parser.set_defaults(func=cmd_migrate)


def cmd_migrate(args: argparse.Namespace) -> int:
    """Execute the *migrate* command."""
    try:
        snapshot = load_snapshot(args.snapshot)
    except FileNotFoundError:
        print(f"Error: file not found: {args.snapshot}", file=sys.stderr)
        return 1

    data = snapshot_to_dict(snapshot)
    original_version = detect_version(data)

    if original_version >= args.target_version:
        print(
            f"Snapshot is already at schema version {original_version}; "
            "nothing to do."
        )
        return 0

    result = migrate_dict(data, target_version=args.target_version)

    for step in result.steps_applied:
        print(f"  Applied: {step}")
    for warning in result.warnings:
        print(f"  Warning: {warning}", file=sys.stderr)

    dest = args.snapshot if args.in_place else (args.output or args.snapshot)
    save_snapshot(result.snapshot, dest)
    print(
        f"Migrated {args.snapshot} from v{original_version} "
        f"to v{result.target_version} -> {dest}"
    )
    return 0
