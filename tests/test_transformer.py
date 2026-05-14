"""Tests for envforge.transformer."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.transformer import (
    TransformResult,
    apply_transforms,
    transform_env_vars,
    transform_pip_packages,
)


@pytest.fixture()
def sample_snapshot() -> EnvSnapshot:
    return EnvSnapshot(
        label="test",
        python_version="3.11.0",
        node_version="18.0.0",
        env_vars={"HOME": "/root", "SECRET_KEY": "abc123", "PATH": "/usr/bin"},
        pip_packages=[
            {"name": "requests", "version": "2.31.0"},
            {"name": "flask", "version": ""},
            {"name": "numpy", "version": "1.24.0"},
        ],
        shell="bash",
        os_info="Linux",
    )


# --- TransformResult ---

def test_transform_result_bool_true_when_applied():
    snap = EnvSnapshot(label="x", env_vars={}, pip_packages=[])
    r = TransformResult(snapshot=snap, applied=["A"], skipped=[])
    assert bool(r) is True


def test_transform_result_bool_false_when_nothing_applied():
    snap = EnvSnapshot(label="x", env_vars={}, pip_packages=[])
    r = TransformResult(snapshot=snap, applied=[], skipped=["B"])
    assert bool(r) is False


# --- transform_env_vars ---

def test_transform_env_vars_identity(sample_snapshot):
    result = transform_env_vars(sample_snapshot, lambda k, v: v)
    assert result.snapshot.env_vars == sample_snapshot.env_vars
    assert result.applied == []
    assert result.skipped == []


def test_transform_env_vars_drops_key_on_none(sample_snapshot):
    def drop_secret(k: str, v: str) -> Optional[str]:
        return None if "SECRET" in k else v

    result = transform_env_vars(sample_snapshot, drop_secret)
    assert "SECRET_KEY" not in result.snapshot.env_vars
    assert "SECRET_KEY" in result.skipped
    assert "HOME" in result.snapshot.env_vars


def test_transform_env_vars_mutates_value(sample_snapshot):
    def mask(k: str, v: str) -> str:
        return "***" if "SECRET" in k else v

    result = transform_env_vars(sample_snapshot, mask)
    assert result.snapshot.env_vars["SECRET_KEY"] == "***"
    assert "SECRET_KEY" in result.applied


def test_transform_env_vars_does_not_mutate_original(sample_snapshot):
    original_vars = dict(sample_snapshot.env_vars)
    transform_env_vars(sample_snapshot, lambda k, v: "X")
    assert sample_snapshot.env_vars == original_vars


# --- transform_pip_packages ---

def test_transform_pip_packages_identity(sample_snapshot):
    result = transform_pip_packages(sample_snapshot, lambda p: p)
    assert result.snapshot.pip_packages == sample_snapshot.pip_packages
    assert result.applied == []


def test_transform_pip_packages_drops_on_none(sample_snapshot):
    def drop_flask(pkg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None if pkg.get("name") == "flask" else pkg

    result = transform_pip_packages(sample_snapshot, drop_flask)
    names = [p["name"] for p in result.snapshot.pip_packages]
    assert "flask" not in names
    assert "flask" in result.skipped
    assert "requests" in names


def test_transform_pip_packages_mutates_entry(sample_snapshot):
    def pin(pkg: Dict[str, Any]) -> Dict[str, Any]:
        if not pkg.get("version"):
            return {**pkg, "version": "0.0.0"}
        return pkg

    result = transform_pip_packages(sample_snapshot, pin)
    flask_entry = next(p for p in result.snapshot.pip_packages if p["name"] == "flask")
    assert flask_entry["version"] == "0.0.0"
    assert "flask" in result.applied


# --- apply_transforms ---

def test_apply_transforms_both_transformers(sample_snapshot):
    env_t = lambda k, v: None if "SECRET" in k else v  # noqa: E731
    pkg_t = lambda p: None if not p.get("version") else p  # noqa: E731

    result = apply_transforms(sample_snapshot, env_transformer=env_t, pkg_transformer=pkg_t)
    assert "SECRET_KEY" not in result.snapshot.env_vars
    pkg_names = [p["name"] for p in result.snapshot.pip_packages]
    assert "flask" not in pkg_names


def test_apply_transforms_no_transformers_returns_copy(sample_snapshot):
    result = apply_transforms(sample_snapshot)
    assert result.snapshot is not sample_snapshot
    assert result.snapshot.env_vars == sample_snapshot.env_vars
    assert result.applied == []
    assert result.skipped == []


def test_apply_transforms_only_env_transformer(sample_snapshot):
    result = apply_transforms(sample_snapshot, env_transformer=lambda k, v: v.upper())
    assert result.snapshot.env_vars["HOME"] == "/ROOT"
    assert result.snapshot.pip_packages == sample_snapshot.pip_packages
