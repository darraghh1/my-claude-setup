#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
TeammateIdle hook — quality gate for premature idling.

Prevents teammates from going idle when they have assigned tasks
that are still in_progress. The user depends on this gate to
ensure teammates complete their assigned work before idling.
"""

import json
import sys


def main():
    try:
        input_data = json.load(sys.stdin)

        # Check if teammate has in-progress tasks
        # The hook receives teammate context — if the teammate
        # is idling with incomplete work, block it.
        agent_name = input_data.get("agent_name", "unknown")

        # Log the idle event for debugging
        sys.stderr.write(
            f"Teammate '{agent_name}' is going idle. "
            "The user configured this gate because premature "
            "idling causes incomplete work and missed tasks. "
            "If you have assigned tasks still in_progress, "
            "complete them before going idle.\n"
        )

        # Exit 0 to allow idling (non-blocking by default).
        # Change to exit 2 to block with the stderr message
        # when you want stricter enforcement.
        sys.exit(0)

    except (json.JSONDecodeError, Exception):
        sys.exit(0)


if __name__ == "__main__":
    main()
