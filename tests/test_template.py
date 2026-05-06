"""Tests for envforge.template module."""

import pytest
from pathlib import Path

from envforge.snapshot import EnvSnapshot
from envforge.template import (
    save_template,
    load_template,
    list_templates,
    delete_template,
    template_path,
)


@pytest.fixture
def tmp_template_dir(tmp_path):
    return tmp_path / "templates"


@pytest.fixture
def sample_snapshot():
    return EnvSnapshot(
        env_vars={"HOME": "/home/user", "LANG": "en_US.UTF-8"},
        python_version="3.11.4",
        node_version="18.17.0",
        pip_packages=["requests==2.31.0", "flask==3.0.0"],
        shell="/bin/bash",
    )


def test_save_and_load_template(tmp_template_dir, sample_snapshot):
    path = save_template("myenv", sample_snapshot, tmp_template_dir)
    assert path.exists()
    loaded = load_template("myenv", tmp_template_dir)
    assert loaded.python_version == sample_snapshot.python_version
    assert loaded.env_vars == sample_snapshot.env_vars
    assert loaded.pip_packages == sample_snapshot.pip_packages


def test_template_path_has_json_extension(tmp_template_dir, sample_snapshot):
    save_template("myenv", sample_snapshot, tmp_template_dir)
    p = template_path("myenv", tmp_template_dir)
    assert p.suffix == ".json"
    assert p.stem == "myenv"


def test_list_templates_empty(tmp_template_dir):
    assert list_templates(tmp_template_dir) == []


def test_list_templates_multiple(tmp_template_dir, sample_snapshot):
    save_template("alpha", sample_snapshot, tmp_template_dir)
    save_template("beta", sample_snapshot, tmp_template_dir)
    save_template("gamma", sample_snapshot, tmp_template_dir)
    names = list_templates(tmp_template_dir)
    assert names == ["alpha", "beta", "gamma"]


def test_delete_existing_template(tmp_template_dir, sample_snapshot):
    save_template("todelete", sample_snapshot, tmp_template_dir)
    result = delete_template("todelete", tmp_template_dir)
    assert result is True
    assert list_templates(tmp_template_dir) == []


def test_delete_nonexistent_template(tmp_template_dir):
    result = delete_template("ghost", tmp_template_dir)
    assert result is False


def test_load_missing_template_raises(tmp_template_dir):
    with pytest.raises(FileNotFoundError, match="Template 'missing' not found"):
        load_template("missing", tmp_template_dir)


def test_invalid_template_name_raises(tmp_template_dir, sample_snapshot):
    with pytest.raises(ValueError, match="Invalid template name"):
        save_template("bad/name", sample_snapshot, tmp_template_dir)


def test_save_template_creates_dir(tmp_path, sample_snapshot):
    new_dir = tmp_path / "deep" / "nested"
    save_template("env", sample_snapshot, new_dir)
    assert new_dir.exists()
    assert (new_dir / "env.json").exists()
