"""Tests for envforge.labeler."""

import pytest

from envforge.snapshot import EnvSnapshot
from envforge.labeler import (
    LabelResult,
    get_label,
    set_label,
    clear_label,
    has_label,
    label_matches,
)


@pytest.fixture()
def unlabeled_snapshot() -> EnvSnapshot:
    return EnvSnapshot(
        label="",
        env_vars={"HOME": "/home/user"},
        python_version="3.11.0",
        node_version="",
        pip_packages=[],
        conda_packages=[],
        shell_aliases={},
    )


@pytest.fixture()
def labeled_snapshot(unlabeled_snapshot: EnvSnapshot) -> EnvSnapshot:
    unlabeled_snapshot.label = "my-env"
    return unlabeled_snapshot


# --- get_label ---

def test_get_label_returns_none_when_empty(unlabeled_snapshot):
    assert get_label(unlabeled_snapshot) is None


def test_get_label_returns_label(labeled_snapshot):
    assert get_label(labeled_snapshot) == "my-env"


# --- set_label ---

def test_set_label_returns_label_result(unlabeled_snapshot):
    result = set_label(unlabeled_snapshot, "prod")
    assert isinstance(result, LabelResult)


def test_set_label_updates_snapshot(unlabeled_snapshot):
    set_label(unlabeled_snapshot, "prod")
    assert unlabeled_snapshot.label == "prod"


def test_set_label_changed_true_when_new(unlabeled_snapshot):
    result = set_label(unlabeled_snapshot, "prod")
    assert result.changed is True
    assert bool(result) is True


def test_set_label_changed_false_when_same(labeled_snapshot):
    result = set_label(labeled_snapshot, "my-env")
    assert result.changed is False
    assert bool(result) is False


def test_set_label_records_previous(labeled_snapshot):
    result = set_label(labeled_snapshot, "new-label")
    assert result.previous_label == "my-env"
    assert result.new_label == "new-label"


def test_set_label_strips_whitespace(unlabeled_snapshot):
    result = set_label(unlabeled_snapshot, "  dev  ")
    assert result.new_label == "dev"


def test_set_label_raises_on_empty_string(unlabeled_snapshot):
    with pytest.raises(ValueError):
        set_label(unlabeled_snapshot, "")


def test_set_label_raises_on_whitespace_only(unlabeled_snapshot):
    with pytest.raises(ValueError):
        set_label(unlabeled_snapshot, "   ")


# --- clear_label ---

def test_clear_label_removes_label(labeled_snapshot):
    clear_label(labeled_snapshot)
    assert get_label(labeled_snapshot) is None


def test_clear_label_changed_true_when_had_label(labeled_snapshot):
    result = clear_label(labeled_snapshot)
    assert result.changed is True


def test_clear_label_changed_false_when_no_label(unlabeled_snapshot):
    result = clear_label(unlabeled_snapshot)
    assert result.changed is False


# --- has_label ---

def test_has_label_false_when_empty(unlabeled_snapshot):
    assert has_label(unlabeled_snapshot) is False


def test_has_label_true_when_set(labeled_snapshot):
    assert has_label(labeled_snapshot) is True


# --- label_matches ---

def test_label_matches_substring(labeled_snapshot):
    assert label_matches(labeled_snapshot, "my") is True


def test_label_matches_case_insensitive(labeled_snapshot):
    assert label_matches(labeled_snapshot, "MY-ENV") is True


def test_label_matches_false_on_no_match(labeled_snapshot):
    assert label_matches(labeled_snapshot, "prod") is False


def test_label_matches_false_when_unlabeled(unlabeled_snapshot):
    assert label_matches(unlabeled_snapshot, "anything") is False
