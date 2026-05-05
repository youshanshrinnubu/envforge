"""Tests for envforge.reproducer."""

from __future__ import annotations

import os
import stat
import textwrap

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.reproducer import (
    build_reproduction_script,
    generate_env_exports,
    generate_pip_install,
    generate_version_checks,
    write_reproduction_script,
)


@pytest.fixture()
def sample_snapshot() -> EnvSnapshot:
    return EnvSnapshot(
        env_vars={"HOME": "/home/user", "EDITOR": "vim", 'PATH': '/usr/bin'},
        python_version="3.11.4",
        node_version="18.17.0",
        pip_packages=["requests==2.31.0", "pytest==7.4.0"],
    )


def test_generate_env_exports_contains_keys(sample_snapshot):
    result = generate_env_exports(sample_snapshot)
    assert 'export EDITOR="vim"' in result
    assert 'export HOME="/home/user"' in result


def test_generate_env_exports_escapes_quotes():
    snap = EnvSnapshot(
        env_vars={"GREETING": 'say "hello"'},
        python_version=None,
        node_version=None,
        pip_packages=[],
    )
    result = generate_env_exports(snap)
    assert 'say \\"hello\\"' in result


def test_generate_pip_install_contains_packages(sample_snapshot):
    result = generate_pip_install(sample_snapshot)
    assert "requests==2.31.0" in result
    assert "pytest==7.4.0" in result
    assert result.startswith("# Python pip packages")


def test_generate_pip_install_empty():
    snap = EnvSnapshot(
        env_vars={}, python_version=None, node_version=None, pip_packages=[]
    )
    result = generate_pip_install(snap)
    assert result == "# No pip packages captured"


def test_generate_version_checks(sample_snapshot):
    result = generate_version_checks(sample_snapshot)
    assert "3.11.4" in result
    assert "18.17.0" in result


def test_build_reproduction_script_structure(sample_snapshot):
    script = build_reproduction_script(sample_snapshot)
    assert script.startswith("#!/usr/bin/env bash")
    assert "export EDITOR" in script
    assert "pip install" in script
    assert "Environment reproduced successfully" in script


def test_build_reproduction_script_exclude_env(sample_snapshot):
    script = build_reproduction_script(sample_snapshot, include_env=False)
    assert "export EDITOR" not in script
    assert "pip install" in script


def test_build_reproduction_script_exclude_packages(sample_snapshot):
    script = build_reproduction_script(sample_snapshot, include_packages=False)
    assert "pip install" not in script
    assert "export EDITOR" in script


def test_write_reproduction_script_creates_file(tmp_path, sample_snapshot):
    output = str(tmp_path / "reproduce.sh")
    returned = write_reproduction_script(sample_snapshot, output)
    assert returned == output
    assert os.path.isfile(output)
    file_stat = os.stat(output)
    assert file_stat.st_mode & stat.S_IXUSR, "Script should be executable"


def test_write_reproduction_script_content(tmp_path, sample_snapshot):
    output = str(tmp_path / "reproduce.sh")
    write_reproduction_script(sample_snapshot, output)
    content = open(output).read()
    assert "#!/usr/bin/env bash" in content
    assert "requests==2.31.0" in content
