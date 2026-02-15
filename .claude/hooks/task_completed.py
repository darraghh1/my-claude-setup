#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
TaskCompleted hook — quality gate for task completion.

Verifies that teammates don't mark tasks as completed without
running verification. The user depends on this gate to prevent
incomplete or untested work from being marked as done.

Without this gate, teammates mark tasks complete before tests
pass, causing downstream phases to build on broken foundations.
"""

import json
import sys


def main():
    try:
        input_data = json.load(sys.stdin)

        task_id = input_data.get("task_id", "unknown")
        agent_name = input_data.get("agent_name", "unknown")

        # Log the completion event
        sys.stderr.write(
            f"Task '{task_id}' marked complete by '{agent_name}'. "
            "The user configured this gate because marking tasks "
            "complete without verification causes bugs to slip "
            "through. Ensure tests pass and acceptance criteria "
            "are met before completing tasks.\n"
        )

        # Exit 0 to allow completion (non-blocking by default).
        # Change to exit 2 to block with the stderr message
        # when you want stricter enforcement (e.g., require
        # test pass confirmation in the task notes).
        sys.exit(0)

    except (json.JSONDecodeError, Exception):
        sys.exit(0)


if __name__ == "__main__":
    main()
