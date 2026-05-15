"""CLI sub-command: envforge trim."""
from __future__ import annotations

import argparse
import sys

from envforge.serializer import load_snapshot, save_snapshot
from envforge.trimmer import trim_snapshot


def add_trimmer_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *trim* sub-command."""
    p = subparsers.add_parser(
        "trim",
        help="Remove empty env vars and unpinned packages from a snapshot.",
    )
    p.add_argument("snapshot", help="Path to the snapshot JSON file.")
    p.add_argument(
        "--inplace",
        action="store_true",
        help="Overwrite the source file with the trimmed snapshot.",
    )
    p.add_argument(
        "--output",
        metavar="FILE",
        help="Write trimmed snapshot to FILE instead of stdout.",
    )
    p.set_defaults(func=cmd_trim)


def cmd_trim(args: argparse.Namespace) -> int:
    """Execute the trim sub-command."""
    try:
        snap = load_snapshot(args.snapshot)
    except FileNotFoundError:
        print(f"Error: file not found: {args.snapshot}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading snapshot: {exc}", file=sys.stderr)
        return 1

    result = trim_snapshot(snap)

    for msg in result.messages:
        print(msg)

    if not result:
        print("Nothing to trim.")

    dest = args.output or (args.snapshot if args.inplace else None)
    if dest:
        save_snapshot(result.snapshot, dest)
        print(f"Trimmed snapshot written to {dest}")
    else:
        # Print summary only when not saving
        print(
            f"Removed {len(result.removed_env_vars)} env var(s), "
            f"{len(result.removed_packages)} package(s)."
        )

    return 0
