"""CLI entry-point for envforge."""

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
from envforge.validator import validate_snapshot


def cmd_capture(args: argparse.Namespace) -> int:
    snapshot = EnvSnapshot(
        env_vars=capture_env_vars(),
        python_version=capture_python_version(),
        node_version=capture_node_version(),
        pip_packages=capture_pip_packages(),
    )

    if args.validate:
        result = validate_snapshot(snapshot)
        for warning in result.warnings:
            print(f"[warn] {warning}", file=sys.stderr)
        if not result.valid:
            for error in result.errors:
                print(f"[error] {error}", file=sys.stderr)
            print("Snapshot validation failed. Aborting.", file=sys.stderr)
            return 1

    save_snapshot(snapshot, args.output)
    print(f"Snapshot saved to {args.output}")
    return 0


def cmd_reproduce(args: argparse.Namespace) -> int:
    snapshot = load_snapshot(args.input)

    if args.validate:
        result = validate_snapshot(snapshot)
        for warning in result.warnings:
            print(f"[warn] {warning}", file=sys.stderr)
        if not result.valid:
            for error in result.errors:
                print(f"[error] {error}", file=sys.stderr)
            print("Snapshot validation failed. Aborting.", file=sys.stderr)
            return 1

    write_reproduction_script(snapshot, args.output)
    print(f"Reproduction script written to {args.output}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    snapshot = load_snapshot(args.input)
    result = validate_snapshot(snapshot)

    for warning in result.warnings:
        print(f"[warn] {warning}")
    for error in result.errors:
        print(f"[error] {error}")

    if result.valid:
        print("Snapshot is valid.")
        return 0
    else:
        print("Snapshot validation failed.")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envforge", description="Snapshot and reproduce dev environments"
    )
    sub = parser.add_subparsers(dest="command")

    capture_p = sub.add_parser("capture", help="Capture current environment")
    capture_p.add_argument("-o", "--output", default="snapshot.json")
    capture_p.add_argument("--validate", action="store_true", help="Validate before saving")
    capture_p.set_defaults(func=cmd_capture)

    reproduce_p = sub.add_parser("reproduce", help="Generate reproduction script")
    reproduce_p.add_argument("-i", "--input", default="snapshot.json")
    reproduce_p.add_argument("-o", "--output", default="reproduce.sh")
    reproduce_p.add_argument("--validate", action="store_true", help="Validate before reproducing")
    reproduce_p.set_defaults(func=cmd_reproduce)

    validate_p = sub.add_parser("validate", help="Validate a snapshot file")
    validate_p.add_argument("-i", "--input", default="snapshot.json")
    validate_p.set_defaults(func=cmd_validate)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
