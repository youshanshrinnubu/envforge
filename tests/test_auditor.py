"""Tests for envforge.auditor."""

import time
from pathlib import Path

import pytest

from envforge.auditor import (
    AuditEntry,
    clear_audit_log,
    filter_audit_log,
    load_audit_log,
    record_audit,
)


@pytest.fixture()
def audit_dir(tmp_path: Path) -> Path:
    return tmp_path / "audit"


def test_record_audit_creates_entry(audit_dir):
    entry = record_audit("capture", "my-env", audit_dir=audit_dir)
    assert isinstance(entry, AuditEntry)
    assert entry.operation == "capture"
    assert entry.snapshot_name == "my-env"


def test_record_audit_persists(audit_dir):
    record_audit("capture", "snap1", audit_dir=audit_dir)
    entries = load_audit_log(audit_dir=audit_dir)
    assert len(entries) == 1
    assert entries[0].snapshot_name == "snap1"


def test_record_audit_appends(audit_dir):
    record_audit("capture", "snap1", audit_dir=audit_dir)
    record_audit("reproduce", "snap2", audit_dir=audit_dir)
    entries = load_audit_log(audit_dir=audit_dir)
    assert len(entries) == 2


def test_record_audit_stores_details(audit_dir):
    record_audit("export", "snap1", details={"format": "dockerfile"}, audit_dir=audit_dir)
    entries = load_audit_log(audit_dir=audit_dir)
    assert entries[0].details == {"format": "dockerfile"}


def test_record_audit_timestamp_is_recent(audit_dir):
    before = time.time()
    entry = record_audit("capture", "snap", audit_dir=audit_dir)
    after = time.time()
    assert before <= entry.timestamp <= after


def test_load_audit_log_empty_dir(audit_dir):
    entries = load_audit_log(audit_dir=audit_dir)
    assert entries == []


def test_clear_audit_log_returns_count(audit_dir):
    record_audit("capture", "s1", audit_dir=audit_dir)
    record_audit("capture", "s2", audit_dir=audit_dir)
    count = clear_audit_log(audit_dir=audit_dir)
    assert count == 2


def test_clear_audit_log_removes_entries(audit_dir):
    record_audit("capture", "s1", audit_dir=audit_dir)
    clear_audit_log(audit_dir=audit_dir)
    assert load_audit_log(audit_dir=audit_dir) == []


def test_filter_by_operation(audit_dir):
    record_audit("capture", "s1", audit_dir=audit_dir)
    record_audit("reproduce", "s2", audit_dir=audit_dir)
    results = filter_audit_log(operation="capture", audit_dir=audit_dir)
    assert len(results) == 1
    assert results[0].operation == "capture"


def test_filter_by_snapshot_name(audit_dir):
    record_audit("capture", "alpha", audit_dir=audit_dir)
    record_audit("capture", "beta", audit_dir=audit_dir)
    results = filter_audit_log(snapshot_name="beta", audit_dir=audit_dir)
    assert len(results) == 1
    assert results[0].snapshot_name == "beta"


def test_filter_combined(audit_dir):
    record_audit("capture", "alpha", audit_dir=audit_dir)
    record_audit("reproduce", "alpha", audit_dir=audit_dir)
    record_audit("capture", "beta", audit_dir=audit_dir)
    results = filter_audit_log(operation="capture", snapshot_name="alpha", audit_dir=audit_dir)
    assert len(results) == 1
