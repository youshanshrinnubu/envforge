"""Tests for envforge.notifier module."""

import json
from pathlib import Path

import pytest

from envforge.notifier import (
    NotifyConfig,
    EVENT_CAPTURE,
    EVENT_DRIFT_DETECTED,
    EVENT_REPRODUCE,
    EVENT_VALIDATE_FAIL,
    SUPPORTED_EVENTS,
    load_config,
    notify,
    save_config,
)


@pytest.fixture
def cfg_path(tmp_path):
    return tmp_path / "notify.json"


def test_default_config_has_all_events():
    cfg = NotifyConfig()
    assert set(cfg.events) == SUPPORTED_EVENTS


def test_default_config_enabled():
    cfg = NotifyConfig()
    assert cfg.enabled is True


def test_save_and_load_config(cfg_path):
    cfg = NotifyConfig(enabled=True, events=[EVENT_CAPTURE], handlers=["print"], log_path="/tmp/ef.log")
    save_config(cfg, cfg_path)
    loaded = load_config(cfg_path)
    assert loaded.enabled is True
    assert loaded.events == [EVENT_CAPTURE]
    assert loaded.handlers == ["print"]
    assert loaded.log_path == "/tmp/ef.log"


def test_load_config_missing_file_returns_defaults(tmp_path):
    cfg = load_config(tmp_path / "nonexistent.json")
    assert cfg.enabled is True
    assert set(cfg.events) == SUPPORTED_EVENTS


def test_save_config_creates_parent_dirs(tmp_path):
    nested = tmp_path / "a" / "b" / "notify.json"
    save_config(NotifyConfig(), nested)
    assert nested.exists()


def test_notify_print_handler(capsys):
    cfg = NotifyConfig(enabled=True, events=[EVENT_CAPTURE], handlers=["print"])
    notify(EVENT_CAPTURE, "snapshot taken", config=cfg)
    captured = capsys.readouterr()
    assert "snapshot taken" in captured.out
    assert EVENT_CAPTURE in captured.out


def test_notify_skips_disabled_event(capsys):
    cfg = NotifyConfig(enabled=True, events=[EVENT_REPRODUCE], handlers=["print"])
    notify(EVENT_CAPTURE, "should not appear", config=cfg)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_notify_skips_when_disabled(capsys):
    cfg = NotifyConfig(enabled=False, events=list(SUPPORTED_EVENTS), handlers=["print"])
    notify(EVENT_DRIFT_DETECTED, "drift!", config=cfg)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_notify_log_handler(tmp_path):
    log_file = tmp_path / "envforge.log"
    cfg = NotifyConfig(
        enabled=True,
        events=[EVENT_VALIDATE_FAIL],
        handlers=["log"],
        log_path=str(log_file),
    )
    notify(EVENT_VALIDATE_FAIL, "validation failed", config=cfg)
    content = log_file.read_text()
    assert "validation failed" in content
    assert EVENT_VALIDATE_FAIL in content


def test_notify_log_appends_multiple(tmp_path):
    log_file = tmp_path / "envforge.log"
    cfg = NotifyConfig(
        enabled=True,
        events=list(SUPPORTED_EVENTS),
        handlers=["log"],
        log_path=str(log_file),
    )
    notify(EVENT_CAPTURE, "first", config=cfg)
    notify(EVENT_REPRODUCE, "second", config=cfg)
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 2
