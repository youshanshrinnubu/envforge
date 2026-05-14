"""Snapshot digester: compute and verify content hashes for snapshots."""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional

from envforge.snapshot import EnvSnapshot


@dataclass
class DigestResult:
    snapshot_label: str
    algorithm: str
    digest: str
    verified: Optional[bool] = None  # None = not checked, True/False = result
    expected: Optional[str] = None

    def __bool__(self) -> bool:
        if self.verified is None:
            return True
        return self.verified


def _snapshot_canonical(snapshot: EnvSnapshot) -> bytes:
    """Produce a stable, canonical byte representation of the snapshot."""
    data = {
        "label": snapshot.label or "",
        "python_version": snapshot.python_version or "",
        "node_version": snapshot.node_version or "",
        "env_vars": dict(sorted(snapshot.env_vars.items())),
        "pip_packages": sorted(snapshot.pip_packages),
        "extra": dict(sorted((snapshot.extra or {}).items())),
    }
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_digest(snapshot: EnvSnapshot, algorithm: str = "sha256") -> DigestResult:
    """Compute a content digest for the given snapshot."""
    supported = {"sha256", "sha1", "md5"}
    if algorithm not in supported:
        raise ValueError(f"Unsupported algorithm '{algorithm}'. Choose from: {supported}")

    canonical = _snapshot_canonical(snapshot)
    h = hashlib.new(algorithm, canonical)
    digest = h.hexdigest()

    return DigestResult(
        snapshot_label=snapshot.label or "(unlabeled)",
        algorithm=algorithm,
        digest=digest,
    )


def verify_digest(snapshot: EnvSnapshot, expected: str, algorithm: str = "sha256") -> DigestResult:
    """Verify a snapshot against a known digest string."""
    result = compute_digest(snapshot, algorithm=algorithm)
    result.verified = result.digest == expected
    result.expected = expected
    return result


def attach_digest(snapshot: EnvSnapshot, algorithm: str = "sha256") -> str:
    """Compute digest and store it in snapshot.extra['digest']. Returns the digest."""
    result = compute_digest(snapshot, algorithm=algorithm)
    if snapshot.extra is None:
        snapshot.extra = {}
    snapshot.extra["digest"] = result.digest
    snapshot.extra["digest_algorithm"] = algorithm
    return result.digest


def check_attached_digest(snapshot: EnvSnapshot) -> DigestResult:
    """Verify the digest stored in snapshot.extra against the current content."""
    extra = snapshot.extra or {}
    expected = extra.get("digest")
    algorithm = extra.get("digest_algorithm", "sha256")

    if not expected:
        raise ValueError("No digest attached to this snapshot (missing snapshot.extra['digest'])")

    # Temporarily strip digest fields so they don't affect the hash
    stored_extra = dict(extra)
    snapshot.extra = {k: v for k, v in extra.items() if k not in ("digest", "digest_algorithm")}
    try:
        result = verify_digest(snapshot, expected=expected, algorithm=algorithm)
    finally:
        snapshot.extra = stored_extra

    return result
