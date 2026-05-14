"""CLI sub-commands for snapshot annotations."""

from __future__ import annotations

import argparse
import sys

from envforge.annotator import (
    add_annotation,
    clear_annotations,
    get_annotations,
    remove_annotation,
)
from envforge.serializer import load_snapshot, save_snapshot


def add_annotator_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("annotate", help="Manage snapshot annotations")
    sub = p.add_subparsers(dest="annotate_cmd", required=True)

    # list
    ls = sub.add_parser("list", help="List annotations on a snapshot")
    ls.add_argument("snapshot", help="Path to snapshot file")

    # add
    add = sub.add_parser("add", help="Add an annotation")
    add.add_argument("snapshot", help="Path to snapshot file")
    add.add_argument("text", help="Annotation text")
    add.add_argument("--author", default="unknown", help="Author name")

    # remove
    rm = sub.add_parser("remove", help="Remove annotation by index")
    rm.add_argument("snapshot", help="Path to snapshot file")
    rm.add_argument("index", type=int, help="Zero-based annotation index")

    # clear
    cl = sub.add_parser("clear", help="Remove all annotations")
    cl.add_argument("snapshot", help="Path to snapshot file")

    p.set_defaults(func=cmd_annotate)


def cmd_annotate(args: argparse.Namespace) -> int:
    snapshot = load_snapshot(args.snapshot)

    if args.annotate_cmd == "list":
        notes = get_annotations(snapshot)
        if not notes:
            print("No annotations.")
        for i, note in enumerate(notes):
            print(f"[{i}] ({note.author} @ {note.created_at})  {note.text}")
        return 0

    if args.annotate_cmd == "add":
        note = add_annotation(snapshot, args.text, args.author)
        save_snapshot(snapshot, args.snapshot)
        print(f"Annotation added: {note.text!r} by {note.author}")
        return 0

    if args.annotate_cmd == "remove":
        ok = remove_annotation(snapshot, args.index)
        if not ok:
            print(f"No annotation at index {args.index}.", file=sys.stderr)
            return 1
        save_snapshot(snapshot, args.snapshot)
        print(f"Annotation {args.index} removed.")
        return 0

    if args.annotate_cmd == "clear":
        count = clear_annotations(snapshot)
        save_snapshot(snapshot, args.snapshot)
        print(f"Cleared {count} annotation(s).")
        return 0

    return 1
