"""Tests for envforge.tagger module."""

import pytest
from pathlib import Path

from envforge.tagger import (
    add_tags,
    remove_tags,
    get_tags,
    find_by_tag,
    clear_tags,
    get_tags_file,
)


@pytest.fixture
def tag_dir(tmp_path):
    return str(tmp_path)


def test_get_tags_file_creates_directory(tmp_path):
    subdir = str(tmp_path / "nested" / "envforge")
    tags_file = get_tags_file(subdir)
    assert tags_file.exists() or tags_file.parent.exists()
    assert tags_file.name == ".envforge_tags.json"


def test_add_tags_single(tag_dir):
    result = add_tags("snap-001", ["production"], directory=tag_dir)
    assert "production" in result


def test_add_tags_multiple(tag_dir):
    result = add_tags("snap-002", ["dev", "python3", "ml"], directory=tag_dir)
    assert set(result) == {"dev", "python3", "ml"}


def test_add_tags_deduplicates(tag_dir):
    add_tags("snap-003", ["stable"], directory=tag_dir)
    result = add_tags("snap-003", ["stable", "release"], directory=tag_dir)
    assert result.count("stable") == 1
    assert "release" in result


def test_get_tags_returns_empty_for_unknown(tag_dir):
    tags = get_tags("nonexistent-snap", directory=tag_dir)
    assert tags == []


def test_get_tags_returns_added_tags(tag_dir):
    add_tags("snap-004", ["alpha", "beta"], directory=tag_dir)
    tags = get_tags("snap-004", directory=tag_dir)
    assert "alpha" in tags
    assert "beta" in tags


def test_remove_tags_removes_specific(tag_dir):
    add_tags("snap-005", ["v1", "v2", "v3"], directory=tag_dir)
    result = remove_tags("snap-005", ["v2"], directory=tag_dir)
    assert "v2" not in result
    assert "v1" in result
    assert "v3" in result


def test_remove_tags_nonexistent_tag_is_noop(tag_dir):
    add_tags("snap-006", ["keep"], directory=tag_dir)
    result = remove_tags("snap-006", ["missing"], directory=tag_dir)
    assert result == ["keep"]


def test_find_by_tag_returns_matching_snapshots(tag_dir):
    add_tags("snap-007", ["shared", "gpu"], directory=tag_dir)
    add_tags("snap-008", ["shared", "cpu"], directory=tag_dir)
    add_tags("snap-009", ["gpu"], directory=tag_dir)
    result = find_by_tag("shared", directory=tag_dir)
    assert "snap-007" in result
    assert "snap-008" in result
    assert "snap-009" not in result


def test_find_by_tag_returns_empty_when_none_match(tag_dir):
    result = find_by_tag("no-such-tag", directory=tag_dir)
    assert result == []


def test_clear_tags_removes_all(tag_dir):
    add_tags("snap-010", ["x", "y", "z"], directory=tag_dir)
    clear_tags("snap-010", directory=tag_dir)
    assert get_tags("snap-010", directory=tag_dir) == []


def test_clear_tags_nonexistent_is_noop(tag_dir):
    clear_tags("snap-999", directory=tag_dir)  # should not raise


def test_tags_are_sorted(tag_dir):
    result = add_tags("snap-011", ["zebra", "apple", "mango"], directory=tag_dir)
    assert result == sorted(result)
