"""Tests for envforge.cli_history CLI subcommands."""

import argparse
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envforge.snapshot import EnvSnapshot
from envforge.history import record_snapshot
from envforge.cli_history import add_history_subparser, cmd_history


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        env_vars={"HOME": "/home/user"},
        python_version="3.10.0",
        node_version="16.0.0",
        pip_packages={"numpy": "1.24.0"},
        shell="zsh",
    )


@pytest.fixture
def parser_with_history():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_history_subparser(sub)
    return parser


def _make_args(history_action, **kwargs):
    ns = argparse.Namespace(history_action=history_action, history_dir=None)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def test_add_history_subparser_registers(parser_with_history):
    args = parser_with_history.parse_args(["history", "list"])
    assert args.command == "history"
    assert args.history_action == "list"


def test_cmd_history_list_empty(tmp_path, capsys):
    args = _make_args("list", history_dir=tmp_path / "empty")
    ret = cmd_history(args)
    assert ret == 0
    out = capsys.readouterr().out
    assert "No history entries" in out


def test_cmd_history_list_with_entries(sample_snapshot, tmp_path, capsys):
    hdir = tmp_path / "hist"
    record_snapshot(sample_snapshot, label="test", history_dir=hdir)
    args = _make_args("list", history_dir=hdir)
    ret = cmd_history(args)
    assert ret == 0
    out = capsys.readouterr().out
    assert "test" in out


def test_cmd_history_show_valid(sample_snapshot, tmp_path, capsys):
    hdir = tmp_path / "hist"
    path = record_snapshot(sample_snapshot, label="show_test", history_dir=hdir)
    args = _make_args("show", filename=path.name, history_dir=hdir)
    ret = cmd_history(args)
    assert ret == 0
    out = capsys.readouterr().out
    assert "3.10.0" in out


def test_cmd_history_show_not_found(tmp_path, capsys):
    args = _make_args("show", filename="missing.json", history_dir=tmp_path)
    ret = cmd_history(args)
    assert ret == 1
    err = capsys.readouterr().err
    assert "Error" in err


def test_cmd_history_reproduce(sample_snapshot, tmp_path, capsys):
    hdir = tmp_path / "hist"
    path = record_snapshot(sample_snapshot, history_dir=hdir)
    output = str(tmp_path / "out.sh")
    args = _make_args("reproduce", filename=path.name, history_dir=hdir, output=output)
    ret = cmd_history(args)
    assert ret == 0
    assert Path(output).exists()


def test_cmd_history_delete(sample_snapshot, tmp_path, capsys):
    hdir = tmp_path / "hist"
    path = record_snapshot(sample_snapshot, history_dir=hdir)
    args = _make_args("delete", filename=path.name, history_dir=hdir)
    ret = cmd_history(args)
    assert ret == 0
    assert not path.exists()


def test_cmd_history_delete_not_found(tmp_path, capsys):
    args = _make_args("delete", filename="nope.json", history_dir=tmp_path)
    ret = cmd_history(args)
    assert ret == 1
