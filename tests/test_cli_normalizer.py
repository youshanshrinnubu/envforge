"""Tests for envforge.cli_normalizer."""

from __future__ import annotations

import argparse
import json
import pytest

from envforge.snapshot import EnvSnapshot
from envforge.serializer import save_snapshot
from envforge.cli_normalizer import add_normalizer_subparser, cmd_normalize


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        env_vars={"path": "/usr/bin", "home": "/root"},
        pip_packages=[{"name": "Requests", "version": "2.28.0"}],
        python_version="3.11.0",
    )


@pytest.fixture
def snapshot_file(tmp_path, sample_snapshot):
    p = tmp_path / "snap.json"
    save_snapshot(sample_snapshot, str(p))
    return p


@pytest.fixture
def parser_with_normalize():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_normalizer_subparser(sub)
    return p


def _make_args(**kwargs):
    base = {"dry_run": False, "output": None, "quiet": False}
    base.update(kwargs)
    return argparse.Namespace(**base)


def test_add_normalizer_subparser_registers(parser_with_normalize):
    args = parser_with_normalize.parse_args(["normalize", "snap.json"])
    assert hasattr(args, "func")


def test_cmd_normalize_missing_file_returns_1(tmp_path):
    args = _make_args(snapshot=str(tmp_path / "missing.json"))
    assert cmd_normalize(args) == 1


def test_cmd_normalize_writes_normalized_file(snapshot_file):
    args = _make_args(snapshot=str(snapshot_file))
    rc = cmd_normalize(args)
    assert rc == 0
    data = json.loads(snapshot_file.read_text())
    assert "PATH" in data.get("env_vars", {})


def test_cmd_normalize_dry_run_does_not_write(snapshot_file):
    original = snapshot_file.read_text()
    args = _make_args(snapshot=str(snapshot_file), dry_run=True)
    rc = cmd_normalize(args)
    assert rc == 0
    assert snapshot_file.read_text() == original


def test_cmd_normalize_output_to_different_file(snapshot_file, tmp_path):
    out = tmp_path / "out.json"
    args = _make_args(snapshot=str(snapshot_file), output=str(out))
    rc = cmd_normalize(args)
    assert rc == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert "PATH" in data.get("env_vars", {})


def test_cmd_normalize_quiet_flag(snapshot_file, capsys):
    args = _make_args(snapshot=str(snapshot_file), quiet=True)
    rc = cmd_normalize(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out == ""
