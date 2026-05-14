"""Tests for envforge.cli_snapcmp."""
import argparse
import json
import os
import pytest

from envforge.snapshot import EnvSnapshot
from envforge.serializer import save_snapshot
from envforge.cli_snapcmp import add_snapcmp_subparser, cmd_snapcmp


@pytest.fixture
def base_snapshot(tmp_path):
    snap = EnvSnapshot(
        label="base",
        python_version="3.10.0",
        env_vars={"HOME": "/home/user"},
        pip_packages={"requests": "2.28.0"},
    )
    path = str(tmp_path / "base.json")
    save_snapshot(snap, path)
    return path


@pytest.fixture
def other_snapshot(tmp_path):
    snap = EnvSnapshot(
        label="other",
        python_version="3.11.0",
        env_vars={"HOME": "/home/other"},
        pip_packages={"requests": "2.29.0"},
    )
    path = str(tmp_path / "other.json")
    save_snapshot(snap, path)
    return path


@pytest.fixture
def parser_with_snapcmp():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_snapcmp_subparser(sub)
    return p


def _make_args(left, right, left_label=None, right_label=None, exit_code=False):
    ns = argparse.Namespace(
        left=left,
        right=right,
        left_label=left_label,
        right_label=right_label,
        exit_code=exit_code,
    )
    return ns


def test_add_snapcmp_subparser_registers(parser_with_snapcmp):
    args = parser_with_snapcmp.parse_args(["snapcmp", "a.json", "b.json"])
    assert hasattr(args, "func")


def test_cmd_snapcmp_returns_zero_identical(base_snapshot):
    args = _make_args(base_snapshot, base_snapshot)
    result = cmd_snapcmp(args)
    assert result == 0


def test_cmd_snapcmp_returns_zero_with_diff_no_exit_code(base_snapshot, other_snapshot):
    args = _make_args(base_snapshot, other_snapshot, exit_code=False)
    result = cmd_snapcmp(args)
    assert result == 0


def test_cmd_snapcmp_returns_one_with_diff_and_exit_code(base_snapshot, other_snapshot):
    args = _make_args(base_snapshot, other_snapshot, exit_code=True)
    result = cmd_snapcmp(args)
    assert result == 1


def test_cmd_snapcmp_exit_code_zero_when_identical(base_snapshot):
    args = _make_args(base_snapshot, base_snapshot, exit_code=True)
    result = cmd_snapcmp(args)
    assert result == 0


def test_cmd_snapcmp_custom_labels(base_snapshot, other_snapshot, capsys):
    args = _make_args(
        base_snapshot, other_snapshot,
        left_label="PROD", right_label="DEV", exit_code=False
    )
    cmd_snapcmp(args)
    captured = capsys.readouterr()
    assert "PROD" in captured.out
    assert "DEV" in captured.out
