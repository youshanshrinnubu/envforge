"""Redactor: mask sensitive values in EnvSnapshot before sharing or exporting."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from envforge.snapshot import EnvSnapshot

# Default patterns whose values should be redacted
DEFAULT_SENSITIVE_PATTERNS: List[str] = [
    r".*SECRET.*",
    r".*PASSWORD.*",
    r".*PASSWD.*",
    r".*TOKEN.*",
    r".*API_KEY.*",
    r".*PRIVATE_KEY.*",
    r".*CREDENTIALS.*",
    r".*AUTH.*",
]

REDACT_PLACEHOLDER = "**REDACTED**"


@dataclass
class RedactResult:
    snapshot: EnvSnapshot
    redacted_keys: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return len(self.redacted_keys) > 0


def _compile_patterns(patterns: List[str]) -> List[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


def _is_sensitive(key: str, compiled: List[re.Pattern]) -> bool:
    return any(p.fullmatch(key) for p in compiled)


def redact_env_vars(
    snapshot: EnvSnapshot,
    patterns: Optional[List[str]] = None,
    placeholder: str = REDACT_PLACEHOLDER,
) -> RedactResult:
    """Return a new snapshot with sensitive env var values masked."""
    active_patterns = _compile_patterns(patterns if patterns is not None else DEFAULT_SENSITIVE_PATTERNS)
    redacted_keys: List[str] = []
    new_env: dict = {}

    for key, value in snapshot.env_vars.items():
        if _is_sensitive(key, active_patterns):
            new_env[key] = placeholder
            redacted_keys.append(key)
        else:
            new_env[key] = value

    new_snapshot = EnvSnapshot(
        label=snapshot.label,
        env_vars=new_env,
        python_version=snapshot.python_version,
        node_version=snapshot.node_version,
        pip_packages=list(snapshot.pip_packages),
        extra=dict(snapshot.extra) if hasattr(snapshot, "extra") else {},
    )
    return RedactResult(snapshot=new_snapshot, redacted_keys=sorted(redacted_keys))


def redact_snapshot(
    snapshot: EnvSnapshot,
    patterns: Optional[List[str]] = None,
    placeholder: str = REDACT_PLACEHOLDER,
) -> RedactResult:
    """Top-level convenience wrapper that applies all redaction passes."""
    return redact_env_vars(snapshot, patterns=patterns, placeholder=placeholder)
