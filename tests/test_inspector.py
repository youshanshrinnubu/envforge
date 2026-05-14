"""Tests for envforge.inspector."""

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.inspector import (
    FieldInspection,
    InspectionReport,
    inspect_snapshot,
)


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        label="test-env",
        python_version="3.11.2",
        node_version="18.0.0",
        env_vars={"HOME": "/home/user", "PATH": "/usr/bin"},
        pip_packages={"requests": "2.28.0", "flask": "2.3.0"},
    )


@pytest.fixture
def empty_snapshot():
    return EnvSnapshot(
        label="",
        python_version=None,
        node_version=None,
        env_vars={},
        pip_packages={},
    )


def test_inspect_returns_inspection_report(sample_snapshot):
    report = inspect_snapshot(sample_snapshot)
    assert isinstance(report, InspectionReport)


def test_report_label(sample_snapshot):
    report = inspect_snapshot(sample_snapshot)
    assert report.label == "test-env"


def test_report_label_unlabeled(empty_snapshot):
    report = inspect_snapshot(empty_snapshot)
    assert report.label == "(unlabeled)"


def test_report_has_four_fields(sample_snapshot):
    report = inspect_snapshot(sample_snapshot)
    assert len(report.fields) == 4


def test_python_version_field_present(sample_snapshot):
    report = inspect_snapshot(sample_snapshot)
    f = report.get("python_version")
    assert f is not None
    assert f.present is True
    assert f.summary == "3.11.2"


def test_python_version_field_missing(empty_snapshot):
    report = inspect_snapshot(empty_snapshot)
    f = report.get("python_version")
    assert f.present is False
    assert "not captured" in f.summary


def test_python_version_details_contain_parts(sample_snapshot):
    report = inspect_snapshot(sample_snapshot)
    f = report.get("python_version")
    assert any("3" in d for d in f.details)
    assert any("11" in d for d in f.details)


def test_node_version_field_present(sample_snapshot):
    report = inspect_snapshot(sample_snapshot)
    f = report.get("node_version")
    assert f.present is True
    assert f.summary == "18.0.0"


def test_node_version_field_missing(empty_snapshot):
    report = inspect_snapshot(empty_snapshot)
    f = report.get("node_version")
    assert f.present is False


def test_env_vars_field_summary(sample_snapshot):
    report = inspect_snapshot(sample_snapshot)
    f = report.get("env_vars")
    assert f.present is True
    assert "2" in f.summary


def test_env_vars_field_empty(empty_snapshot):
    report = inspect_snapshot(empty_snapshot)
    f = report.get("env_vars")
    assert f.present is False
    assert f.summary == "empty"


def test_env_vars_details_show_keys(sample_snapshot):
    report = inspect_snapshot(sample_snapshot)
    f = report.get("env_vars")
    combined = " ".join(f.details)
    assert "HOME" in combined or "PATH" in combined


def test_pip_packages_field_summary(sample_snapshot):
    report = inspect_snapshot(sample_snapshot)
    f = report.get("pip_packages")
    assert f.present is True
    assert "2" in f.summary


def test_pip_packages_details_contain_versions(sample_snapshot):
    report = inspect_snapshot(sample_snapshot)
    f = report.get("pip_packages")
    combined = " ".join(f.details)
    assert "requests" in combined or "flask" in combined


def test_present_fields_filters_correctly(sample_snapshot):
    report = inspect_snapshot(sample_snapshot)
    present = report.present_fields()
    assert all(f.present for f in present)


def test_missing_fields_on_empty(empty_snapshot):
    report = inspect_snapshot(empty_snapshot)
    missing = report.missing_fields()
    names = [f.name for f in missing]
    assert "python_version" in names
    assert "env_vars" in names


def test_get_returns_none_for_unknown_field(sample_snapshot):
    report = inspect_snapshot(sample_snapshot)
    assert report.get("nonexistent") is None


def test_long_env_var_value_truncated():
    snap = EnvSnapshot(
        label="trunc",
        python_version="3.10.0",
        node_version=None,
        env_vars={"LONG_VAR": "x" * 100},
        pip_packages={},
    )
    report = inspect_snapshot(snap)
    f = report.get("env_vars")
    assert "..." in f.details[0]
