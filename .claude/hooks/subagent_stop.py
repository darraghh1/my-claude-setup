#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""SubagentStop hook — logs sub-agent completion with agent type and transcript path.

Runs when a sub-agent finishes. Logs the event for debugging and session tracking.
"""

import json
import sys
from utils.constants import ensure_session_log_dir


def main():
    try:
        input_data = json.load(sys.stdin)

        # If stop_hook_active, exit to prevent infinite loops
        if input_data.get("stop_hook_active", False):
            sys.exit(0)

        session_id = input_data.get("session_id", "unknown")
        log_dir = ensure_session_log_dir(session_id)
        log_path = log_dir / "subagent_stop.json"

        # Read existing log data or initialize empty list
        if log_path.exists():
            with open(log_path, "r") as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []

        log_entry = {
            "session_id": session_id,
            "hook_event_name": input_data.get(
                "hook_event_name", "SubagentStop"
            ),
            "stop_hook_active": False,
            "agent_id": input_data.get("agent_id", ""),
            "agent_type": input_data.get("agent_type", ""),
            "agent_transcript_path": input_data.get(
                "agent_transcript_path", ""
            ),
        }
        log_data.append(log_entry)

        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)

        sys.exit(0)

    except (json.JSONDecodeError, Exception):
        sys.exit(0)


if __name__ == "__main__":
    main()
