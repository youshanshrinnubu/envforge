"""Tests for envforge.comparator."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from envforge.comparator import (
    LiveComparison,
    compare_with_live,
)
from envforge.snapshot import EnvSnapshot


@pytest.fixture()
def sample_snapshot() -> EnvSnapshot:
    return EnvSnapshot(
        env_vars={"PATH": "/usr/bin", "HOME": "/root", "LANG": "en_US.UTF-8"},
        python_version="Python 3.11.4",
        node_version="",
        pip_packages={"requests": "2.31.0", "flask": "3.0.0"},
        shell="bash",
    )


def _mock_live_env(snapshot: EnvSnapshot) -> dict:
    """Return a live env identical to the snapshot."""
    return dict(snapshot.env_vars)


def _mock_live_pkgs(snapshot: EnvSnapshot) -> dict:
    return {k.lower(): v for k, v in snapshot.pip_packages.items()}


# --- LiveComparison.is_clean ---

def test_is_clean_when_no_differences():
    cmp = LiveComparison(python_match=True)
    assert cmp.is_clean


def test_is_clean_false_when_missing_env_var():
    cmp = LiveComparison(missing_env_vars=["HOME"], python_match=True)
    assert not cmp.is_clean


def test_is_clean_false_when_python_mismatch():
    cmp = LiveComparison(python_match=False)
    assert not cmp.is_clean


def test_is_clean_false_when_missing_package():
    cmp = LiveComparison(missing_packages=["requests"], python_match=True)
    assert not cmp.is_clean


# --- compare_with_live ---

def test_compare_identical_env(sample_snapshot):
    with (
        patch("envforge.comparator.capture_env_vars", return_value=_mock_live_env(sample_snapshot)),
        patch("envforge.comparator._get_live_python_version", return_value=sample_snapshot.python_version),
        patch("envforge.comparator._get_live_pip_packages", return_value=_mock_live_pkgs(sample_snapshot)),
    ):
        result = compare_with_live(sample_snapshot)
    assert result.is_clean


def test_compare_detects_missing_env_var(sample_snapshot):
    live = _mock_live_env(sample_snapshot)
    del live["LANG"]
    with (
        patch("envforge.comparator.capture_env_vars", return_value=live),
        patch("envforge.comparator._get_live_python_version", return_value=sample_snapshot.python_version),
        patch("envforge.comparator._get_live_pip_packages", return_value=_mock_live_pkgs(sample_snapshot)),
    ):
        result = compare_with_live(sample_snapshot)
    assert "LANG" in result.missing_env_vars
    assert not result.is_clean


def test_compare_detects_changed_env_var(sample_snapshot):
    live = _mock_live_env(sample_snapshot)
    live["PATH"] = "/different/path"
    with (
        patch("envforge.comparator.capture_env_vars", return_value=live),
        patch("envforge.comparator._get_live_python_version", return_value=sample_snapshot.python_version),
        patch("envforge.comparator._get_live_pip_packages", return_value=_mock_live_pkgs(sample_snapshot)),
    ):
        result = compare_with_live(sample_snapshot)
    assert "PATH" in result.changed_env_vars
    assert result.changed_env_vars["PATH"] == ("/usr/bin", "/different/path")


def test_compare_detects_python_mismatch(sample_snapshot):
    with (
        patch("envforge.comparator.capture_env_vars", return_value=_mock_live_env(sample_snapshot)),
        patch("envforge.comparator._get_live_python_version", return_value="Python 3.10.0"),
        patch("envforge.comparator._get_live_pip_packages", return_value=_mock_live_pkgs(sample_snapshot)),
    ):
        result = compare_with_live(sample_snapshot)
    assert not result.python_match
    assert result.snapshot_python == "Python 3.11.4"
    assert result.live_python == "Python 3.10.0"


def test_compare_detects_missing_package(sample_snapshot):
    live_pkgs = _mock_live_pkgs(sample_snapshot)
    del live_pkgs["flask"]
    with (
        patch("envforge.comparator.capture_env_vars", return_value=_mock_live_env(sample_snapshot)),
        patch("envforge.comparator._get_live_python_version", return_value=sample_snapshot.python_version),
        patch("envforge.comparator._get_live_pip_packages", return_value=live_pkgs),
    ):
        result = compare_with_live(sample_snapshot)
    assert "flask" in result.missing_packages


def test_compare_detects_changed_package_version(sample_snapshot):
    live_pkgs = _mock_live_pkgs(sample_snapshot)
    live_pkgs["requests"] = "2.28.0"
    with (
        patch("envforge.comparator.capture_env_vars", return_value=_mock_live_env(sample_snapshot)),
        patch("envforge.comparator._get_live_python_version", return_value=sample_snapshot.python_version),
        patch("envforge.comparator._get_live_pip_packages", return_value=live_pkgs),
    ):
        result = compare_with_live(sample_snapshot)
    assert "requests" in result.changed_packages
    assert result.changed_packages["requests"] == ("2.31.0", "2.28.0")
