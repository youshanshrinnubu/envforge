"""Tests for envforge.cli_migrator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envforge.cli_migrator import add_migrator_subparser, cmd_migrate
from envforge.migrator import CURRENT_SCHEMA_VERSION
from envforge.serializer import load_snapshot
from envforge.snapshot import EnvSnapshot


@pytest.fixture()
def parser_with_migrate():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_migrator_subparser(sub)
    return p


@pytest.fixture()
def v0_snapshot_file(tmp_path):
    data = {
        "schema_version": 0,
        "label": "old",
        "env_vars": {"PATH": "/usr/bin"},
        "pip_packages": ["click==8.0.0"],
        "python_version": "3.10.0",
        "node_version": None,
        "shell": "bash",
    }
    p = tmp_path / "old.json"
    p.write_text(json.dumps(data))
    return str(p)


def _make_args(**kwargs):
    defaults = {
        "snapshot": None,
        "target_version": CURRENT_SCHEMA_VERSION,
        "in_place": False,
        "output": None,
        "func": cmd_migrate,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_migrator_subparser_registers(parser_with_migrate):
    parsed = parser_with_migrate.parse_args(["migrate", "some.json"])
    assert parsed.func is cmd_migrate


def test_cmd_migrate_missing_file_returns_1(tmp_path):
    args = _make_args(snapshot=str(tmp_path / "missing.json"))
    assert cmd_migrate(args) == 1


def test_cmd_migrate_already_current_returns_0(tmp_path):
    from envforge.serializer import save_snapshot
    snap = EnvSnapshot(
        label="current",
        env_vars={},
        pip_packages=[],
        python_version="3.11.0",
        node_version=None,
        shell="zsh",
    )
    p = tmp_path / "current.json"
    save_snapshot(snap, str(p))
    # patch schema_version to current
    data = json.loads(p.read_text())
    data["schema_version"] = CURRENT_SCHEMA_VERSION
    p.write_text(json.dumps(data))

    args = _make_args(snapshot=str(p), target_version=CURRENT_SCHEMA_VERSION)
    assert cmd_migrate(args) == 0


def test_cmd_migrate_in_place_upgrades_file(v0_snapshot_file):
    args = _make_args(snapshot=v0_snapshot_file, in_place=True)
    rc = cmd_migrate(args)
    assert rc == 0
    snap = load_snapshot(v0_snapshot_file)
    assert isinstance(snap, EnvSnapshot)
    assert all(isinstance(p, dict) for p in snap.pip_packages)


def test_cmd_migrate_output_writes_new_file(v0_snapshot_file, tmp_path):
    out = str(tmp_path / "migrated.json")
    args = _make_args(snapshot=v0_snapshot_file, output=out)
    rc = cmd_migrate(args)
    assert rc == 0
    assert Path(out).exists()
