"""Tests for envforge.annotator."""

from __future__ import annotations

import pytest

from envforge.annotator import (
    Annotation,
    add_annotation,
    clear_annotations,
    get_annotations,
    remove_annotation,
)
from envforge.snapshot import EnvSnapshot


@pytest.fixture
def sample_snapshot() -> EnvSnapshot:
    return EnvSnapshot(
        label="test",
        env_vars={"HOME": "/home/user"},
        python_version="3.11.0",
        node_version=None,
        pip_packages={"requests": "2.31.0"},
        extra={},
    )


def test_get_annotations_empty(sample_snapshot):
    assert get_annotations(sample_snapshot) == []


def test_add_annotation_returns_annotation(sample_snapshot):
    note = add_annotation(sample_snapshot, "initial setup", author="alice")
    assert isinstance(note, Annotation)
    assert note.text == "initial setup"
    assert note.author == "alice"


def test_add_annotation_stored_in_snapshot(sample_snapshot):
    add_annotation(sample_snapshot, "first note")
    notes = get_annotations(sample_snapshot)
    assert len(notes) == 1
    assert notes[0].text == "first note"


def test_add_multiple_annotations(sample_snapshot):
    add_annotation(sample_snapshot, "note A")
    add_annotation(sample_snapshot, "note B")
    notes = get_annotations(sample_snapshot)
    assert len(notes) == 2
    assert notes[1].text == "note B"


def test_remove_annotation_valid_index(sample_snapshot):
    add_annotation(sample_snapshot, "to remove")
    ok = remove_annotation(sample_snapshot, 0)
    assert ok is True
    assert get_annotations(sample_snapshot) == []


def test_remove_annotation_invalid_index(sample_snapshot):
    ok = remove_annotation(sample_snapshot, 5)
    assert ok is False


def test_remove_annotation_leaves_others(sample_snapshot):
    add_annotation(sample_snapshot, "keep")
    add_annotation(sample_snapshot, "delete")
    remove_annotation(sample_snapshot, 1)
    notes = get_annotations(sample_snapshot)
    assert len(notes) == 1
    assert notes[0].text == "keep"


def test_clear_annotations_returns_count(sample_snapshot):
    add_annotation(sample_snapshot, "a")
    add_annotation(sample_snapshot, "b")
    count = clear_annotations(sample_snapshot)
    assert count == 2


def test_clear_annotations_empties_list(sample_snapshot):
    add_annotation(sample_snapshot, "x")
    clear_annotations(sample_snapshot)
    assert get_annotations(sample_snapshot) == []


def test_annotation_roundtrip():
    note = Annotation(text="hello", author="bob", created_at="2024-01-01T00:00:00+00:00")
    restored = Annotation.from_dict(note.to_dict())
    assert restored.text == note.text
    assert restored.author == note.author
    assert restored.created_at == note.created_at


def test_add_annotation_initialises_extra_if_none(sample_snapshot):
    sample_snapshot.extra = None
    add_annotation(sample_snapshot, "init")
    assert sample_snapshot.extra is not None
    assert len(get_annotations(sample_snapshot)) == 1
