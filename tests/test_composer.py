"""Tests for envforge.composer."""
import pytest

from envforge.snapshot import EnvSnapshot
from envforge.composer import ComposeResult, compose_snapshots


@pytest.fixture
def snap_a():
    return EnvSnapshot(
        label="snap-a",
        python_version="3.10.0",
        node_version=None,
        env_vars={"HOME": "/home/user", "APP_ENV": "staging"},
        pip_packages=[{"name": "requests", "version": "2.28.0"}, {"name": "flask", "version": "2.2.0"}],
        extra={},
    )


@pytest.fixture
def snap_b():
    return EnvSnapshot(
        label="snap-b",
        python_version="3.11.1",
        node_version="18.0.0",
        env_vars={"APP_ENV": "production", "DEBUG": "false"},
        pip_packages=[{"name": "requests", "version": "2.31.0"}, {"name": "gunicorn", "version": "21.0.0"}],
        extra={},
    )


def test_compose_result_bool_true_when_snapshot(snap_a):
    result = compose_snapshots([snap_a])
    assert bool(result) is True


def test_compose_result_bool_false_when_no_snapshots():
    result = compose_snapshots([])
    assert bool(result) is False


def test_compose_empty_list_returns_warning():
    result = compose_snapshots([])
    assert result.snapshot is None
    assert any("No snapshots" in w for w in result.warnings)


def test_compose_single_snapshot_unchanged(snap_a):
    result = compose_snapshots([snap_a])
    assert result.snapshot is not None
    assert result.snapshot.env_vars["HOME"] == "/home/user"
    assert result.snapshot.python_version == "3.10.0"


def test_compose_source_labels_recorded(snap_a, snap_b):
    result = compose_snapshots([snap_a, snap_b])
    assert "snap-a" in result.source_labels
    assert "snap-b" in result.source_labels


def test_compose_prefer_last_env_var(snap_a, snap_b):
    result = compose_snapshots([snap_a, snap_b], prefer_last=True)
    assert result.snapshot.env_vars["APP_ENV"] == "production"


def test_compose_prefer_first_env_var(snap_a, snap_b):
    result = compose_snapshots([snap_a, snap_b], prefer_last=False)
    assert result.snapshot.env_vars["APP_ENV"] == "staging"


def test_compose_env_var_conflict_recorded(snap_a, snap_b):
    result = compose_snapshots([snap_a, snap_b])
    assert "env_var:APP_ENV" in result.conflicts


def test_compose_no_conflict_for_unique_keys(snap_a, snap_b):
    result = compose_snapshots([snap_a, snap_b])
    assert "env_var:HOME" not in result.conflicts
    assert "env_var:DEBUG" not in result.conflicts


def test_compose_merges_all_env_vars(snap_a, snap_b):
    result = compose_snapshots([snap_a, snap_b])
    assert "HOME" in result.snapshot.env_vars
    assert "DEBUG" in result.snapshot.env_vars


def test_compose_pip_conflict_recorded(snap_a, snap_b):
    result = compose_snapshots([snap_a, snap_b])
    assert "pip:requests" in result.conflicts


def test_compose_pip_prefer_last_version(snap_a, snap_b):
    result = compose_snapshots([snap_a, snap_b], prefer_last=True)
    pkgs = {p["name"]: p["version"] for p in result.snapshot.pip_packages}
    assert pkgs["requests"] == "2.31.0"


def test_compose_pip_includes_all_packages(snap_a, snap_b):
    result = compose_snapshots([snap_a, snap_b])
    names = [p["name"] for p in result.snapshot.pip_packages]
    assert "flask" in names
    assert "gunicorn" in names


def test_compose_python_version_prefer_last(snap_a, snap_b):
    result = compose_snapshots([snap_a, snap_b], prefer_last=True)
    assert result.snapshot.python_version == "3.11.1"


def test_compose_node_version_filled_from_later(snap_a, snap_b):
    result = compose_snapshots([snap_a, snap_b])
    assert result.snapshot.node_version == "18.0.0"


def test_compose_custom_label(snap_a, snap_b):
    result = compose_snapshots([snap_a, snap_b], label="merged")
    assert result.snapshot.label == "merged"


def test_compose_conflicts_deduplicated(snap_a, snap_b):
    result = compose_snapshots([snap_a, snap_b])
    assert len(result.conflicts) == len(set(result.conflicts))
