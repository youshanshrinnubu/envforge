"""Tests for envforge.watchdog drift detection."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.watchdog import DriftReport, _build_summary, detect_drift


@pytest.fixture()
def sample_snapshot() -> EnvSnapshot:
    return EnvSnapshot(
        label="test-env",
        env_vars={"HOME": "/home/user", "PATH": "/usr/bin"},
        python_version="3.11.4",
        node_version="18.0.0",
        pip_packages={"requests": "2.31.0", "flask": "3.0.0"},
    )


def _make_clean_comparison(snapshot: EnvSnapshot):
    diff = MagicMock()
    diff.env_vars.added = set()
    diff.env_vars.removed = set()
    diff.env_vars.changed = set()
    diff.pip_packages.added = set()
    diff.pip_packages.removed = set()
    diff.pip_packages.changed = set()
    diff.python_version_changed = False
    cmp = MagicMock()
    cmp.is_clean = True
    cmp.diff = diff
    return cmp


def _make_drifted_comparison():
    diff = MagicMock()
    diff.env_vars.added = {"NEW_VAR"}
    diff.env_vars.removed = {"OLD_VAR"}
    diff.env_vars.changed = set()
    diff.pip_packages.added = set()
    diff.pip_packages.removed = {"flask"}
    diff.pip_packages.changed = {"requests"}
    diff.python_version_changed = True
    cmp = MagicMock()
    cmp.is_clean = False
    cmp.diff = diff
    return cmp


def test_detect_drift_no_drift(sample_snapshot):
    with patch("envforge.watchdog.compare_with_live", return_value=_make_clean_comparison(sample_snapshot)):
        report = detect_drift(sample_snapshot)
    assert isinstance(report, DriftReport)
    assert report.has_drift is False
    assert bool(report) is False
    assert report.summary == "no drift detected"


def test_detect_drift_with_drift(sample_snapshot):
    with patch("envforge.watchdog.compare_with_live", return_value=_make_drifted_comparison()):
        report = detect_drift(sample_snapshot)
    assert report.has_drift is True
    assert bool(report) is True
    assert "NEW_VAR" in report.added_env_vars
    assert "OLD_VAR" in report.removed_env_vars
    assert "flask" in report.removed_packages
    assert "requests" in report.changed_packages
    assert report.python_version_changed is True


def test_detect_drift_summary_contains_all_categories(sample_snapshot):
    with patch("envforge.watchdog.compare_with_live", return_value=_make_drifted_comparison()):
        report = detect_drift(sample_snapshot)
    assert "python version changed" in report.summary
    assert "env-var" in report.summary
    assert "package" in report.summary


def test_detect_drift_notifies_on_drift(sample_snapshot):
    mock_cfg = MagicMock()
    with patch("envforge.watchdog.compare_with_live", return_value=_make_drifted_comparison()), \
         patch("envforge.watchdog.load_config", return_value=mock_cfg) as mock_load, \
         patch("envforge.watchdog.notify") as mock_notify:
        detect_drift(sample_snapshot, notify_on_drift=True)
    mock_load.assert_called_once()
    mock_notify.assert_called_once()


def test_detect_drift_no_notify_when_clean(sample_snapshot):
    with patch("envforge.watchdog.compare_with_live", return_value=_make_clean_comparison(sample_snapshot)), \
         patch("envforge.watchdog.notify") as mock_notify:
        detect_drift(sample_snapshot, notify_on_drift=True)
    mock_notify.assert_not_called()


def test_build_summary_empty_report():
    report = DriftReport(snapshot_label="x", has_drift=False)
    assert _build_summary(report) == "no drift detected"


def test_drift_report_label(sample_snapshot):
    with patch("envforge.watchdog.compare_with_live", return_value=_make_clean_comparison(sample_snapshot)):
        report = detect_drift(sample_snapshot)
    assert report.snapshot_label == "test-env"
