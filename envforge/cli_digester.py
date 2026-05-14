"""CLI subcommand for snapshot digest operations."""

import argparse
import sys

from envforge.serializer import load_snapshot, save_snapshot
from envforge.digester import compute_digest, verify_digest, attach_digest, check_attached_digest


def add_digester_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("digest", help="Compute or verify snapshot content digests")
    sub = p.add_subparsers(dest="digest_cmd", required=True)

    # compute
    pc = sub.add_parser("compute", help="Print the digest of a snapshot")
    pc.add_argument("snapshot", help="Path to snapshot JSON file")
    pc.add_argument("--algorithm", default="sha256", choices=["sha256", "sha1", "md5"])

    # verify
    pv = sub.add_parser("verify", help="Verify snapshot against a known digest")
    pv.add_argument("snapshot", help="Path to snapshot JSON file")
    pv.add_argument("expected", help="Expected digest hex string")
    pv.add_argument("--algorithm", default="sha256", choices=["sha256", "sha1", "md5"])

    # attach
    pa = sub.add_parser("attach", help="Compute and embed digest into snapshot file")
    pa.add_argument("snapshot", help="Path to snapshot JSON file")
    pa.add_argument("--algorithm", default="sha256", choices=["sha256", "sha1", "md5"])

    # check
    pk = sub.add_parser("check", help="Verify the digest already embedded in a snapshot")
    pk.add_argument("snapshot", help="Path to snapshot JSON file")

    p.set_defaults(func=cmd_digest)


def cmd_digest(args: argparse.Namespace) -> int:
    snapshot = load_snapshot(args.snapshot)

    if args.digest_cmd == "compute":
        result = compute_digest(snapshot, algorithm=args.algorithm)
        print(f"{result.algorithm}:{result.digest}  {args.snapshot}")
        return 0

    if args.digest_cmd == "verify":
        result = verify_digest(snapshot, expected=args.expected, algorithm=args.algorithm)
        if result.verified:
            print(f"OK  digest matches ({result.algorithm})")
            return 0
        else:
            print(f"MISMATCH  expected={result.expected}  got={result.digest}", file=sys.stderr)
            return 1

    if args.digest_cmd == "attach":
        digest = attach_digest(snapshot, algorithm=args.algorithm)
        save_snapshot(snapshot, args.snapshot)
        print(f"Attached {args.algorithm} digest: {digest}")
        return 0

    if args.digest_cmd == "check":
        try:
            result = check_attached_digest(snapshot)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
        if result.verified:
            print(f"OK  embedded digest is valid ({result.algorithm})")
            return 0
        else:
            print(f"TAMPERED  embedded={result.expected}  computed={result.digest}", file=sys.stderr)
            return 1

    return 0
