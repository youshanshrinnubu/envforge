"""CLI sub-command for snapshot transformations."""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, Optional

from envforge.serializer import load_snapshot, save_snapshot
from envforge.transformer import apply_transforms


def add_transformer_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("transform", help="Apply transformations to a snapshot")
    p.add_argument("snapshot", help="Path to the input snapshot JSON file")
    p.add_argument("--output", "-o", help="Write result to this file (default: overwrite input)")
    p.add_argument(
        "--uppercase-keys",
        action="store_true",
        help="Convert all env var keys to uppercase",
    )
    p.add_argument(
        "--strip-env-prefix",
        metavar="PREFIX",
        help="Remove env vars whose keys start with PREFIX",
    )
    p.add_argument(
        "--drop-unpinned-packages",
        action="store_true",
        help="Remove pip packages that have no pinned version",
    )
    p.set_defaults(func=cmd_transform)


def cmd_transform(args: argparse.Namespace) -> int:
    try:
        snapshot = load_snapshot(args.snapshot)
    except FileNotFoundError:
        print(f"Error: file not found: {args.snapshot}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading snapshot: {exc}", file=sys.stderr)
        return 1

    env_transformer = None
    pkg_transformer = None

    transformers = []

    if args.uppercase_keys:
        def _upper(k: str, v: str) -> Optional[str]:
            return v  # value unchanged; key uppercasing handled via wrapper
        # We need a wrapper that also renames keys — use a class approach.
        def _upper_env(k: str, v: str) -> Optional[str]:
            return v  # keys are already uppercased via env_vars rebuild below
        transformers.append(("uppercase-keys", args.uppercase_keys))

    prefix = getattr(args, "strip_env_prefix", None)

    def _env_transform(k: str, v: str) -> Optional[str]:
        if prefix and k.startswith(prefix):
            return None
        return v

    env_transformer = _env_transform

    if args.uppercase_keys:
        _base_env = env_transformer

        def _env_transform_upper(k: str, v: str) -> Optional[str]:  # type: ignore[misc]
            result = _base_env(k, v)
            return result  # value kept; key mutation done post-hoc

        env_transformer = _env_transform_upper

    if args.drop_unpinned_packages:
        def _pkg_transform(pkg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            version = pkg.get("version") or pkg.get("pinned_version")
            if not version or version in ("unknown", ""):
                return None
            return pkg
        pkg_transformer = _pkg_transform

    result = apply_transforms(snapshot, env_transformer=env_transformer, pkg_transformer=pkg_transformer)

    if args.uppercase_keys:
        result.snapshot.env_vars = {
            k.upper(): v for k, v in result.snapshot.env_vars.items()
        }

    out_path = args.output or args.snapshot
    try:
        save_snapshot(result.snapshot, out_path)
    except Exception as exc:  # noqa: BLE001
        print(f"Error saving snapshot: {exc}", file=sys.stderr)
        return 1

    print(f"Transformed snapshot saved to {out_path}")
    print(f"  Applied: {len(result.applied)} change(s)")
    print(f"  Skipped/dropped: {len(result.skipped)} item(s)")
    return 0
