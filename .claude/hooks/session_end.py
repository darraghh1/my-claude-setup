#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""SessionEnd hook — logs session end and cleans up MCP server processes.

Runs when a Claude Code session ends. Records the end event and kills
MCP server processes owned by THIS session only. Other sessions' MCP
servers are untouched.

MCP server patterns are discovered dynamically from config files
(~/.claude.json, settings.json, settings.local.json, .mcp.json) rather
than hardcoded, so cleanup works for any project's MCP configuration.

Uses process-tree ancestry to identify ownership: only kills MCP
processes that are descendants of the current Claude process.

Notification is handled by stop.py to avoid double-dinging.
"""

import json
import sys
from datetime import datetime

from utils.constants import LOG_DIR
from utils.mcp_cleanup import kill_session_mcp


def log_session_end(input_data, cleanup_results):
    """Log session end event with cleanup info."""
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

    if cleanup_results:
        log_entry["mcp_cleanup"] = {
            pattern: count for pattern, count in cleanup_results
        }

    log_data.append(log_entry)

    # Keep log bounded — last 100 entries
    if len(log_data) > 100:
        log_data = log_data[-100:]

    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, Exception):
        input_data = {}

    cleanup_results = kill_session_mcp()
    log_session_end(input_data, cleanup_results)
    sys.exit(0)


if __name__ == "__main__":
    main()
