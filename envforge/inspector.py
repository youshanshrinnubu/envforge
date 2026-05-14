"""Inspect and describe individual fields of an EnvSnapshot in detail."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from envforge.snapshot import EnvSnapshot


@dataclass
class FieldInspection:
    name: str
    value: Any
    value_type: str
    present: bool
    summary: str
    details: List[str] = field(default_factory=list)


@dataclass
class InspectionReport:
    label: str
    fields: List[FieldInspection] = field(default_factory=list)

    def get(self, name: str) -> Optional[FieldInspection]:
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def present_fields(self) -> List[FieldInspection]:
        return [f for f in self.fields if f.present]

    def missing_fields(self) -> List[FieldInspection]:
        return [f for f in self.fields if not f.present]


def _inspect_python_version(version: Optional[str]) -> FieldInspection:
    present = bool(version)
    summary = version if present else "not captured"
    details = []
    if present:
        parts = version.split(".")
        details.append(f"Major: {parts[0]}" if len(parts) > 0 else "")
        details.append(f"Minor: {parts[1]}" if len(parts) > 1 else "")
        details.append(f"Patch: {parts[2]}" if len(parts) > 2 else "")
        details = [d for d in details if d]
    return FieldInspection(
        name="python_version",
        value=version,
        value_type="str",
        present=present,
        summary=summary,
        details=details,
    )


def _inspect_node_version(version: Optional[str]) -> FieldInspection:
    present = bool(version)
    summary = version if present else "not captured"
    return FieldInspection(
        name="node_version",
        value=version,
        value_type="str",
        present=present,
        summary=summary,
    )


def _inspect_env_vars(env_vars: Dict[str, str]) -> FieldInspection:
    count = len(env_vars)
    present = count > 0
    summary = f"{count} variable(s)" if present else "empty"
    details = [f"{k}={v[:40]}{'...' if len(v) > 40 else ''}" for k, v in list(env_vars.items())[:5]]
    if count > 5:
        details.append(f"... and {count - 5} more")
    return FieldInspection(
        name="env_vars",
        value=env_vars,
        value_type="dict",
        present=present,
        summary=summary,
        details=details,
    )


def _inspect_pip_packages(packages: Dict[str, str]) -> FieldInspection:
    count = len(packages)
    present = count > 0
    summary = f"{count} package(s)" if present else "empty"
    details = [f"{k}=={v}" for k, v in list(packages.items())[:5]]
    if count > 5:
        details.append(f"... and {count - 5} more")
    return FieldInspection(
        name="pip_packages",
        value=packages,
        value_type="dict",
        present=present,
        summary=summary,
        details=details,
    )


def inspect_snapshot(snapshot: EnvSnapshot) -> InspectionReport:
    """Return a detailed InspectionReport for all fields of the snapshot."""
    report = InspectionReport(label=snapshot.label or "(unlabeled)")
    report.fields.append(_inspect_python_version(snapshot.python_version))
    report.fields.append(_inspect_node_version(snapshot.node_version))
    report.fields.append(_inspect_env_vars(snapshot.env_vars))
    report.fields.append(_inspect_pip_packages(snapshot.pip_packages))
    return report
