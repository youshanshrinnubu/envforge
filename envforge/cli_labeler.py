"""CLI sub-commands for managing snapshot labels."""

from __future__ import annotations

import argparse
import sys

from envforge.serializer import load_snapshot, save_snapshot
from envforge.labeler import set_label, clear_label, get_label


def add_labeler_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the ``label`` sub-command on *subparsers*."""
    parser = subparsers.add_parser(
        "label",
        help="Get, set, or clear the label on a snapshot file.",
    )
    parser.add_argument("snapshot", help="Path to the snapshot JSON file.")

    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--set",
        metavar="LABEL",
        dest="set_label",
        default=None,
        help="Set a new label on the snapshot.",
    )
    action_group.add_argument(
        "--clear",
        action="store_true",
        default=False,
        help="Remove the existing label from the snapshot.",
    )
    parser.set_defaults(func=cmd_label)


def cmd_label(args: argparse.Namespace) -> int:
    """Execute the ``label`` sub-command."""
    try:
        snapshot = load_snapshot(args.snapshot)
    except FileNotFoundError:
        print(f"error: file not found: {args.snapshot}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not load snapshot: {exc}", file=sys.stderr)
        return 1

    if args.set_label is not None:
        try:
            result = set_label(snapshot, args.set_label)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        save_snapshot(snapshot, args.snapshot)
        status = "updated" if result.changed else "unchanged"
        print(f"Label {status}: {result.new_label!r}")
        return 0

    if args.clear:
        result = clear_label(snapshot)
        save_snapshot(snapshot, args.snapshot)
        if result.changed:
            print(f"Label cleared (was {result.previous_label!r}).")
        else:
            print("No label was set; nothing to clear.")
        return 0

    # Default: print current label
    label = get_label(snapshot)
    if label:
        print(label)
    else:
        print("(no label)")
    return 0
