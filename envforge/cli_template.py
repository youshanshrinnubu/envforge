"""CLI subcommands for template management in envforge."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envforge.template import (
    save_template,
    load_template,
    list_templates,
    delete_template,
)
from envforge.serializer import load_snapshot
from envforge.reproducer import write_reproduction_script


def add_template_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'template' subcommand group."""
    parser = subparsers.add_parser("template", help="Manage named snapshot templates")
    sub = parser.add_subparsers(dest="template_cmd", required=True)

    # template save
    p_save = sub.add_parser("save", help="Save a snapshot as a named template")
    p_save.add_argument("name", help="Template name")
    p_save.add_argument("snapshot", help="Path to snapshot JSON file")

    # template load
    p_load = sub.add_parser("load", help="Generate reproduction script from a template")
    p_load.add_argument("name", help="Template name")
    p_load.add_argument("-o", "--output", default="reproduce.sh", help="Output script path")

    # template list
    sub.add_parser("list", help="List available templates")

    # template delete
    p_del = sub.add_parser("delete", help="Delete a named template")
    p_del.add_argument("name", help="Template name to delete")

    parser.set_defaults(func=cmd_template)


def cmd_template(args: argparse.Namespace) -> int:
    """Dispatch template subcommands."""
    if args.template_cmd == "save":
        snapshot = load_snapshot(Path(args.snapshot))
        path = save_template(args.name, snapshot)
        print(f"Template '{args.name}' saved to {path}")

    elif args.template_cmd == "load":
        try:
            snapshot = load_template(args.name)
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        write_reproduction_script(snapshot, Path(args.output))
        print(f"Reproduction script written to {args.output}")

    elif args.template_cmd == "list":
        names = list_templates()
        if names:
            print("Available templates:")
            for name in names:
                print(f"  {name}")
        else:
            print("No templates saved yet.")

    elif args.template_cmd == "delete":
        deleted = delete_template(args.name)
        if deleted:
            print(f"Template '{args.name}' deleted.")
        else:
            print(f"Template '{args.name}' not found.", file=sys.stderr)
            return 1

    return 0
