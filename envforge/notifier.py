"""Notification system for envforge snapshot events."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

NOTIFY_CONFIG_ENV = "ENVFORGE_NOTIFY_CONFIG"
DEFAULT_CONFIG_PATH = Path.home() / ".envforge" / "notify.json"

EVENT_CAPTURE = "capture"
EVENT_REPRODUCE = "reproduce"
EVENT_VALIDATE_FAIL = "validate_fail"
EVENT_DRIFT_DETECTED = "drift_detected"

SUPPORTED_EVENTS = {EVENT_CAPTURE, EVENT_REPRODUCE, EVENT_VALIDATE_FAIL, EVENT_DRIFT_DETECTED}


@dataclass
class NotifyConfig:
    enabled: bool = True
    events: List[str] = field(default_factory=lambda: list(SUPPORTED_EVENTS))
    handlers: List[str] = field(default_factory=list)  # e.g. ["print", "log"]
    log_path: Optional[str] = None


def get_config_path() -> Path:
    custom = os.environ.get(NOTIFY_CONFIG_ENV)
    return Path(custom) if custom else DEFAULT_CONFIG_PATH


def load_config(config_path: Optional[Path] = None) -> NotifyConfig:
    path = config_path or get_config_path()
    if not path.exists():
        return NotifyConfig()
    with open(path, "r") as f:
        data = json.load(f)
    return NotifyConfig(
        enabled=data.get("enabled", True),
        events=data.get("events", list(SUPPORTED_EVENTS)),
        handlers=data.get("handlers", []),
        log_path=data.get("log_path"),
    )


def save_config(config: NotifyConfig, config_path: Optional[Path] = None) -> Path:
    path = config_path or get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(
            {
                "enabled": config.enabled,
                "events": config.events,
                "handlers": config.handlers,
                "log_path": config.log_path,
            },
            f,
            indent=2,
        )
    return path


def notify(event: str, message: str, config: Optional[NotifyConfig] = None) -> None:
    """Fire a notification for the given event."""
    cfg = config or load_config()
    if not cfg.enabled or event not in cfg.events:
        return

    for handler in cfg.handlers:
        if handler == "print":
            print(f"[envforge:{event}] {message}")
        elif handler == "log" and cfg.log_path:
            _log_to_file(cfg.log_path, event, message)


def _log_to_file(log_path: str, event: str, message: str) -> None:
    import datetime
    ts = datetime.datetime.utcnow().isoformat()
    with open(log_path, "a") as f:
        f.write(f"{ts} [{event}] {message}\n")
