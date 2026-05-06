"""CLI sub-command handler for the 'export' command."""

from __future__ import annotations

import argparse
import sys

from envforge.exporter import SUPPORTED_FORMATS, export_snapshot, write_export
from envforge.serializer import load_snapshot


def add_export_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'export' sub-command onto an existing subparsers group."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "export",
        help="Export a snapshot to shell, Dockerfile, or requirements.txt",
    )
    parser.add_argument(
        "snapshot",
        metavar="SNAPSHOT",
        help="Path to the .json snapshot file",
    )
    parser.add_argument(
        "--format",
        "-f",
        dest="fmt",
        choices=SUPPORTED_FORMATS,
        default="shell",
        help="Output format (default: shell)",
    )
    parser.add_argument(
        "--output",
        "-o",
        dest="output",
        default=None,
        help="Write output to this file instead of stdout",
    )
    parser.set_defaults(func=cmd_export)


def cmd_export(args: argparse.Namespace) -> int:
    """Execute the export sub-command.

    Returns 0 on success, 1 on error.
    """
    try:
        snapshot = load_snapshot(args.snapshot)
    except FileNotFoundError:
        print(f"[envforge] Error: snapshot file not found: {args.snapshot}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"[envforge] Error loading snapshot: {exc}", file=sys.stderr)
        return 1

    try:
        if args.output:
            write_export(snapshot, args.fmt, args.output)
            print(f"[envforge] Exported {args.fmt} to {args.output}")
        else:
            content = export_snapshot(snapshot, args.fmt)
            sys.stdout.write(content)
    except ValueError as exc:
        print(f"[envforge] Export error: {exc}", file=sys.stderr)
        return 1

    return 0
