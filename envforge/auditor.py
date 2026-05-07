"""Audit log for envforge snapshot operations."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

AUDIT_LOG_ENV = "ENVFORGE_AUDIT_DIR"
DEFAULT_AUDIT_DIR = Path.home() / ".envforge" / "audit"


@dataclass
class AuditEntry:
    timestamp: float
    operation: str
    snapshot_name: str
    details: dict = field(default_factory=dict)
    user: str = ""


def get_audit_dir() -> Path:
    custom = os.environ.get(AUDIT_LOG_ENV)
    return Path(custom) if custom else DEFAULT_AUDIT_DIR


def _audit_log_path(audit_dir: Path) -> Path:
    audit_dir.mkdir(parents=True, exist_ok=True)
    return audit_dir / "audit.log"


def record_audit(operation: str, snapshot_name: str, details: Optional[dict] = None,
                 audit_dir: Optional[Path] = None) -> AuditEntry:
    """Append an audit entry to the audit log."""
    audit_dir = audit_dir or get_audit_dir()
    entry = AuditEntry(
        timestamp=time.time(),
        operation=operation,
        snapshot_name=snapshot_name,
        details=details or {},
        user=os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
    )
    log_path = _audit_log_path(audit_dir)
    with log_path.open("a") as fh:
        fh.write(json.dumps(entry.__dict__) + "\n")
    return entry


def load_audit_log(audit_dir: Optional[Path] = None) -> List[AuditEntry]:
    """Load all audit entries from the log file."""
    audit_dir = audit_dir or get_audit_dir()
    log_path = _audit_log_path(audit_dir)
    if not log_path.exists():
        return []
    entries = []
    with log_path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                data = json.loads(line)
                entries.append(AuditEntry(**data))
    return entries


def clear_audit_log(audit_dir: Optional[Path] = None) -> int:
    """Remove all audit entries; returns count of deleted entries."""
    entries = load_audit_log(audit_dir)
    audit_dir = audit_dir or get_audit_dir()
    log_path = _audit_log_path(audit_dir)
    log_path.write_text("")
    return len(entries)


def filter_audit_log(operation: Optional[str] = None, snapshot_name: Optional[str] = None,
                     audit_dir: Optional[Path] = None) -> List[AuditEntry]:
    """Return entries optionally filtered by operation and/or snapshot name."""
    entries = load_audit_log(audit_dir)
    if operation:
        entries = [e for e in entries if e.operation == operation]
    if snapshot_name:
        entries = [e for e in entries if e.snapshot_name == snapshot_name]
    return entries
