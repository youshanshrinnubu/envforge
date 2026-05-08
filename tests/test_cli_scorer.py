"""Tests for envforge.cli_scorer."""

import argparse
import json
import pytest
from pathlib import Path
from envforge.snapshot import EnvSnapshot
from envforge.serializer import save_snapshot
from envforge.cli_scorer import add_scorer_subparser, cmd_score


@pytest.fixture
def snapshot_file(tmp_path):
    snap = EnvSnapshot(
        python_version="3.11.4",
        node_version="20.1.0",
        pip_packages={"requests": "2.31.0"},
        env_vars={"HOME": "/home/dev", "PATH": "/usr/bin", "SHELL": "/bin/bash",
                  "USER": "dev", "LANG": "en_US.UTF-8"},
    )
    path = tmp_path / "snap.json"
    save_snapshot(snap, str(path))
    return str(path)


@pytest.fixture
def parser_with_score():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_scorer_subparser(sub)
    return p


def _make_args(parser, *argv):
    return parser.parse_args(["score", *argv])


def test_add_scorer_subparser_registers(parser_with_score):
    args = _make_args(parser_with_score, "snap.json")
    assert hasattr(args, "func")
    assert args.func is cmd_score


def test_cmd_score_returns_zero_on_good_snapshot(snapshot_file, parser_with_score):
    args = _make_args(parser_with_score, snapshot_file)
    assert cmd_score(args) == 0


def test_cmd_score_quiet_mode(snapshot_file, parser_with_score, capsys):
    args = _make_args(parser_with_score, snapshot_file, "--quiet")
    rc = cmd_score(args)
    captured = capsys.readouterr()
    assert captured.out.strip().isdigit()
    assert rc == 0


def test_cmd_score_min_score_fail(tmp_path, parser_with_score):
    snap = EnvSnapshot(python_version=None, node_version=None, pip_packages={}, env_vars={})
    path = tmp_path / "empty.json"
    save_snapshot(snap, str(path))
    args = _make_args(parser_with_score, str(path), "--min-score", "80")
    assert cmd_score(args) == 1


def test_cmd_score_min_score_pass(snapshot_file, parser_with_score):
    args = _make_args(parser_with_score, snapshot_file, "--min-score", "1")
    assert cmd_score(args) == 0


def test_cmd_score_missing_file(tmp_path, parser_with_score):
    args = _make_args(parser_with_score, str(tmp_path / "nope.json"))
    assert cmd_score(args) == 2


def test_cmd_score_prints_breakdown(snapshot_file, parser_with_score, capsys):
    args = _make_args(parser_with_score, snapshot_file)
    cmd_score(args)
    out = capsys.readouterr().out
    assert "python_version" in out
    assert "pip_packages" in out
