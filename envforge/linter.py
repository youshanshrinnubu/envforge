"""Lint snapshots for common issues and best practices."""

from dataclasses import dataclass, field
from typing import List
from envforge.snapshot import EnvSnapshot

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"
SEVERITY_INFO = "info"


@dataclass
class LintIssue:
    code: str
    severity: str
    message: str


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == SEVERITY_ERROR]

    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == SEVERITY_WARNING]

    def passed(self) -> bool:
        return len(self.errors()) == 0

    def __bool__(self) -> bool:
        return self.passed()


def lint_python_version(snapshot: EnvSnapshot) -> List[LintIssue]:
    issues = []
    version = snapshot.python_version
    if not version:
        issues.append(LintIssue("L001", SEVERITY_WARNING, "Python version is not set in snapshot."))
    elif not version.replace(".", "").isdigit():
        issues.append(LintIssue("L002", SEVERITY_ERROR, f"Python version '{version}' has an unexpected format."))
    return issues


def lint_pip_packages(snapshot: EnvSnapshot) -> List[LintIssue]:
    issues = []
    unpinned = [name for name, ver in snapshot.pip_packages.items() if not ver or ver == "latest"]
    for name in unpinned:
        issues.append(LintIssue("L003", SEVERITY_WARNING, f"Package '{name}' has no pinned version."))
    if not snapshot.pip_packages:
        issues.append(LintIssue("L004", SEVERITY_INFO, "No pip packages recorded in snapshot."))
    return issues


def lint_env_vars(snapshot: EnvSnapshot) -> List[LintIssue]:
    issues = []
    sensitive_patterns = ["SECRET", "PASSWORD", "TOKEN", "API_KEY", "PRIVATE"]
    for key in snapshot.env_vars:
        for pattern in sensitive_patterns:
            if pattern in key.upper():
                issues.append(LintIssue(
                    "L005", SEVERITY_WARNING,
                    f"Env var '{key}' may contain sensitive data."
                ))
                break
    return issues


def lint_snapshot(snapshot: EnvSnapshot) -> LintResult:
    result = LintResult()
    result.issues.extend(lint_python_version(snapshot))
    result.issues.extend(lint_pip_packages(snapshot))
    result.issues.extend(lint_env_vars(snapshot))
    return result
