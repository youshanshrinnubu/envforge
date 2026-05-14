"""Tests for envforge.cli_labeler."""

import argparse
import json
import pathlib

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.serializer import save_snapshot
from envforge.cli_labeler import add_labeler_subparser, cmd_label


@pytest.fixture()
def sample_snapshot() -> EnvSnapshot:
    return EnvSnapshot(
        label="original",
        env_vars={"HOME": "/home/user"},
        python_version="3.11.0",
        node_version="",
        pip_packages=[{"name": "requests", "version": "2.31.0"}],
        conda_packages=[],
        shell_aliases={},
    )


@pytest.fixture()
def snapshot_file(tmp_path: pathlib.Path, sample_snapshot: EnvSnapshot) -> pathlib.Path:
    p = tmp_path / "snap.json"
    save_snapshot(sample_snapshot, str(p))
    return p


@pytest.fixture()
def parser_with_label() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_labeler_subparser(subparsers)
    return parser


def _make_args(parser, *argv):
    return parser.parse_args(["label", *argv])


# --- registration ---

def test_add_labeler_subparser_registers(parser_with_label):
    args = _make_args(parser_with_label, "some_file.json")
    assert hasattr(args, "func")


# --- get label ---

def test_cmd_label_prints_existing_label(snapshot_file, parser_with_label, capsys):
    args = _make_args(parser_with_label, str(snapshot_file))
    rc = cmd_label(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "original" in out


def test_cmd_label_prints_no_label_when_empty(tmp_path, parser_with_label, capsys):
    snap = EnvSnapshot(
        label="",
        env_vars={},
        python_version="",
        node_version="",
        pip_packages=[],
        conda_packages=[],
        shell_aliases={},
    )
    p = tmp_path / "empty.json"
    save_snapshot(snap, str(p))
    args = _make_args(parser_with_label, str(p))
    rc = cmd_label(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "no label" in out


# --- set label ---

def test_cmd_label_set_updates_file(snapshot_file, parser_with_label):
    args = _make_args(parser_with_label, str(snapshot_file), "--set", "new-label")
    rc = cmd_label(args)
    assert rc == 0
    data = json.loads(snapshot_file.read_text())
    assert data["label"] == "new-label"


def test_cmd_label_set_prints_updated(snapshot_file, parser_with_label, capsys):
    args = _make_args(parser_with_label, str(snapshot_file), "--set", "prod")
    cmd_label(args)
    out = capsys.readouterr().out
    assert "prod" in out


# --- clear label ---

def test_cmd_label_clear_removes_label(snapshot_file, parser_with_label):
    args = _make_args(parser_with_label, str(snapshot_file), "--clear")
    rc = cmd_label(args)
    assert rc == 0
    data = json.loads(snapshot_file.read_text())
    assert data.get("label", "") == ""


# --- error handling ---

def test_cmd_label_missing_file_returns_1(tmp_path, parser_with_label):
    args = _make_args(parser_with_label, str(tmp_path / "ghost.json"))
    rc = cmd_label(args)
    assert rc == 1
