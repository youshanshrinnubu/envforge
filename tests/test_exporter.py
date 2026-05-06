"""Tests for envforge.exporter."""

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.exporter import (
    export_as_shell,
    export_as_dockerfile,
    export_as_requirements,
    export_snapshot,
    write_export,
    SUPPORTED_FORMATS,
)


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        env_vars={"HOME": "/root", "MY_VAR": 'say "hello"'},
        python_version="3.11.2",
        node_version="18.0.0",
        pip_packages={"requests": "2.28.0", "flask": "2.3.1"},
        shell="/bin/bash",
    )


@pytest.fixture
def empty_snapshot():
    """Snapshot with no pip packages or env vars, for edge-case testing."""
    return EnvSnapshot(
        env_vars={},
        python_version="3.10.0",
        node_version=None,
        pip_packages={},
        shell="/bin/bash",
    )


def test_supported_formats_constant():
    assert "shell" in SUPPORTED_FORMATS
    assert "dockerfile" in SUPPORTED_FORMATS
    assert "requirements" in SUPPORTED_FORMATS


def test_export_as_shell_contains_shebang(sample_snapshot):
    result = export_as_shell(sample_snapshot)
    assert result.startswith("#!/usr/bin/env bash")


def test_export_as_shell_exports_env_vars(sample_snapshot):
    result = export_as_shell(sample_snapshot)
    assert 'export HOME="/root"' in result
    assert 'export MY_VAR=' in result


def test_export_as_shell_escapes_quotes(sample_snapshot):
    result = export_as_shell(sample_snapshot)
    assert '\\"hello\\"' in result


def test_export_as_shell_contains_pip_packages(sample_snapshot):
    result = export_as_shell(sample_snapshot)
    assert "pip install" in result
    assert "requests==2.28.0" in result
    assert "flask==2.3.1" in result


def test_export_as_shell_empty_snapshot(empty_snapshot):
    """Shell export should still produce a valid script with no packages or vars."""
    result = export_as_shell(empty_snapshot)
    assert result.startswith("#!/usr/bin/env bash")
    assert "pip install" not in result
    assert "export" not in result


def test_export_as_dockerfile_has_from(sample_snapshot):
    result = export_as_dockerfile(sample_snapshot)
    assert "FROM python:3.11-slim" in result


def test_export_as_dockerfile_has_env(sample_snapshot):
    result = export_as_dockerfile(sample_snapshot)
    assert 'ENV HOME="/root"' in result


def test_export_as_dockerfile_has_run_pip(sample_snapshot):
    result = export_as_dockerfile(sample_snapshot)
    assert "RUN pip install" in result
    assert "requests==2.28.0" in result


def test_export_as_dockerfile_empty_snapshot(empty_snapshot):
    """Dockerfile export with no packages should omit the RUN pip install line."""
    result = export_as_dockerfile(empty_snapshot)
    assert "FROM python:3.10-slim" in result
    assert "RUN pip install" not in result


def test_export_as_requirements_format(sample_snapshot):
    result = export_as_requirements(sample_snapshot)
    assert "flask==2.3.1" in result
    assert "requests==2.28.0" in result
    assert result.endswith("\n")


def test_export_as_requirements_no_env_vars(sample_snapshot):
    result = export_as_requirements(sample_snapshot)
    assert "HOME" not in result


def test_export_as_requirements_empty_snapshot(empty_snapshot):
    """Requirements export of an empty snapshot should be an empty string or just a newline."""
    result = export_as_requirements(empty_snapshot)
    assert result.strip() == ""


def test_export_snapshot_dispatch(sample_snapshot):
    for fmt in SUPPORTED_FORMATS:
        result = export_snapshot(sample_snapshot, fmt)
        assert isinstance(result, str)
        assert len(result) > 0


def test_export_snapshot_invalid_format(sample_snapshot):
    with pytest.raises(ValueError, match="Unsupported format"):
        export_snapshot(sample_snapshot, "yaml")


def test_write_export_creates_file(tmp_path, sample_snapshot):
    out = tmp_path / "env_setup.sh"
    write_export(sample_snapshot, "shell", str(out))
    assert out.exists()
    content = out.read_text()
    assert "#!/usr/bin/env bash" in content
