"""CLI sub-command: envforge freeze — freeze a snapshot file in place."""

import argparse
import sys

from envforge.freezer import freeze_snapshot
from envforge.serializer import load_snapshot, save_snapshot


def add_freezer_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "freeze",
        help="Lock all package versions and env vars in a snapshot",
    )
    p.add_argument("snapshot", help="Path to the snapshot JSON file")
    p.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write frozen snapshot to this file (default: overwrite input)",
    )
    p.add_argument(
        "--warn",
        action="store_true",
        default=False,
        help="Print warnings about un-pinned packages",
    )
    p.set_defaults(func=cmd_freeze)


def cmd_freeze(args: argparse.Namespace) -> int:
    try:
        snapshot = load_snapshot(args.snapshot)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[envforge] Error loading snapshot: {exc}", file=sys.stderr)
        return 1

    result = freeze_snapshot(snapshot)

    if args.warn and result.warnings:
        for w in result.warnings:
            print(f"[warn] {w}")

    output_path = args.output or args.snapshot
    try:
        save_snapshot(result.frozen_snapshot, output_path)
    except OSError as exc:
        print(f"[envforge] Error saving frozen snapshot: {exc}", file=sys.stderr)
        return 1

    print(f"[envforge] Frozen snapshot saved to '{output_path}'")
    print(f"  Pinned packages : {len(result.pinned_packages)}")
    print(f"  Locked env vars : {len(result.locked_env_vars)}")
    if result.warnings:
        print(f"  Warnings        : {len(result.warnings)} (run with --warn to see details)")
    return 0
