"""Tests for envforge.cli_filterer."""
from __future__ import annotations

import argparse
import json
import os

import pytest

from envforge.cli_filterer import add_filterer_subparser, cmd_filter
from envforge.serializer import save_snapshot
from envforge.snapshot import EnvSnapshot


@pytest.fixture()
def sample_snapshot() -> EnvSnapshot:
    snap = EnvSnapshot()
    snap.env_vars = {
        "HOME": "/home/user",
        "AWS_KEY": "AKIA",
        "PATH": "/usr/bin",
    }
    snap.pip_packages = [
        {"name": "requests", "version": "2.31.0"},
        {"name": "boto3", "version": "1.34.0"},
    ]
    snap.python_version = "3.11.4"
    return snap


@pytest.fixture()
def snapshot_file(tmp_path, sample_snapshot):
    path = tmp_path / "snap.json"
    save_snapshot(sample_snapshot, str(path))
    return str(path)


@pytest.fixture()
def parser_with_filter():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_filterer_subparser(sub)
    return p


def _make_args(parser, snapshot, **kwargs):
    argv = ["filter", snapshot]
    for k, v in kwargs.items():
        argv += [f"--{k.replace('_', '-')}", v]
    return parser.parse_args(argv)


def test_add_filterer_subparser_registers(parser_with_filter):
    result = parser_with_filter.parse_args(["filter", "snap.json"])
    assert hasattr(result, "func")


def test_cmd_filter_missing_file_returns_1(parser_with_filter, tmp_path):
    args = _make_args(parser_with_filter, str(tmp_path / "missing.json"))
    assert cmd_filter(args) == 1


def test_cmd_filter_env_key_pattern_filters(parser_with_filter, snapshot_file):
    args = _make_args(parser_with_filter, snapshot_file, env_key_pattern="^AWS")
    rc = cmd_filter(args)
    assert rc == 0
    from envforge.serializer import load_snapshot
    snap = load_snapshot(snapshot_file)
    assert set(snap.env_vars.keys()) == {"AWS_KEY"}


def test_cmd_filter_pkg_pattern_filters(parser_with_filter, snapshot_file):
    args = _make_args(parser_with_filter, snapshot_file, pkg_name_pattern="requests")
    rc = cmd_filter(args)
    assert rc == 0
    from envforge.serializer import load_snapshot
    snap = load_snapshot(snapshot_file)
    assert len(snap.pip_packages) == 1
    assert snap.pip_packages[0]["name"] == "requests"


def test_cmd_filter_dry_run_does_not_write(parser_with_filter, snapshot_file):
    before = open(snapshot_file).read()
    argv = ["filter", snapshot_file, "--env-key-pattern", "^AWS", "--dry-run"]
    args = parser_with_filter.parse_args(argv)
    rc = cmd_filter(args)
    assert rc == 0
    assert open(snapshot_file).read() == before


def test_cmd_filter_output_flag_writes_new_file(parser_with_filter, snapshot_file, tmp_path):
    out = str(tmp_path / "filtered.json")
    argv = ["filter", snapshot_file, "--env-key-pattern", "^HOME", "--output", out]
    args = parser_with_filter.parse_args(argv)
    rc = cmd_filter(args)
    assert rc == 0
    assert os.path.exists(out)
