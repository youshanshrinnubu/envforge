"""Tests for envforge.summarizer."""

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.summarizer import (
    SnapshotSummary,
    summarize_snapshot,
    _summarize_versions,
    _summarize_env_vars,
    _summarize_pip_packages,
)


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        python_version="3.11.4",
        node_version="18.17.0",
        env_vars={"HOME": "/home/user", "PATH": "/usr/bin:/bin"},
        pip_packages=["requests==2.31.0", "flask==3.0.0"],
    )


@pytest.fixture
def empty_snapshot():
    return EnvSnapshot(
        python_version=None,
        node_version=None,
        env_vars={},
        pip_packages=[],
    )


def test_summarize_snapshot_returns_summary(sample_snapshot):
    result = summarize_snapshot(sample_snapshot)
    assert isinstance(result, SnapshotSummary)


def test_summary_str_contains_title(sample_snapshot):
    result = summarize_snapshot(sample_snapshot, title="My Env")
    assert "My Env" in str(result)


def test_summary_str_contains_python_version(sample_snapshot):
    result = summarize_snapshot(sample_snapshot)
    assert "3.11.4" in str(result)


def test_summary_str_contains_node_version(sample_snapshot):
    result = summarize_snapshot(sample_snapshot)
    assert "18.17.0" in str(result)


def test_summary_str_contains_env_var_key(sample_snapshot):
    result = summarize_snapshot(sample_snapshot)
    assert "HOME" in str(result)


def test_summary_str_contains_pip_package(sample_snapshot):
    result = summarize_snapshot(sample_snapshot)
    assert "requests==2.31.0" in str(result)


def test_summarize_versions_empty(empty_snapshot):
    text = _summarize_versions(empty_snapshot)
    assert "no language versions" in text


def test_summarize_env_vars_empty(empty_snapshot):
    text = _summarize_env_vars(empty_snapshot)
    assert "no environment variables" in text


def test_summarize_pip_packages_empty(empty_snapshot):
    text = _summarize_pip_packages(empty_snapshot)
    assert "no pip packages" in text


def test_long_env_var_value_is_truncated():
    snapshot = EnvSnapshot(
        python_version=None,
        node_version=None,
        env_vars={"LONG_VAR": "x" * 80},
        pip_packages=[],
    )
    text = _summarize_env_vars(snapshot)
    assert "..." in text
    assert len(text.split("=", 1)[1]) <= 43  # 40 chars + "..."


def test_summary_sections_order(sample_snapshot):
    result = summarize_snapshot(sample_snapshot)
    text = str(result)
    lang_pos = text.index("Language Versions")
    env_pos = text.index("Environment Variables")
    pip_pos = text.index("Pip Packages")
    assert lang_pos < env_pos < pip_pos
