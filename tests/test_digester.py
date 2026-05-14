"""Tests for envforge.digester."""

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.digester import (
    DigestResult,
    compute_digest,
    verify_digest,
    attach_digest,
    check_attached_digest,
)


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        label="test-env",
        python_version="3.11.4",
        node_version="18.0.0",
        env_vars={"HOME": "/home/user", "PATH": "/usr/bin"},
        pip_packages=["requests==2.31.0", "pytest==7.4.0"],
        extra={},
    )


def test_compute_digest_returns_digest_result(sample_snapshot):
    result = compute_digest(sample_snapshot)
    assert isinstance(result, DigestResult)


def test_compute_digest_sha256_length(sample_snapshot):
    result = compute_digest(sample_snapshot, algorithm="sha256")
    assert len(result.digest) == 64
    assert result.algorithm == "sha256"


def test_compute_digest_sha1_length(sample_snapshot):
    result = compute_digest(sample_snapshot, algorithm="sha1")
    assert len(result.digest) == 40


def test_compute_digest_md5_length(sample_snapshot):
    result = compute_digest(sample_snapshot, algorithm="md5")
    assert len(result.digest) == 32


def test_compute_digest_unsupported_algorithm(sample_snapshot):
    with pytest.raises(ValueError, match="Unsupported"):
        compute_digest(sample_snapshot, algorithm="blake2b")


def test_digest_is_deterministic(sample_snapshot):
    r1 = compute_digest(sample_snapshot)
    r2 = compute_digest(sample_snapshot)
    assert r1.digest == r2.digest


def test_digest_changes_with_env_var(sample_snapshot):
    r1 = compute_digest(sample_snapshot)
    sample_snapshot.env_vars["NEW_VAR"] = "value"
    r2 = compute_digest(sample_snapshot)
    assert r1.digest != r2.digest


def test_digest_changes_with_package(sample_snapshot):
    r1 = compute_digest(sample_snapshot)
    sample_snapshot.pip_packages.append("numpy==1.25.0")
    r2 = compute_digest(sample_snapshot)
    assert r1.digest != r2.digest


def test_verify_digest_correct(sample_snapshot):
    r = compute_digest(sample_snapshot)
    verified = verify_digest(sample_snapshot, expected=r.digest)
    assert verified.verified is True
    assert bool(verified) is True


def test_verify_digest_wrong(sample_snapshot):
    verified = verify_digest(sample_snapshot, expected="deadbeef" * 8)
    assert verified.verified is False
    assert bool(verified) is False


def test_attach_digest_stores_in_extra(sample_snapshot):
    digest = attach_digest(sample_snapshot)
    assert sample_snapshot.extra["digest"] == digest
    assert sample_snapshot.extra["digest_algorithm"] == "sha256"


def test_check_attached_digest_valid(sample_snapshot):
    attach_digest(sample_snapshot)
    result = check_attached_digest(sample_snapshot)
    assert result.verified is True


def test_check_attached_digest_tampered(sample_snapshot):
    attach_digest(sample_snapshot)
    sample_snapshot.pip_packages.append("evil==0.0.1")
    result = check_attached_digest(sample_snapshot)
    assert result.verified is False


def test_check_attached_digest_missing_raises(sample_snapshot):
    sample_snapshot.extra = {}
    with pytest.raises(ValueError, match="No digest attached"):
        check_attached_digest(sample_snapshot)


def test_digest_result_bool_none_verified(sample_snapshot):
    result = compute_digest(sample_snapshot)
    assert result.verified is None
    assert bool(result) is True
