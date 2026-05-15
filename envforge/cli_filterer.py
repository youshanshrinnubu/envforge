"""CLI sub-command: envforge filter — filter snapshot fields by pattern."""
from __future__ import annotations

import argparse
import re
import sys

from envforge.filterer import filter_snapshot
from envforge.serializer import load_snapshot, save_snapshot


def add_filterer_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("filter", help="Filter snapshot fields by pattern")
    p.add_argument("snapshot", help="Path to snapshot JSON file")
    p.add_argument("--env-key-pattern", metavar="REGEX",
                   help="Keep only env vars whose key matches REGEX")
    p.add_argument("--pkg-name-pattern", metavar="REGEX",
                   help="Keep only packages whose name matches REGEX")
    p.add_argument("--output", "-o", metavar="FILE",
                   help="Write filtered snapshot to FILE (default: overwrite input)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print what would be removed without writing")
    p.set_defaults(func=cmd_filter)


def cmd_filter(args: argparse.Namespace) -> int:
    try:
        snap = load_snapshot(args.snapshot)
    except FileNotFoundError:
        print(f"[filter] File not found: {args.snapshot}", file=sys.stderr)
        return 1

    env_pred = None
    pkg_pred = None

    if args.env_key_pattern:
        rx = re.compile(args.env_key_pattern)
        env_pred = lambda k, v: bool(rx.search(k))  # noqa: E731

    if args.pkg_name_pattern:
        rx = re.compile(args.pkg_name_pattern)
        pkg_pred = lambda p: bool(rx.search(p.get("name", "")))  # noqa: E731

    result = filter_snapshot(snap, env_predicate=env_pred, pkg_predicate=pkg_pred)

    removed_env = result.original_env_count - result.filtered_env_count
    removed_pkg = result.original_pkg_count - result.filtered_pkg_count

    print(f"[filter] env vars: {result.original_env_count} -> {result.filtered_env_count} "
          f"(removed {removed_env})")
    print(f"[filter] packages: {result.original_pkg_count} -> {result.filtered_pkg_count} "
          f"(removed {removed_pkg})")

    if args.dry_run:
        print("[filter] dry-run: no changes written.")
        return 0

    dest = args.output or args.snapshot
    save_snapshot(result.snapshot, dest)
    print(f"[filter] Written to {dest}")
    return 0
