"""Tests for envforge.splitter."""

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.splitter import (
    SplitResult,
    split_by_env_prefix,
    split_by_package_prefix,
)


@pytest.fixture
def sample_snapshot() -> EnvSnapshot:
    return EnvSnapshot(
        label="test",
        env_vars={
            "AWS_ACCESS_KEY": "key123",
            "AWS_SECRET": "secret",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "HOME": "/home/user",
        },
        python_version="3.11.0",
        node_version="18.0.0",
        pip_packages=[
            {"name": "boto3", "version": "1.26.0"},
            {"name": "botocore", "version": "1.29.0"},
            {"name": "django", "version": "4.2.0"},
            {"name": "requests", "version": "2.28.0"},
        ],
        extra={},
    )


# ---------------------------------------------------------------------------
# SplitResult
# ---------------------------------------------------------------------------

def test_split_result_bool_true_when_parts(sample_snapshot):
    result = split_by_env_prefix(sample_snapshot, ["AWS_"])
    assert bool(result) is True


def test_split_result_bool_false_when_no_parts():
    result = SplitResult()
    assert bool(result) is False


# ---------------------------------------------------------------------------
# split_by_env_prefix
# ---------------------------------------------------------------------------

def test_split_env_prefix_creates_expected_parts(sample_snapshot):
    result = split_by_env_prefix(sample_snapshot, ["AWS_", "DB_"])
    assert "AWS_" in result.parts
    assert "DB_" in result.parts


def test_split_env_prefix_aws_contains_only_aws_keys(sample_snapshot):
    result = split_by_env_prefix(sample_snapshot, ["AWS_", "DB_"])
    aws_part = result.parts["AWS_"]
    assert set(aws_part.env_vars.keys()) == {"AWS_ACCESS_KEY", "AWS_SECRET"}


def test_split_env_prefix_db_contains_only_db_keys(sample_snapshot):
    result = split_by_env_prefix(sample_snapshot, ["AWS_", "DB_"])
    db_part = result.parts["DB_"]
    assert set(db_part.env_vars.keys()) == {"DB_HOST", "DB_PORT"}


def test_split_env_prefix_unmatched_goes_to_other(sample_snapshot):
    result = split_by_env_prefix(sample_snapshot, ["AWS_", "DB_"])
    assert "other" in result.parts
    assert "HOME" in result.parts["other"].env_vars


def test_split_env_prefix_exclude_unmatched(sample_snapshot):
    result = split_by_env_prefix(sample_snapshot, ["AWS_"], include_unmatched=False)
    assert "other" not in result.parts
    assert result.skipped_env_vars == 3  # DB_HOST, DB_PORT, HOME


def test_split_env_prefix_part_packages_are_empty(sample_snapshot):
    result = split_by_env_prefix(sample_snapshot, ["AWS_"])
    assert result.parts["AWS_"].pip_packages == []


def test_split_env_prefix_label_derived_from_snapshot(sample_snapshot):
    result = split_by_env_prefix(sample_snapshot, ["AWS_"])
    assert "aws" in result.parts["AWS_"].label


# ---------------------------------------------------------------------------
# split_by_package_prefix
# ---------------------------------------------------------------------------

def test_split_package_prefix_creates_boto_part(sample_snapshot):
    result = split_by_package_prefix(sample_snapshot, ["boto"])
    assert "boto" in result.parts


def test_split_package_prefix_boto_contains_boto_packages(sample_snapshot):
    result = split_by_package_prefix(sample_snapshot, ["boto"])
    names = [p["name"] for p in result.parts["boto"].pip_packages]
    assert "boto3" in names
    assert "botocore" in names


def test_split_package_prefix_other_contains_non_boto(sample_snapshot):
    result = split_by_package_prefix(sample_snapshot, ["boto"])
    other_names = [p["name"] for p in result.parts["other"].pip_packages]
    assert "django" in other_names
    assert "requests" in other_names


def test_split_package_prefix_exclude_unmatched_counts_skipped(sample_snapshot):
    result = split_by_package_prefix(sample_snapshot, ["boto"], include_unmatched=False)
    assert result.skipped_packages == 2
    assert "other" not in result.parts


def test_split_package_prefix_env_vars_are_empty(sample_snapshot):
    result = split_by_package_prefix(sample_snapshot, ["django"])
    assert result.parts["django"].env_vars == {}


def test_split_package_prefix_preserves_versions(sample_snapshot):
    result = split_by_package_prefix(sample_snapshot, ["boto"])
    boto3_entry = next(
        p for p in result.parts["boto"].pip_packages if p["name"] == "boto3"
    )
    assert boto3_entry["version"] == "1.26.0"
