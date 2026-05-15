"""envforge.sampler — Extract a random or deterministic sample of env vars and packages from a snapshot."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional

from envforge.snapshot import EnvSnapshot


@dataclass
class SampleResult:
    snapshot: Optional[EnvSnapshot]
    sampled_env_vars: int = 0
    sampled_packages: int = 0
    warnings: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.snapshot is not None


def _copy_snapshot(snap: EnvSnapshot) -> EnvSnapshot:
    return EnvSnapshot(
        env_vars=dict(snap.env_vars),
        python_version=snap.python_version,
        node_version=snap.node_version,
        pip_packages=list(snap.pip_packages),
        label=snap.label,
    )


def sample_env_vars(
    snap: EnvSnapshot,
    n: int,
    seed: Optional[int] = None,
) -> SampleResult:
    """Return a new snapshot containing at most *n* randomly chosen env vars."""
    rng = random.Random(seed)
    keys = list(snap.env_vars.keys())
    chosen = rng.sample(keys, min(n, len(keys)))
    out = _copy_snapshot(snap)
    out.env_vars = {k: snap.env_vars[k] for k in chosen}
    warnings: List[str] = []
    if n > len(keys):
        warnings.append(
            f"Requested {n} env vars but only {len(keys)} available; returning all."
        )
    return SampleResult(
        snapshot=out,
        sampled_env_vars=len(chosen),
        sampled_packages=len(out.pip_packages),
        warnings=warnings,
    )


def sample_pip_packages(
    snap: EnvSnapshot,
    n: int,
    seed: Optional[int] = None,
) -> SampleResult:
    """Return a new snapshot containing at most *n* randomly chosen pip packages."""
    rng = random.Random(seed)
    chosen = rng.sample(snap.pip_packages, min(n, len(snap.pip_packages)))
    out = _copy_snapshot(snap)
    out.pip_packages = list(chosen)
    warnings: List[str] = []
    if n > len(snap.pip_packages):
        warnings.append(
            f"Requested {n} packages but only {len(snap.pip_packages)} available; returning all."
        )
    return SampleResult(
        snapshot=out,
        sampled_env_vars=len(out.env_vars),
        sampled_packages=len(chosen),
        warnings=warnings,
    )


def sample_snapshot(
    snap: EnvSnapshot,
    n_env: int,
    n_pkg: int,
    seed: Optional[int] = None,
) -> SampleResult:
    """Sample both env vars and pip packages from *snap*."""
    r1 = sample_env_vars(snap, n_env, seed=seed)
    assert r1.snapshot is not None
    r2 = sample_pip_packages(r1.snapshot, n_pkg, seed=seed)
    assert r2.snapshot is not None
    return SampleResult(
        snapshot=r2.snapshot,
        sampled_env_vars=r1.sampled_env_vars,
        sampled_packages=r2.sampled_packages,
        warnings=r1.warnings + r2.warnings,
    )
