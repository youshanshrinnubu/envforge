"""Tests for envforge.cli_annotator."""

from __future__ import annotations

import argparse
import json
import os

import pytest

from envforge.cli_annotator import add_annotator_subparser, cmd_annotate
from envforge.serializer import save_snapshot
from envforge.snapshot import EnvSnapshot


@pytest.fixture
def sample_snapshot() -> EnvSnapshot:
    return EnvSnapshot(
        label="cli-test",
        env_vars={"PATH": "/usr/bin"},
        python_version="3.10.0",
        node_version=None,
        pip_packages={},
        extra={},
    )


@pytest.fixture
def snapshot_file(tmp_path, sample_snapshot):
    p = tmp_path / "snap.json"
    save_snapshot(sample_snapshot, str(p))
    return str(p)


@pytest.fixture
def parser_with_annotate():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    add_annotator_subparser(sub)
    return p


def _make_args(parser, *argv):
    return parser.parse_args(["annotate"] + list(argv))


def test_add_annotator_subparser_registers(parser_with_annotate):
    choices = parser_with_annotate._subparsers._actions[-1].choices
    assert "annotate" in choices


def test_cmd_annotate_list_empty(parser_with_annotate, snapshot_file, capsys):
    args = _make_args(parser_with_annotate, "list", snapshot_file)
    rc = cmd_annotate(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No annotations" in out


def test_cmd_annotate_add(parser_with_annotate, snapshot_file, capsys):
    args = _make_args(parser_with_annotate, "add", snapshot_file, "my note", "--author", "tester")
    rc = cmd_annotate(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "my note" in out


def test_cmd_annotate_list_after_add(parser_with_annotate, snapshot_file, capsys):
    add_args = _make_args(parser_with_annotate, "add", snapshot_file, "hello world")
    cmd_annotate(add_args)
    list_args = _make_args(parser_with_annotate, "list", snapshot_file)
    cmd_annotate(list_args)
    out = capsys.readouterr().out
    assert "hello world" in out


def test_cmd_annotate_remove(parser_with_annotate, snapshot_file):
    add_args = _make_args(parser_with_annotate, "add", snapshot_file, "to delete")
    cmd_annotate(add_args)
    rm_args = _make_args(parser_with_annotate, "remove", snapshot_file, "0")
    rc = cmd_annotate(rm_args)
    assert rc == 0


def test_cmd_annotate_remove_bad_index(parser_with_annotate, snapshot_file):
    rm_args = _make_args(parser_with_annotate, "remove", snapshot_file, "99")
    rc = cmd_annotate(rm_args)
    assert rc == 1


def test_cmd_annotate_clear(parser_with_annotate, snapshot_file, capsys):
    cmd_annotate(_make_args(parser_with_annotate, "add", snapshot_file, "a"))
    cmd_annotate(_make_args(parser_with_annotate, "add", snapshot_file, "b"))
    rc = cmd_annotate(_make_args(parser_with_annotate, "clear", snapshot_file))
    assert rc == 0
    out = capsys.readouterr().out
    assert "2" in out
