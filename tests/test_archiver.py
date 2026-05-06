"""Tests for envforge.archiver module."""

import gzip
import json
import os

import pytest

from envforge.archiver import (
    DEFAULT_ARCHIVE_EXT,
    archive_info,
    archive_snapshot,
    restore_snapshot,
)
from envforge.snapshot import EnvSnapshot


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        env_vars={"HOME": "/home/user", "LANG": "en_US.UTF-8"},
        python_version="3.11.4",
        node_version="18.17.0",
        pip_packages={"requests": "2.31.0", "pytest": "7.4.0"},
        shell="bash",
    )


def test_archive_adds_extension(tmp_path, sample_snapshot):
    dest = str(tmp_path / "myenv")
    result = archive_snapshot(sample_snapshot, dest)
    assert result.endswith(DEFAULT_ARCHIVE_EXT)
    assert os.path.exists(result)


def test_archive_does_not_double_extension(tmp_path, sample_snapshot):
    dest = str(tmp_path / "myenv.efz")
    result = archive_snapshot(sample_snapshot, dest)
    assert result.endswith(".efz")
    assert ".efz.efz" not in result


def test_archive_creates_gzip_file(tmp_path, sample_snapshot):
    dest = str(tmp_path / "snap")
    path = archive_snapshot(sample_snapshot, dest, compress=True)
    with gzip.open(path, "rb") as fh:
        content = fh.read()
    data = json.loads(content.decode("utf-8"))
    assert "python_version" in data


def test_archive_uncompressed(tmp_path, sample_snapshot):
    dest = str(tmp_path / "snap")
    path = archive_snapshot(sample_snapshot, dest, compress=False)
    with open(path, "rb") as fh:
        data = json.loads(fh.read().decode("utf-8"))
    assert data["python_version"] == "3.11.4"


def test_restore_roundtrip(tmp_path, sample_snapshot):
    dest = str(tmp_path / "env")
    path = archive_snapshot(sample_snapshot, dest)
    restored = restore_snapshot(path)
    assert restored.python_version == sample_snapshot.python_version
    assert restored.pip_packages == sample_snapshot.pip_packages
    assert restored.env_vars == sample_snapshot.env_vars


def test_restore_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        restore_snapshot(str(tmp_path / "nonexistent.efz"))


def test_restore_invalid_content_raises(tmp_path):
    bad_file = tmp_path / "bad.efz"
    bad_file.write_bytes(b"not valid json or gzip")
    with pytest.raises(ValueError):
        restore_snapshot(str(bad_file))


def test_archive_info_returns_metadata(tmp_path, sample_snapshot):
    dest = str(tmp_path / "info_test")
    path = archive_snapshot(sample_snapshot, dest)
    info = archive_info(path)
    assert info["python_version"] == "3.11.4"
    assert info["pip_package_count"] == 2
    assert info["env_var_count"] == 2
    assert info["size_bytes"] > 0
    assert info["path"] == path
