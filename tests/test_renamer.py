"""Tests for envforge.renamer."""

from __future__ import annotations

import json
import os

import pytest

from envforge.renamer import RenameResult, rename_snapshot_file, update_snapshot_label
from envforge.snapshot import EnvSnapshot
from envforge.serializer import save_snapshot, load_snapshot


@pytest.fixture()
def sample_snapshot() -> EnvSnapshot:
    return EnvSnapshot(
        env_vars={"HOME": "/home/user", "PATH": "/usr/bin"},
        python_version="3.11.0",
        node_version="18.0.0",
        pip_packages={"requests": "2.31.0"},
        metadata={"name": "original"},
    )


@pytest.fixture()
def snapshot_file(tmp_path, sample_snapshot):
    path = tmp_path / "original.json"
    save_snapshot(sample_snapshot, str(path))
    return path


# ---------------------------------------------------------------------------
# RenameResult
# ---------------------------------------------------------------------------

def test_rename_result_bool_true():
    r = RenameResult("a", "b", "/some/path", True)
    assert bool(r) is True


def test_rename_result_bool_false():
    r = RenameResult("a", "b", "/some/path", False, "oops")
    assert bool(r) is False


# ---------------------------------------------------------------------------
# rename_snapshot_file
# ---------------------------------------------------------------------------

def test_rename_creates_new_file(tmp_path, snapshot_file):
    dst = tmp_path / "renamed.json"
    result = rename_snapshot_file(str(snapshot_file), str(dst))
    assert result.success
    assert os.path.isfile(str(dst))


def test_rename_removes_old_file(tmp_path, snapshot_file):
    dst = tmp_path / "renamed.json"
    rename_snapshot_file(str(snapshot_file), str(dst))
    assert not os.path.isfile(str(snapshot_file))


def test_rename_updates_metadata_name(tmp_path, snapshot_file):
    dst = tmp_path / "newname.json"
    rename_snapshot_file(str(snapshot_file), str(dst))
    snap = load_snapshot(str(dst))
    assert snap.metadata.get("name") == "newname"


def test_rename_appends_json_extension(tmp_path, snapshot_file):
    dst = tmp_path / "no_ext"
    result = rename_snapshot_file(str(snapshot_file), str(dst))
    assert result.path.endswith(".json")
    assert os.path.isfile(result.path)


def test_rename_fails_if_src_missing(tmp_path):
    result = rename_snapshot_file(
        str(tmp_path / "ghost.json"), str(tmp_path / "dst.json")
    )
    assert not result.success
    assert "not found" in (result.error or "")


def test_rename_fails_if_dst_exists_no_overwrite(tmp_path, snapshot_file, sample_snapshot):
    dst = tmp_path / "existing.json"
    save_snapshot(sample_snapshot, str(dst))
    result = rename_snapshot_file(str(snapshot_file), str(dst), overwrite=False)
    assert not result.success
    assert "already exists" in (result.error or "")


def test_rename_succeeds_with_overwrite(tmp_path, snapshot_file, sample_snapshot):
    dst = tmp_path / "existing.json"
    save_snapshot(sample_snapshot, str(dst))
    result = rename_snapshot_file(str(snapshot_file), str(dst), overwrite=True)
    assert result.success


# ---------------------------------------------------------------------------
# update_snapshot_label
# ---------------------------------------------------------------------------

def test_update_snapshot_label_sets_name(sample_snapshot):
    updated = update_snapshot_label(sample_snapshot, "my-label")
    assert updated.metadata["name"] == "my-label"


def test_update_snapshot_label_creates_metadata_if_none():
    snap = EnvSnapshot(
        env_vars={}, python_version=None, node_version=None,
        pip_packages={}, metadata=None,
    )
    updated = update_snapshot_label(snap, "fresh")
    assert updated.metadata["name"] == "fresh"
