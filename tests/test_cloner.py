"""Tests for envforge.cloner."""

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.cloner import CloneResult, clone_snapshot, clone_with_env_patch


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        label="base",
        python_version="3.11.2",
        node_version="18.0.0",
        env_vars={"HOME": "/home/user", "PATH": "/usr/bin"},
        pip_packages={"requests": "2.31.0", "flask": "3.0.0"},
    )


def test_clone_result_bool_true():
    r = CloneResult(original_label="a", cloned_label="b", success=True)
    assert bool(r) is True


def test_clone_result_bool_false():
    r = CloneResult(original_label="a", cloned_label="", success=False)
    assert bool(r) is False


def test_clone_preserves_original_label(sample_snapshot):
    cloned, result = clone_snapshot(sample_snapshot, "clone-1")
    assert sample_snapshot.label == "base"
    assert result.original_label == "base"


def test_clone_sets_new_label(sample_snapshot):
    cloned, result = clone_snapshot(sample_snapshot, "clone-1")
    assert cloned.label == "clone-1"
    assert result.cloned_label == "clone-1"


def test_clone_is_deep_copy(sample_snapshot):
    cloned, _ = clone_snapshot(sample_snapshot, "clone-1")
    cloned.env_vars["NEW_KEY"] = "value"
    assert "NEW_KEY" not in sample_snapshot.env_vars


def test_clone_inherits_env_vars(sample_snapshot):
    cloned, _ = clone_snapshot(sample_snapshot, "clone-1")
    assert cloned.env_vars == sample_snapshot.env_vars


def test_clone_override_env_vars(sample_snapshot):
    new_env = {"CUSTOM": "yes"}
    cloned, result = clone_snapshot(sample_snapshot, "clone-2", override_env_vars=new_env)
    assert cloned.env_vars == {"CUSTOM": "yes"}
    assert result.success is True


def test_clone_override_pip_packages(sample_snapshot):
    new_pkgs = {"numpy": "1.26.0"}
    cloned, _ = clone_snapshot(sample_snapshot, "clone-3", override_pip_packages=new_pkgs)
    assert cloned.pip_packages == {"numpy": "1.26.0"}


def test_clone_override_python_version(sample_snapshot):
    cloned, _ = clone_snapshot(sample_snapshot, "clone-4", override_python_version="3.12.0")
    assert cloned.python_version == "3.12.0"
    assert sample_snapshot.python_version == "3.11.2"


def test_clone_override_node_version(sample_snapshot):
    cloned, _ = clone_snapshot(sample_snapshot, "clone-5", override_node_version="20.0.0")
    assert cloned.node_version == "20.0.0"


def test_clone_empty_label_fails(sample_snapshot):
    _, result = clone_snapshot(sample_snapshot, "")
    assert result.success is False
    assert "non-empty" in result.message


def test_clone_whitespace_label_fails(sample_snapshot):
    _, result = clone_snapshot(sample_snapshot, "   ")
    assert result.success is False


def test_clone_with_env_patch_merges(sample_snapshot):
    cloned, result = clone_with_env_patch(sample_snapshot, "patched", {"EXTRA": "1"})
    assert cloned.env_vars["HOME"] == "/home/user"
    assert cloned.env_vars["EXTRA"] == "1"
    assert result.success is True


def test_clone_with_env_patch_overrides_existing(sample_snapshot):
    cloned, _ = clone_with_env_patch(sample_snapshot, "patched", {"HOME": "/root"})
    assert cloned.env_vars["HOME"] == "/root"
    assert sample_snapshot.env_vars["HOME"] == "/home/user"
