"""Tests for envforge.linter module."""

import pytest
from envforge.snapshot import EnvSnapshot
from envforge.linter import (
    lint_snapshot, lint_python_version, lint_pip_packages, lint_env_vars,
    LintResult, LintIssue, SEVERITY_ERROR, SEVERITY_WARNING, SEVERITY_INFO,
)


@pytest.fixture
def clean_snapshot():
    return EnvSnapshot(
        python_version="3.11.4",
        node_version="18.0.0",
        pip_packages={"requests": "2.31.0", "flask": "3.0.0"},
        env_vars={"HOME": "/home/user", "PATH": "/usr/bin"},
        shell="bash",
    )


def test_lint_result_passed_when_no_errors():
    result = LintResult(issues=[LintIssue("L004", SEVERITY_INFO, "info")])
    assert result.passed() is True
    assert bool(result) is True


def test_lint_result_fails_on_error():
    result = LintResult(issues=[LintIssue("L002", SEVERITY_ERROR, "bad version")])
    assert result.passed() is False
    assert bool(result) is False


def test_lint_result_errors_and_warnings(clean_snapshot):
    result = lint_snapshot(clean_snapshot)
    assert isinstance(result.errors(), list)
    assert isinstance(result.warnings(), list)


def test_clean_snapshot_has_no_errors(clean_snapshot):
    result = lint_snapshot(clean_snapshot)
    assert result.passed()
    assert result.errors() == []


def test_missing_python_version_warns():
    snap = EnvSnapshot(python_version="", node_version=None,
                       pip_packages={}, env_vars={}, shell="bash")
    issues = lint_python_version(snap)
    codes = [i.code for i in issues]
    assert "L001" in codes


def test_invalid_python_version_format_errors():
    snap = EnvSnapshot(python_version="not-a-version", node_version=None,
                       pip_packages={}, env_vars={}, shell="bash")
    issues = lint_python_version(snap)
    codes = [i.code for i in issues]
    assert "L002" in codes
    severities = [i.severity for i in issues if i.code == "L002"]
    assert SEVERITY_ERROR in severities


def test_unpinned_package_warns():
    snap = EnvSnapshot(python_version="3.11.4", node_version=None,
                       pip_packages={"requests": "latest", "flask": "3.0.0"},
                       env_vars={}, shell="bash")
    issues = lint_pip_packages(snap)
    codes = [i.code for i in issues]
    assert "L003" in codes
    msgs = [i.message for i in issues if i.code == "L003"]
    assert any("requests" in m for m in msgs)


def test_no_packages_info():
    snap = EnvSnapshot(python_version="3.11.4", node_version=None,
                       pip_packages={}, env_vars={}, shell="bash")
    issues = lint_pip_packages(snap)
    codes = [i.code for i in issues]
    assert "L004" in codes
    severities = [i.severity for i in issues if i.code == "L004"]
    assert SEVERITY_INFO in severities


def test_sensitive_env_var_warns():
    snap = EnvSnapshot(python_version="3.11.4", node_version=None,
                       pip_packages={}, env_vars={"GITHUB_TOKEN": "abc123"}, shell="bash")
    issues = lint_env_vars(snap)
    codes = [i.code for i in issues]
    assert "L005" in codes


def test_non_sensitive_env_var_no_warning():
    snap = EnvSnapshot(python_version="3.11.4", node_version=None,
                       pip_packages={}, env_vars={"HOME": "/home/user"}, shell="bash")
    issues = lint_env_vars(snap)
    assert all(i.code != "L005" for i in issues)


def test_full_lint_aggregates_all_checks():
    snap = EnvSnapshot(
        python_version="",
        node_version=None,
        pip_packages={"boto3": "latest"},
        env_vars={"AWS_SECRET_ACCESS_KEY": "shh"},
        shell="bash",
    )
    result = lint_snapshot(snap)
    codes = [i.code for i in result.issues]
    assert "L001" in codes
    assert "L003" in codes
    assert "L005" in codes
