"""Tests for envforge.snapcmp."""
import pytest
from envforge.snapshot import EnvSnapshot
from envforge.snapcmp import (
    compare_snapshots_report,
    ComparisonReport,
    _fmt_env_section,
    _fmt_pkg_section,
    _fmt_version_section,
)
from envforge.differ import compare_snapshots


@pytest.fixture
def base_snapshot():
    return EnvSnapshot(
        label="base",
        python_version="3.10.0",
        node_version="18.0.0",
        env_vars={"HOME": "/home/user", "SHARED": "same"},
        pip_packages={"requests": "2.28.0", "flask": "2.2.0"},
    )


@pytest.fixture
def other_snapshot():
    return EnvSnapshot(
        label="other",
        python_version="3.11.0",
        node_version="18.0.0",
        env_vars={"HOME": "/home/other", "SHARED": "same", "NEW_VAR": "hello"},
        pip_packages={"requests": "2.29.0", "numpy": "1.24.0"},
    )


def test_compare_returns_comparison_report(base_snapshot, other_snapshot):
    report = compare_snapshots_report(base_snapshot, other_snapshot)
    assert isinstance(report, ComparisonReport)


def test_report_labels_from_snapshot(base_snapshot, other_snapshot):
    report = compare_snapshots_report(base_snapshot, other_snapshot)
    assert report.left_label == "base"
    assert report.right_label == "other"


def test_report_labels_overridden(base_snapshot, other_snapshot):
    report = compare_snapshots_report(
        base_snapshot, other_snapshot,
        left_label="LEFT", right_label="RIGHT"
    )
    assert report.left_label == "LEFT"
    assert report.right_label == "RIGHT"


def test_bool_false_when_differences(base_snapshot, other_snapshot):
    report = compare_snapshots_report(base_snapshot, other_snapshot)
    assert not bool(report)


def test_bool_true_when_identical(base_snapshot):
    report = compare_snapshots_report(base_snapshot, base_snapshot)
    assert bool(report)


def test_str_contains_labels(base_snapshot, other_snapshot):
    report = compare_snapshots_report(base_snapshot, other_snapshot)
    text = str(report)
    assert "base" in text
    assert "other" in text


def test_str_no_differences_message_when_identical(base_snapshot):
    report = compare_snapshots_report(base_snapshot, base_snapshot)
    assert "No differences found" in str(report)


def test_fmt_env_section_added(base_snapshot, other_snapshot):
    diff = compare_snapshots(base_snapshot, other_snapshot)
    lines = _fmt_env_section(diff)
    assert any("NEW_VAR" in l and "+" in l for l in lines)


def test_fmt_env_section_removed(base_snapshot, other_snapshot):
    diff = compare_snapshots(other_snapshot, base_snapshot)
    lines = _fmt_env_section(diff)
    assert any("NEW_VAR" in l and "-" in l for l in lines)


def test_fmt_env_section_changed(base_snapshot, other_snapshot):
    diff = compare_snapshots(base_snapshot, other_snapshot)
    lines = _fmt_env_section(diff)
    assert any("HOME" in l and "~" in l for l in lines)


def test_fmt_pkg_section_added(base_snapshot, other_snapshot):
    diff = compare_snapshots(base_snapshot, other_snapshot)
    lines = _fmt_pkg_section(diff)
    assert any("numpy" in l and "+" in l for l in lines)


def test_fmt_pkg_section_removed(base_snapshot, other_snapshot):
    diff = compare_snapshots(base_snapshot, other_snapshot)
    lines = _fmt_pkg_section(diff)
    assert any("flask" in l and "-" in l for l in lines)


def test_fmt_version_section_python(base_snapshot, other_snapshot):
    diff = compare_snapshots(base_snapshot, other_snapshot)
    lines = _fmt_version_section(diff)
    assert any("python" in l and "3.10.0" in l for l in lines)


def test_summary_lines_populated_on_diff(base_snapshot, other_snapshot):
    report = compare_snapshots_report(base_snapshot, other_snapshot)
    assert len(report.summary_lines) > 0


def test_summary_lines_empty_on_identical(base_snapshot):
    report = compare_snapshots_report(base_snapshot, base_snapshot)
    assert report.summary_lines == []
