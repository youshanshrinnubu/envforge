"""Tests for envforge.scorer."""

import pytest
from envforge.snapshot import EnvSnapshot
from envforge.scorer import score_snapshot, ScoreResult, MAX_SCORE


@pytest.fixture
def full_snapshot():
    return EnvSnapshot(
        python_version="3.11.4",
        node_version="20.1.0",
        pip_packages={"requests": "2.31.0", "flask": "3.0.0"},
        env_vars={"HOME": "/home/user", "PATH": "/usr/bin", "SHELL": "/bin/bash",
                  "USER": "dev", "LANG": "en_US.UTF-8"},
    )


@pytest.fixture
def empty_snapshot():
    return EnvSnapshot(
        python_version=None,
        node_version=None,
        pip_packages={},
        env_vars={},
    )


def test_score_result_is_score_result(full_snapshot):
    result = score_snapshot(full_snapshot)
    assert isinstance(result, ScoreResult)


def test_full_snapshot_high_score(full_snapshot):
    result = score_snapshot(full_snapshot)
    assert result.score >= 80


def test_empty_snapshot_low_score(empty_snapshot):
    result = score_snapshot(empty_snapshot)
    assert result.score <= 20


def test_score_does_not_exceed_max(full_snapshot):
    result = score_snapshot(full_snapshot)
    assert result.score <= MAX_SCORE


def test_grade_a_for_high_score(full_snapshot):
    result = score_snapshot(full_snapshot)
    assert result.grade == "A"


def test_grade_f_for_empty(empty_snapshot):
    result = score_snapshot(empty_snapshot)
    assert result.grade == "F"


def test_breakdown_has_expected_keys(full_snapshot):
    result = score_snapshot(full_snapshot)
    for key in ("python_version", "pip_packages", "env_vars", "node_version", "shell"):
        assert key in result.breakdown


def test_no_suggestions_for_full_snapshot(full_snapshot):
    result = score_snapshot(full_snapshot)
    assert result.suggestions == []


def test_suggestions_for_empty_snapshot(empty_snapshot):
    result = score_snapshot(empty_snapshot)
    assert len(result.suggestions) > 0


def test_partial_python_version_gives_partial_points():
    snap = EnvSnapshot(python_version="3.11", node_version=None, pip_packages={}, env_vars={})
    result = score_snapshot(snap)
    assert 0 < result.breakdown["python_version"] < 20


def test_unpinned_packages_reduce_score():
    snap = EnvSnapshot(
        python_version="3.11.4",
        node_version=None,
        pip_packages={"requests": "*", "flask": "*"},
        env_vars={},
    )
    result = score_snapshot(snap)
    assert result.breakdown["pip_packages"] == 0


def test_percentage_is_float(full_snapshot):
    result = score_snapshot(full_snapshot)
    assert isinstance(result.percentage, float)
    assert 0.0 <= result.percentage <= 100.0
