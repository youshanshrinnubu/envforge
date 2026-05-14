"""CLI subcommand for stripping fields from a snapshot."""

import argparse
import sys

from envforge.serializer import load_snapshot, save_snapshot
from envforge.stripper import strip_snapshot


def add_stripper_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("strip", help="Strip fields from a snapshot")
    p.add_argument("snapshot", help="Path to the snapshot file")
    p.add_argument("-o", "--output", default=None, help="Output file (default: overwrite input)")
    p.add_argument("--env-vars", action="store_true", help="Strip all environment variables")
    p.add_argument("--pip-packages", action="store_true", help="Strip all pip packages")
    p.add_argument("--versions", action="store_true", help="Strip python and node version fields")
    p.add_argument(
        "--keep-only-keys",
        nargs="+",
        metavar="KEY",
        default=None,
        help="Keep only these env var keys (ignored if --env-vars is set)",
    )
    p.set_defaults(func=cmd_strip)


def cmd_strip(args: argparse.Namespace) -> int:
    try:
        snap = load_snapshot(args.snapshot)
    except FileNotFoundError:
        print(f"Error: snapshot file not found: {args.snapshot}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading snapshot: {exc}", file=sys.stderr)
        return 1

    if not any([args.env_vars, args.pip_packages, args.versions, args.keep_only_keys]):
        print("Nothing to strip. Use --env-vars, --pip-packages, --versions, or --keep-only-keys.",
              file=sys.stderr)
        return 1

    result = strip_snapshot(
        snap,
        env_vars=args.env_vars,
        pip_packages=args.pip_packages,
        versions=args.versions,
        keep_only_keys=args.keep_only_keys,
    )

    out_path = args.output or args.snapshot
    try:
        save_snapshot(result.snapshot, out_path)
    except Exception as exc:  # noqa: BLE001
        print(f"Error saving snapshot: {exc}", file=sys.stderr)
        return 1

    if result.stripped_fields:
        print(f"Stripped fields: {', '.join(result.stripped_fields)}")
        print(f"  env_vars  : {result.original_env_var_count} -> {len(result.snapshot.env_vars)}")
        print(f"  packages  : {result.original_package_count} -> {len(result.snapshot.pip_packages)}")
    else:
        print("No fields were stripped (snapshot unchanged).")

    print(f"Saved to: {out_path}")
    return 0
