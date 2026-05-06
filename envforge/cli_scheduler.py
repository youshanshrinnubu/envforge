"""CLI subcommands for managing snapshot schedules."""

import argparse
import sys
from typing import List

from envforge.scheduler import (
    add_schedule,
    remove_schedule,
    list_schedules,
    due_schedules,
)


def add_scheduler_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("schedule", help="Manage periodic snapshot schedules")
    sub = parser.add_subparsers(dest="schedule_cmd", required=True)

    p_add = sub.add_parser("add", help="Add a new schedule entry")
    p_add.add_argument("name", help="Unique schedule name")
    p_add.add_argument("--interval", type=int, required=True,
                       help="Capture interval in seconds")
    p_add.add_argument("--output-dir", required=True,
                       help="Directory to save captured snapshots")
    p_add.add_argument("--tags", nargs="*", default=[],
                       help="Optional tags to attach")

    p_rm = sub.add_parser("remove", help="Remove a schedule entry")
    p_rm.add_argument("name", help="Schedule name to remove")

    sub.add_parser("list", help="List all schedule entries")
    sub.add_parser("due", help="List schedules that are due to run")

    parser.set_defaults(func=cmd_schedule)


def cmd_schedule(args: argparse.Namespace) -> int:
    schedule_file = getattr(args, "schedule_file", None)
    kwargs = {"path": schedule_file} if schedule_file else {}

    if args.schedule_cmd == "add":
        try:
            entry = add_schedule(
                name=args.name,
                interval_seconds=args.interval,
                output_dir=args.output_dir,
                tags=args.tags,
                **kwargs,
            )
            print(f"Schedule '{entry.name}' added (every {entry.interval_seconds}s).")
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    elif args.schedule_cmd == "remove":
        removed = remove_schedule(args.name, **kwargs)
        if removed:
            print(f"Schedule '{args.name}' removed.")
        else:
            print(f"No schedule named '{args.name}'.", file=sys.stderr)
            return 1

    elif args.schedule_cmd == "list":
        entries = list_schedules(**kwargs)
        if not entries:
            print("No schedules defined.")
        for e in entries:
            status = "enabled" if e.enabled else "disabled"
            last = f"{e.last_run:.0f}" if e.last_run else "never"
            print(f"  {e.name}: every {e.interval_seconds}s, "
                  f"output={e.output_dir}, last_run={last}, {status}")

    elif args.schedule_cmd == "due":
        entries = due_schedules(**kwargs)
        if not entries:
            print("No schedules are due.")
        for e in entries:
            print(f"  {e.name} (every {e.interval_seconds}s) is due.")

    return 0
