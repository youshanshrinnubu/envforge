"""Integration helper: wire history CLI into the main envforge parser.

This module is imported by cli.py to register the 'history' subcommand
and also provides a convenience hook to auto-record snapshots on capture.
"""

from pathlib import Path
from typing import Optional

from envforge.snapshot import EnvSnapshot
from envforge.history import record_snapshot
from envforge.cli_history import add_history_subparser, cmd_history


def register_history(subparsers) -> None:
    """Register the history subcommand on the main CLI subparsers."""
    add_history_subparser(subparsers)


def auto_record(
    snapshot: EnvSnapshot,
    label: Optional[str] = None,
    history_dir: Optional[Path] = None,
    silent: bool = False,
) -> Optional[Path]:
    """Record a snapshot to history after capture, with optional feedback.

    Args:
        snapshot: The captured EnvSnapshot to persist.
        label: Optional human-readable label for the entry.
        history_dir: Override default history directory.
        silent: If True, suppress printed confirmation.

    Returns:
        Path to the written history file, or None on error.
    """
    try:
        path = record_snapshot(snapshot, label=label, history_dir=history_dir)
        if not silent:
            print(f"[history] Snapshot recorded: {path.name}")
        return path
    except OSError as exc:
        if not silent:
            print(f"[history] Warning: could not record snapshot: {exc}")
        return None


def history_entry_count(history_dir: Optional[Path] = None) -> int:
    """Return the number of history entries currently stored."""
    from envforge.history import list_history
    return len(list_history(history_dir=history_dir))


def purge_old_entries(
    keep: int = 20,
    history_dir: Optional[Path] = None,
    silent: bool = False,
) -> int:
    """Delete oldest history entries beyond the `keep` limit.

    Args:
        keep: Maximum number of entries to retain (newest kept).
        history_dir: Override default history directory.
        silent: Suppress printed output.

    Returns:
        Number of entries deleted.
    """
    from envforge.history import list_history, delete_history_entry

    entries = list_history(history_dir=history_dir)  # newest first
    to_delete = entries[keep:]
    for entry in to_delete:
        try:
            delete_history_entry(entry["filename"], history_dir=history_dir)
            if not silent:
                print(f"[history] Purged: {entry['filename']}")
        except OSError:
            pass
    return len(to_delete)
