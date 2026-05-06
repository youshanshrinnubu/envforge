"""CLI subcommands for snapshot history management."""

import argparse
import sys
from pathlib import Path

from envforge.history import (
    list_history,
    load_history_entry,
    delete_history_entry,
    get_history_dir,
)
from envforge.reproducer import write_reproduction_script


def add_history_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'history' subcommand and its sub-actions."""
    parser = subparsers.add_parser(
        "history", help="Manage snapshot history"
    )
    sub = parser.add_subparsers(dest="history_action", required=True)

    # list
    list_p = sub.add_parser("list", help="List recorded snapshots")
    list_p.add_argument("--history-dir", type=Path, default=None,
                        help="Custom history directory")

    # show
    show_p = sub.add_parser("show", help="Print details of a history entry")
    show_p.add_argument("filename", help="History entry filename")
    show_p.add_argument("--history-dir", type=Path, default=None)

    # reproduce
    rep_p = sub.add_parser("reproduce",
                           help="Generate reproduction script from history entry")
    rep_p.add_argument("filename", help="History entry filename")
    rep_p.add_argument("--output", "-o", default="reproduce.sh",
                       help="Output script path (default: reproduce.sh)")
    rep_p.add_argument("--history-dir", type=Path, default=None)

    # delete
    del_p = sub.add_parser("delete", help="Delete a history entry")
    del_p.add_argument("filename", help="History entry filename")
    del_p.add_argument("--history-dir", type=Path, default=None)

    parser.set_defaults(func=cmd_history)


def cmd_history(args: argparse.Namespace) -> int:
    """Dispatch history sub-actions."""
    action = args.history_action
    hdir = getattr(args, "history_dir", None)

    if action == "list":
        entries = list_history(history_dir=hdir)
        if not entries:
            print("No history entries found.")
            return 0
        print(f"{'FILENAME':<40} {'TIMESTAMP':<20} LABEL")
        print("-" * 72)
        for e in entries:
            print(f"{e['filename']:<40} {e['timestamp']:<20} {e['label']}")
        return 0

    elif action == "show":
        try:
            snap = load_history_entry(args.filename, history_dir=hdir)
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(f"Python : {snap.python_version}")
        print(f"Node   : {snap.node_version}")
        print(f"Shell  : {snap.shell}")
        print(f"Env vars ({len(snap.env_vars)}): {', '.join(list(snap.env_vars)[:5])} ...")
        print(f"Pip packages ({len(snap.pip_packages)}): "
              f"{', '.join(list(snap.pip_packages)[:5])} ...")
        return 0

    elif action == "reproduce":
        try:
            snap = load_history_entry(args.filename, history_dir=hdir)
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        write_reproduction_script(snap, args.output)
        print(f"Reproduction script written to {args.output}")
        return 0

    elif action == "delete":
        try:
            delete_history_entry(args.filename, history_dir=hdir)
            print(f"Deleted history entry: {args.filename}")
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        return 0

    return 0
