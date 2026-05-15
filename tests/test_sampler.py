"""Tests for envforge.sampler."""
import pytest

from envforge.snapshot import EnvSnapshot
from envforge.sampler import (
    SampleResult,
    sample_env_vars,
    sample_pip_packages,
    sample_snapshot,
)


@pytest.fixture()
def sample_snap() -> EnvSnapshot:
    return EnvSnapshot(
        env_vars={"HOME": "/home/user", "PATH": "/usr/bin", "LANG": "en_US.UTF-8", "EDITOR": "vim"},
        python_version="3.11.4",
        node_version="18.0.0",
        pip_packages=[
            {"name": "requests", "version": "2.31.0"},
            {"name": "flask", "version": "3.0.0"},
            {"name": "pytest", "version": "7.4.0"},
            {"name": "numpy", "version": "1.26.0"},
        ],
        label="test",
    )


def test_sample_result_bool_true_when_snapshot(sample_snap):
    result = sample_env_vars(sample_snap, 2, seed=0)
    assert bool(result) is True


def test_sample_result_bool_false_when_no_snapshot():
    result = SampleResult(snapshot=None)
    assert bool(result) is False


def test_sample_env_vars_returns_correct_count(sample_snap):
    result = sample_env_vars(sample_snap, 2, seed=42)
    assert result.sampled_env_vars == 2
    assert len(result.snapshot.env_vars) == 2


def test_sample_env_vars_deterministic(sample_snap):
    r1 = sample_env_vars(sample_snap, 2, seed=7)
    r2 = sample_env_vars(sample_snap, 2, seed=7)
    assert r1.snapshot.env_vars == r2.snapshot.env_vars


def test_sample_env_vars_different_seeds_may_differ(sample_snap):
    results = set()
    for seed in range(20):
        r = sample_env_vars(sample_snap, 2, seed=seed)
        results.add(tuple(sorted(r.snapshot.env_vars.keys())))
    assert len(results) > 1, "Expected variation across seeds"


def test_sample_env_vars_clamps_to_available(sample_snap):
    result = sample_env_vars(sample_snap, 100, seed=0)
    assert result.sampled_env_vars == len(sample_snap.env_vars)
    assert len(result.warnings) == 1
    assert "only 4 available" in result.warnings[0]


def test_sample_env_vars_preserves_other_fields(sample_snap):
    result = sample_env_vars(sample_snap, 2, seed=0)
    assert result.snapshot.python_version == sample_snap.python_version
    assert result.snapshot.pip_packages == sample_snap.pip_packages


def test_sample_pip_packages_returns_correct_count(sample_snap):
    result = sample_pip_packages(sample_snap, 2, seed=0)
    assert result.sampled_packages == 2
    assert len(result.snapshot.pip_packages) == 2


def test_sample_pip_packages_deterministic(sample_snap):
    r1 = sample_pip_packages(sample_snap, 3, seed=99)
    r2 = sample_pip_packages(sample_snap, 3, seed=99)
    assert r1.snapshot.pip_packages == r2.snapshot.pip_packages


def test_sample_pip_packages_clamps_to_available(sample_snap):
    result = sample_pip_packages(sample_snap, 50, seed=0)
    assert result.sampled_packages == len(sample_snap.pip_packages)
    assert len(result.warnings) == 1


def test_sample_pip_packages_preserves_env_vars(sample_snap):
    result = sample_pip_packages(sample_snap, 2, seed=0)
    assert result.snapshot.env_vars == sample_snap.env_vars


def test_sample_snapshot_samples_both(sample_snap):
    result = sample_snapshot(sample_snap, n_env=2, n_pkg=2, seed=1)
    assert result.sampled_env_vars == 2
    assert result.sampled_packages == 2
    assert len(result.snapshot.env_vars) == 2
    assert len(result.snapshot.pip_packages) == 2


def test_sample_snapshot_no_warnings_within_bounds(sample_snap):
    result = sample_snapshot(sample_snap, n_env=2, n_pkg=2, seed=0)
    assert result.warnings == []


def test_sample_snapshot_collects_warnings_from_both(sample_snap):
    result = sample_snapshot(sample_snap, n_env=100, n_pkg=100, seed=0)
    assert len(result.warnings) == 2
