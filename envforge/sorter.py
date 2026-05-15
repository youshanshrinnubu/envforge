"""Sort snapshot fields (env vars, pip packages) by various criteria."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envforge.snapshot import EnvSnapshot


SORTABLE_FIELDS = ("env_vars", "pip_packages")
SORT_ORDERS = ("asc", "desc")


@dataclass
class SortResult:
    snapshot: EnvSnapshot
    fields_sorted: List[str] = field(default_factory=list)
    order: str = "asc"

    def __bool__(self) -> bool:
        return bool(self.fields_sorted)


def _copy_snapshot(snapshot: EnvSnapshot) -> EnvSnapshot:
    return EnvSnapshot(
        env_vars=dict(snapshot.env_vars),
        python_version=snapshot.python_version,
        node_version=snapshot.node_version,
        pip_packages=list(snapshot.pip_packages),
        label=snapshot.label,
    )


def sort_env_vars(
    snapshot: EnvSnapshot,
    order: str = "asc",
    key: Optional[str] = None,
) -> SortResult:
    """Return a new snapshot with env_vars sorted by key name."""
    reverse = order == "desc"
    result = _copy_snapshot(snapshot)
    sort_fn = (lambda k: k[0]) if key is None else (lambda k: k[1])
    result.env_vars = dict(sorted(result.env_vars.items(), key=sort_fn, reverse=reverse))
    return SortResult(
        snapshot=result,
        fields_sorted=["env_vars"] if result.env_vars else [],
        order=order,
    )


def sort_pip_packages(
    snapshot: EnvSnapshot,
    order: str = "asc",
    key: str = "name",
) -> SortResult:
    """Return a new snapshot with pip_packages sorted by name or version."""
    reverse = order == "desc"
    result = _copy_snapshot(snapshot)

    def _pkg_key(pkg):
        if isinstance(pkg, dict):
            return pkg.get(key, "")
        return str(pkg)

    result.pip_packages = sorted(result.pip_packages, key=_pkg_key, reverse=reverse)
    return SortResult(
        snapshot=result,
        fields_sorted=["pip_packages"] if result.pip_packages else [],
        order=order,
    )


def sort_snapshot(
    snapshot: EnvSnapshot,
    order: str = "asc",
    fields: Optional[List[str]] = None,
) -> SortResult:
    """Sort all (or selected) sortable fields of a snapshot."""
    target_fields = fields if fields is not None else list(SORTABLE_FIELDS)
    current = _copy_snapshot(snapshot)
    sorted_fields: List[str] = []

    if "env_vars" in target_fields:
        r = sort_env_vars(current, order=order)
        current = r.snapshot
        sorted_fields.extend(r.fields_sorted)

    if "pip_packages" in target_fields:
        r = sort_pip_packages(current, order=order)
        current = r.snapshot
        sorted_fields.extend(r.fields_sorted)

    return SortResult(snapshot=current, fields_sorted=sorted_fields, order=order)
