"""
Log cleanup utility — rotates JSONL log and prunes old session directories.

Called from session_start.py to run automatically at session start.
Designed to be fast and fail-safe — never blocks session startup.
"""

import os
import shutil
import time
from datetime import datetime
from pathlib import Path

from utils.constants import JSONL_LOG_DIR, LOG_DIR

# Rotate hooks.jsonl when it exceeds this size
JSONL_MAX_BYTES = 5 * 1024 * 1024  # 5 MB

# Delete session log directories older than this
SESSION_MAX_AGE_DAYS = 30


def rotate_jsonl() -> str | None:
    """Rotate hooks.jsonl if it exceeds the size threshold.

    Renames current file to hooks.{YYYYMMDD}.jsonl and lets the
    next log_jsonl() call create a fresh one.

    Returns the rotated filename if rotation occurred, None otherwise.
    """
    log_path = JSONL_LOG_DIR / "hooks.jsonl"

    if not log_path.exists():
        return None

    try:
        size = log_path.stat().st_size
    except OSError:
        return None

    if size < JSONL_MAX_BYTES:
        return None

    date_stamp = datetime.now().strftime("%Y%m%d")
    rotated_name = f"hooks.{date_stamp}.jsonl"
    rotated_path = JSONL_LOG_DIR / rotated_name

    # Handle multiple rotations on the same day
    counter = 1
    while rotated_path.exists():
        rotated_name = f"hooks.{date_stamp}.{counter}.jsonl"
        rotated_path = JSONL_LOG_DIR / rotated_name
        counter += 1

    try:
        log_path.rename(rotated_path)
        return rotated_name
    except OSError:
        return None


def prune_session_logs() -> int:
    """Delete session log directories older than SESSION_MAX_AGE_DAYS.

    Returns the number of directories removed.
    """
    if not LOG_DIR.exists():
        return 0

    cutoff = time.time() - (SESSION_MAX_AGE_DAYS * 86400)
    removed = 0

    try:
        for entry in LOG_DIR.iterdir():
            if not entry.is_dir():
                continue
            # Skip non-session directories (e.g., transcript_backups)
            # Session dirs are UUIDs: 8-4-4-4-12 hex characters
            name = entry.name
            if len(name) != 36 or name.count("-") != 4:
                continue
            try:
                mtime = entry.stat().st_mtime
                if mtime < cutoff:
                    shutil.rmtree(entry)
                    removed += 1
            except OSError:
                continue
    except OSError:
        pass

    return removed


def cleanup() -> dict:
    """Run all cleanup tasks. Returns a summary dict."""
    rotated = rotate_jsonl()
    pruned = prune_session_logs()

    return {
        "jsonl_rotated": rotated,
        "sessions_pruned": pruned,
    }
