"""CLI sub-commands for envforge watchdog (drift detection)."""
from __future__ import annotations

import argparse
import sys

from envforge.serializer import load_snapshot
from envforge.watchdog import detect_drift


def add_watchdog_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "watchdog",
        help="Detect drift between a snapshot and the live environment",
    )
    p.add_argument("snapshot", help="Path to the snapshot JSON file")
    p.add_argument(
        "--notify",
        action="store_true",
        default=False,
        help="Send a notification if drift is detected",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 when drift is detected",
    )
    p.set_defaults(func=cmd_watchdog)


def cmd_watchdog(args: argparse.Namespace) -> int:
    try:
        snapshot = load_snapshot(args.snapshot)
    except FileNotFoundError:
        print(f"error: snapshot file not found: {args.snapshot}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not load snapshot: {exc}", file=sys.stderr)
        return 2

    report = detect_drift(snapshot, notify_on_drift=args.notify)

    label = report.snapshot_label
    if not report.has_drift:
        print(f"[watchdog] No drift detected for '{label}'.")
        return 0

    print(f"[watchdog] Drift detected for '{label}': {report.summary}")
    if report.python_version_changed:
        print("  • Python version changed")
    for var in report.added_env_vars:
        print(f"  + env: {var}")
    for var in report.removed_env_vars:
        print(f"  - env: {var}")
    for var in report.changed_env_vars:
        print(f"  ~ env: {var}")
    for pkg in report.added_packages:
        print(f"  + pkg: {pkg}")
    for pkg in report.removed_packages:
        print(f"  - pkg: {pkg}")
    for pkg in report.changed_packages:
        print(f"  ~ pkg: {pkg}")

    return 1 if args.exit_code else 0
