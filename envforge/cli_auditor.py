"""CLI subcommands for the envforge audit log."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from envforge.auditor import clear_audit_log, filter_audit_log, load_audit_log


def add_auditor_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("audit", help="View and manage the audit log")
    sub = parser.add_subparsers(dest="audit_cmd", required=True)

    # list
    list_p = sub.add_parser("list", help="List audit log entries")
    list_p.add_argument("--operation", "-o", default=None, help="Filter by operation")
    list_p.add_argument("--snapshot", "-s", default=None, help="Filter by snapshot name")
    list_p.add_argument("--audit-dir", default=None, help="Custom audit directory")

    # clear
    clear_p = sub.add_parser("clear", help="Clear all audit log entries")
    clear_p.add_argument("--audit-dir", default=None, help="Custom audit directory")
    clear_p.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

    parser.set_defaults(func=cmd_audit)


def _fmt_entry(entry) -> str:
    ts = datetime.fromtimestamp(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
    return f"[{ts}] {entry.operation:12s}  {entry.snapshot_name}  user={entry.user}  {entry.details or ''}"


def cmd_audit(args: argparse.Namespace) -> int:
    audit_dir: Optional[Path] = Path(args.audit_dir) if getattr(args, "audit_dir", None) else None

    if args.audit_cmd == "list":
        entries = filter_audit_log(
            operation=getattr(args, "operation", None),
            snapshot_name=getattr(args, "snapshot", None),
            audit_dir=audit_dir,
        )
        if not entries:
            print("No audit entries found.")
            return 0
        for e in entries:
            print(_fmt_entry(e))
        return 0

    if args.audit_cmd == "clear":
        if not getattr(args, "yes", False):
            answer = input("Clear all audit entries? [y/N] ").strip().lower()
            if answer != "y":
                print("Aborted.")
                return 1
        count = clear_audit_log(audit_dir=audit_dir)
        print(f"Cleared {count} audit entries.")
        return 0

    print(f"Unknown audit subcommand: {args.audit_cmd}", file=sys.stderr)
    return 1
