"""Tests for envforge.scheduler."""

import time
import pytest

from envforge.scheduler import (
    add_schedule,
    remove_schedule,
    list_schedules,
    due_schedules,
    mark_ran,
    ScheduleEntry,
)


@pytest.fixture
def sched_file(tmp_path):
    return str(tmp_path / "schedule.json")


def test_add_schedule_creates_entry(sched_file):
    entry = add_schedule("dev", 3600, "/tmp/snaps", path=sched_file)
    assert isinstance(entry, ScheduleEntry)
    assert entry.name == "dev"
    assert entry.interval_seconds == 3600


def test_add_schedule_persists(sched_file):
    add_schedule("dev", 3600, "/tmp/snaps", path=sched_file)
    entries = list_schedules(path=sched_file)
    assert len(entries) == 1
    assert entries[0].name == "dev"


def test_add_schedule_duplicate_raises(sched_file):
    add_schedule("dev", 3600, "/tmp/snaps", path=sched_file)
    with pytest.raises(ValueError, match="already exists"):
        add_schedule("dev", 7200, "/tmp/other", path=sched_file)


def test_add_schedule_with_tags(sched_file):
    entry = add_schedule("ci", 600, "/out", tags=["ci", "auto"], path=sched_file)
    assert "ci" in entry.tags
    assert "auto" in entry.tags


def test_remove_schedule_existing(sched_file):
    add_schedule("dev", 3600, "/tmp", path=sched_file)
    result = remove_schedule("dev", path=sched_file)
    assert result is True
    assert list_schedules(path=sched_file) == []


def test_remove_schedule_nonexistent(sched_file):
    result = remove_schedule("ghost", path=sched_file)
    assert result is False


def test_list_schedules_empty(sched_file):
    assert list_schedules(path=sched_file) == []


def test_list_schedules_multiple(sched_file):
    add_schedule("a", 60, "/a", path=sched_file)
    add_schedule("b", 120, "/b", path=sched_file)
    entries = list_schedules(path=sched_file)
    assert len(entries) == 2
    names = {e.name for e in entries}
    assert names == {"a", "b"}


def test_due_schedules_never_run(sched_file):
    add_schedule("fresh", 9999, "/out", path=sched_file)
    due = due_schedules(path=sched_file)
    assert any(e.name == "fresh" for e in due)


def test_due_schedules_after_interval(sched_file):
    add_schedule("old", 1, "/out", path=sched_file)
    mark_ran("old", path=sched_file)
    time.sleep(1.1)
    due = due_schedules(path=sched_file)
    assert any(e.name == "old" for e in due)


def test_not_due_before_interval(sched_file):
    add_schedule("recent", 9999, "/out", path=sched_file)
    mark_ran("recent", path=sched_file)
    due = due_schedules(path=sched_file)
    assert not any(e.name == "recent" for e in due)


def test_mark_ran_updates_last_run(sched_file):
    add_schedule("snap", 60, "/out", path=sched_file)
    before = time.time()
    mark_ran("snap", path=sched_file)
    entries = list_schedules(path=sched_file)
    assert entries[0].last_run is not None
    assert entries[0].last_run >= before
