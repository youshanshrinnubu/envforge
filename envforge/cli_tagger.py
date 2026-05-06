"""CLI subcommand for managing snapshot tags."""

from __future__ import annotations

import argparse
from typing import Optional

from envforge.tagger import add_tags, remove_tags, get_tags, find_by_tag, clear_tags


def add_tagger_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'tag' subcommand and its sub-actions."""
    parser = subparsers.add_parser("tag", help="Manage snapshot tags")
    tag_sub = parser.add_subparsers(dest="tag_action", required=True)

    # tag add
    p_add = tag_sub.add_parser("add", help="Add tags to a snapshot")
    p_add.add_argument("snapshot_id", help="Snapshot identifier")
    p_add.add_argument("tags", nargs="+", help="Tags to add")

    # tag remove
    p_rm = tag_sub.add_parser("remove", help="Remove tags from a snapshot")
    p_rm.add_argument("snapshot_id", help="Snapshot identifier")
    p_rm.add_argument("tags", nargs="+", help="Tags to remove")

    # tag list
    p_list = tag_sub.add_parser("list", help="List tags for a snapshot")
    p_list.add_argument("snapshot_id", help="Snapshot identifier")

    # tag find
    p_find = tag_sub.add_parser("find", help="Find snapshots by tag")
    p_find.add_argument("tag", help="Tag to search for")

    # tag clear
    p_clear = tag_sub.add_parser("clear", help="Clear all tags from a snapshot")
    p_clear.add_argument("snapshot_id", help="Snapshot identifier")

    parser.set_defaults(func=cmd_tag)


def cmd_tag(args: argparse.Namespace, directory: Optional[str] = None) -> None:
    """Dispatch tag subcommands."""
    action = args.tag_action

    if action == "add":
        updated = add_tags(args.snapshot_id, args.tags, directory=directory)
        print(f"Tags for '{args.snapshot_id}': {', '.join(updated) if updated else '(none)'}")

    elif action == "remove":
        updated = remove_tags(args.snapshot_id, args.tags, directory=directory)
        print(f"Tags for '{args.snapshot_id}': {', '.join(updated) if updated else '(none)'}")

    elif action == "list":
        tags = get_tags(args.snapshot_id, directory=directory)
        if tags:
            print(f"Tags for '{args.snapshot_id}':")
            for tag in tags:
                print(f"  - {tag}")
        else:
            print(f"No tags found for '{args.snapshot_id}'.")

    elif action == "find":
        snapshot_ids = find_by_tag(args.tag, directory=directory)
        if snapshot_ids:
            print(f"Snapshots tagged '{args.tag}':")
            for sid in snapshot_ids:
                print(f"  - {sid}")
        else:
            print(f"No snapshots found with tag '{args.tag}'.")

    elif action == "clear":
        clear_tags(args.snapshot_id, directory=directory)
        print(f"All tags cleared for '{args.snapshot_id}'.")

    else:
        print(f"Unknown tag action: {action}")
