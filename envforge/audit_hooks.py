"""Hooks that automatically record audit entries for key envforge operations."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envforge.auditor import record_audit
from envforge.snapshot import EnvSnapshot


def on_capture(snapshot: EnvSnapshot, output_path: Optional[Path] = None) -> None:
    """Call after a snapshot is captured."""
    record_audit(
        operation="capture",
        snapshot_name=getattr(snapshot, "name", str(output_path or "unknown")),
        details={"path": str(output_path)} if output_path else {},
    )


def on_reproduce(snapshot: EnvSnapshot, script_path: Optional[Path] = None) -> None:
    """Call after a reproduction script is generated."""
    record_audit(
        operation="reproduce",
        snapshot_name=getattr(snapshot, "name", "unknown"),
        details={"script": str(script_path)} if script_path else {},
    )


def on_export(snapshot: EnvSnapshot, fmt: str, output_path: Optional[Path] = None) -> None:
    """Call after a snapshot is exported."""
    record_audit(
        operation="export",
        snapshot_name=getattr(snapshot, "name", "unknown"),
        details={"format": fmt, "path": str(output_path)} if output_path else {"format": fmt},
    )


def on_validate(snapshot: EnvSnapshot, passed: bool) -> None:
    """Call after a snapshot is validated."""
    record_audit(
        operation="validate",
        snapshot_name=getattr(snapshot, "name", "unknown"),
        details={"passed": passed},
    )


def on_merge(base_name: str, other_name: str, result_name: str) -> None:
    """Call after two snapshots are merged."""
    record_audit(
        operation="merge",
        snapshot_name=result_name,
        details={"base": base_name, "other": other_name},
    )
