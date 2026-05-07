"""Tests for envforge.cli_linter module."""

import argparse
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from envforge.snapshot import EnvSnapshot
from envforge.cli_linter import add_linter_subparser, cmd_lint
from envforge.linter import LintResult, LintIssue, SEVERITY_ERROR, SEVERITY_WARNING, SEVERITY_INFO


@pytest.fixture
def parser_with_lint():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_linter_subparser(subparsers)
    return parser


@pytest.fixture
def snapshot_file(tmp_path):
    snap = {
        "python_version": "3.11.4",
        "node_version": None,
        "pip_packages": {"requests": "2.31.0"},
        "env_vars": {"HOME": "/home/user"},
        "shell": "bash",
    }
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(snap))
    return str(p)


def _make_args(snapshot, strict=False, min_severity=SEVERITY_INFO):
    args = argparse.Namespace(
        snapshot=snapshot,
        strict=strict,
        min_severity=min_severity,
        func=cmd_lint,
    )
    return args


def test_add_linter_subparser_registers(parser_with_lint):
    args = parser_with_lint.parse_args(["lint", "some_file.json"])
    assert args.func == cmd_lint


def test_cmd_lint_returns_zero_on_clean(snapshot_file):
    args = _make_args(snapshot_file)
    result = cmd_lint(args)
    assert result == 0


def test_cmd_lint_missing_file_returns_one():
    args = _make_args("/nonexistent/path/snap.json")
    result = cmd_lint(args)
    assert result == 1


def test_cmd_lint_returns_two_on_errors(snapshot_file):
    error_result = LintResult(issues=[LintIssue("L002", SEVERITY_ERROR, "bad version")])
    with patch("envforge.cli_linter.lint_snapshot", return_value=error_result):
        args = _make_args(snapshot_file)
        result = cmd_lint(args)
    assert result == 2


def test_cmd_lint_strict_returns_one_on_warnings(snapshot_file):
    warn_result = LintResult(issues=[LintIssue("L003", SEVERITY_WARNING, "unpinned")])
    with patch("envforge.cli_linter.lint_snapshot", return_value=warn_result):
        args = _make_args(snapshot_file, strict=True)
        result = cmd_lint(args)
    assert result == 1


def test_cmd_lint_non_strict_warnings_returns_zero(snapshot_file):
    warn_result = LintResult(issues=[LintIssue("L003", SEVERITY_WARNING, "unpinned")])
    with patch("envforge.cli_linter.lint_snapshot", return_value=warn_result):
        args = _make_args(snapshot_file, strict=False)
        result = cmd_lint(args)
    assert result == 0


def test_cmd_lint_min_severity_filters_info(snapshot_file, capsys):
    mixed = LintResult(issues=[
        LintIssue("L004", SEVERITY_INFO, "no packages"),
        LintIssue("L001", SEVERITY_WARNING, "no python version"),
    ])
    with patch("envforge.cli_linter.lint_snapshot", return_value=mixed):
        args = _make_args(snapshot_file, min_severity=SEVERITY_WARNING)
        cmd_lint(args)
    captured = capsys.readouterr()
    assert "L001" in captured.out
    assert "L004" not in captured.out
