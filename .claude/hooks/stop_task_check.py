#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Stop hook — orphaned task reminder.

Checks if any tasks were used in this session (via /tmp marker file).
If so, outputs a systemMessage reminding the agent to close out tasks.

This catches the common pattern where agents create tasks but forget
to mark them completed before finishing — especially when the
TaskCompleted hook blocks the first attempt.

Uses a lightweight marker file approach: the task_completed.py hook
writes a marker when tasks are seen, and this hook checks for it.
"""

import json
import sys
from pathlib import Path

MARKER_FILE = Path("/tmp/claude-tasks-active.marker")


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        sys.exit(0)

    # Don't re-trigger on ourselves
    if input_data.get("stop_hook_active", False):
        sys.exit(0)

    # Only fire if tasks were used in this session
    if not MARKER_FILE.exists():
        sys.exit(0)

    # Clean up the marker
    try:
        MARKER_FILE.unlink()
    except OSError:
        pass

    # Output a systemMessage to remind about orphaned tasks
    result = {
        "outputToTerminal": False,
        "systemMessage": (
            "TASK CLEANUP: Before finishing, run TaskList to check for "
            "orphaned in_progress tasks. Mark them completed if the work "
            "is done. If the TaskCompleted hook blocks your first attempt, "
            "retry immediately — it allows the second attempt."
        )
    }
    print(json.dumps(result))
    sys.exit(0)


if __name__ == "__main__":
    main()
