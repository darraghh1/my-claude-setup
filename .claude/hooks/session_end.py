#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""SessionEnd hook — logs session end reason and plays completion sound.

Runs when a Claude Code session ends. Records the end event and notifies the user.
"""

import json
import sys
from datetime import datetime

from utils.constants import LOG_DIR
from utils.notify import notify


def log_session_end(input_data):
    """Log session end event."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "session_end.json"

    if log_file.exists():
        with open(log_file, "r") as f:
            try:
                log_data = json.load(f)
            except (json.JSONDecodeError, ValueError):
                log_data = []
    else:
        log_data = []

    log_entry = {
        "session_id": input_data.get(
            "session_id", "unknown"
        ),
        "hook_event_name": input_data.get(
            "hook_event_name", "SessionEnd"
        ),
        "reason": input_data.get("reason", "other"),
        "logged_at": datetime.now().isoformat(),
    }
    log_data.append(log_entry)

    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)


def main():
    try:
        input_data = json.loads(sys.stdin.read())
        log_session_end(input_data)
        notify("complete")
    except (json.JSONDecodeError, Exception):
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
