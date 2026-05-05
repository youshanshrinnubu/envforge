"""Minimal CLI for envforge: snapshot and reproduce dev environments."""

from __future__ import annotations

import argparse
import sys

from envforge.reproducer import write_reproduction_script
from envforge.serializer import load_snapshot, save_snapshot
from envforge.snapshot import (
    EnvSnapshot,
    capture_env_vars,
    capture_node_version,
    capture_pip_packages,
    capture_python_version,
)


def cmd_capture(args: argparse.Namespace) -> int:
    """Capture the current environment and save it to a JSON snapshot file."""
    snapshot = EnvSnapshot(
        env_vars=capture_env_vars(exclude=set(args.exclude or [])),
        python_version=capture_python_version(),
        node_version=capture_node_version(),
        pip_packages=capture_pip_packages(),
    )
    save_snapshot(snapshot, args.output)
    print(f"Snapshot saved to {args.output}")
    return 0


def cmd_reproduce(args: argparse.Namespace) -> int:
    """Load a snapshot and generate a bash reproduction script."""
    snapshot = load_snapshot(args.snapshot)
    write_reproduction_script(
        snapshot,
        output_path=args.output,
        include_env=not args.no_env,
        include_packages=not args.no_packages,
    )
    print(f"Reproduction script written to {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envforge",
        description="Snapshot and reproduce dev environments.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # capture sub-command
    cap = sub.add_parser("capture", help="Capture the current environment.")
    cap.add_argument(
        "-o", "--output", default="snapshot.json",
        help="Output snapshot file (default: snapshot.json)",
    )
    cap.add_argument(
        "--exclude", nargs="*", metavar="KEY",
        help="Additional env-var keys to exclude.",
    )
    cap.set_defaults(func=cmd_capture)

    # reproduce sub-command
    rep = sub.add_parser("reproduce", help="Generate a reproduction script.")
    rep.add_argument("snapshot", help="Path to snapshot JSON file.")
    rep.add_argument(
        "-o", "--output", default="reproduce.sh",
        help="Output script path (default: reproduce.sh)",
    )
    rep.add_argument(
        "--no-env", action="store_true",
        help="Omit environment variable exports.",
    )
    rep.add_argument(
        "--no-packages", action="store_true",
        help="Omit pip install commands.",
    )
    rep.set_defaults(func=cmd_reproduce)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
