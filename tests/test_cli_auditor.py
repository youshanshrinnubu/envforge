"""Tests for envforge.cli_auditor."""

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from envforge.auditor import record_audit
from envforge.cli_auditor import add_auditor_subparser, cmd_audit


@pytest.fixture()
def audit_dir(tmp_path: Path) -> Path:
    return tmp_path / "audit"


@pytest.fixture()
def parser_with_audit():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    add_auditor_subparser(sub)
    return p


def _make_args(parser, argv):
    return parser.parse_args(argv)


def test_add_auditor_subparser_registers(parser_with_audit):
    args = _make_args(parser_with_audit, ["audit", "list"])
    assert args.cmd == "audit"


def test_cmd_audit_list_empty(audit_dir, parser_with_audit, capsys):
    args = _make_args(parser_with_audit, ["audit", "list", "--audit-dir", str(audit_dir)])
    rc = cmd_audit(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "No audit entries" in captured.out


def test_cmd_audit_list_shows_entries(audit_dir, parser_with_audit, capsys):
    record_audit("capture", "my-snap", audit_dir=audit_dir)
    args = _make_args(parser_with_audit, ["audit", "list", "--audit-dir", str(audit_dir)])
    rc = cmd_audit(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "capture" in out
    assert "my-snap" in out


def test_cmd_audit_list_filter_operation(audit_dir, parser_with_audit, capsys):
    record_audit("capture", "s1", audit_dir=audit_dir)
    record_audit("reproduce", "s2", audit_dir=audit_dir)
    args = _make_args(
        parser_with_audit,
        ["audit", "list", "--operation", "reproduce", "--audit-dir", str(audit_dir)],
    )
    cmd_audit(args)
    out = capsys.readouterr().out
    assert "reproduce" in out
    assert "capture" not in out


def test_cmd_audit_clear_with_yes_flag(audit_dir, parser_with_audit, capsys):
    record_audit("capture", "s1", audit_dir=audit_dir)
    args = _make_args(
        parser_with_audit,
        ["audit", "clear", "--yes", "--audit-dir", str(audit_dir)],
    )
    rc = cmd_audit(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "1" in out


def test_cmd_audit_clear_aborted(audit_dir, parser_with_audit, capsys):
    record_audit("capture", "s1", audit_dir=audit_dir)
    args = _make_args(
        parser_with_audit,
        ["audit", "clear", "--audit-dir", str(audit_dir)],
    )
    with patch("builtins.input", return_value="n"):
        rc = cmd_audit(args)
    assert rc == 1
    out = capsys.readouterr().out
    assert "Aborted" in out
