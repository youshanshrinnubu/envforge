"""Tests for envforge.redactor."""

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.redactor import (
    DEFAULT_SENSITIVE_PATTERNS,
    REDACT_PLACEHOLDER,
    RedactResult,
    redact_env_vars,
    redact_snapshot,
    _is_sensitive,
    _compile_patterns,
)


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        label="test",
        env_vars={
            "HOME": "/home/user",
            "MY_SECRET": "supersecret",
            "DB_PASSWORD": "hunter2",
            "API_KEY": "key-abc-123",
            "PATH": "/usr/bin:/bin",
            "GITHUB_TOKEN": "ghp_xyz",
            "EDITOR": "vim",
        },
        python_version="3.11.0",
        node_version="18.0.0",
        pip_packages=["requests==2.31.0"],
        extra={},
    )


def test_redact_result_bool_true_when_redacted(sample_snapshot):
    result = redact_env_vars(sample_snapshot)
    assert bool(result) is True


def test_redact_result_bool_false_when_nothing_redacted(sample_snapshot):
    safe_snapshot = EnvSnapshot(
        label="safe",
        env_vars={"HOME": "/home/user", "EDITOR": "vim"},
        python_version="3.11.0",
        node_version=None,
        pip_packages=[],
        extra={},
    )
    result = redact_env_vars(safe_snapshot)
    assert bool(result) is False


def test_sensitive_keys_are_redacted(sample_snapshot):
    result = redact_env_vars(sample_snapshot)
    env = result.snapshot.env_vars
    assert env["MY_SECRET"] == REDACT_PLACEHOLDER
    assert env["DB_PASSWORD"] == REDACT_PLACEHOLDER
    assert env["API_KEY"] == REDACT_PLACEHOLDER
    assert env["GITHUB_TOKEN"] == REDACT_PLACEHOLDER


def test_safe_keys_are_preserved(sample_snapshot):
    result = redact_env_vars(sample_snapshot)
    env = result.snapshot.env_vars
    assert env["HOME"] == "/home/user"
    assert env["PATH"] == "/usr/bin:/bin"
    assert env["EDITOR"] == "vim"


def test_redacted_keys_list_sorted(sample_snapshot):
    result = redact_env_vars(sample_snapshot)
    assert result.redacted_keys == sorted(result.redacted_keys)


def test_custom_placeholder(sample_snapshot):
    result = redact_env_vars(sample_snapshot, placeholder="<hidden>")
    assert result.snapshot.env_vars["MY_SECRET"] == "<hidden>"


def test_custom_patterns(sample_snapshot):
    result = redact_env_vars(sample_snapshot, patterns=[r"EDITOR"])
    env = result.snapshot.env_vars
    assert env["EDITOR"] == REDACT_PLACEHOLDER
    # Default sensitive keys should NOT be redacted with custom patterns
    assert env["MY_SECRET"] == "supersecret"


def test_original_snapshot_not_mutated(sample_snapshot):
    original_value = sample_snapshot.env_vars["MY_SECRET"]
    redact_env_vars(sample_snapshot)
    assert sample_snapshot.env_vars["MY_SECRET"] == original_value


def test_pip_packages_preserved(sample_snapshot):
    result = redact_env_vars(sample_snapshot)
    assert result.snapshot.pip_packages == ["requests==2.31.0"]


def test_python_version_preserved(sample_snapshot):
    result = redact_env_vars(sample_snapshot)
    assert result.snapshot.python_version == "3.11.0"


def test_redact_snapshot_convenience(sample_snapshot):
    result = redact_snapshot(sample_snapshot)
    assert isinstance(result, RedactResult)
    assert result.snapshot.env_vars["API_KEY"] == REDACT_PLACEHOLDER


def test_is_sensitive_case_insensitive():
    patterns = _compile_patterns([r".*secret.*"])
    assert _is_sensitive("MY_SECRET", patterns) is True
    assert _is_sensitive("my_secret", patterns) is True
    assert _is_sensitive("HOME", patterns) is False
