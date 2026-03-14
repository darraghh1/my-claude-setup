#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""SessionEnd hook — logs session end and cleans up orphaned MCP processes.

Runs when a Claude Code session ends. Records the end event and kills
MCP server processes that are known to leak (e.g., draw.io spawns headless
browsers that survive session exit and accumulate until OOM).

Notification is handled by stop.py to avoid double-dinging.
"""

import json
import subprocess
import sys
from datetime import datetime

from utils.constants import LOG_DIR

# MCP processes known to leak after session exit.
# Each entry is a pattern matched against the full command line (pkill -f).
# Only add processes here that are confirmed to orphan — don't blanket-kill
# lightweight stdio MCP servers that clean up properly on stdin close.
LEAKY_MCP_PATTERNS = [
    "next-ai-drawio-mcp",  # Spawns HTTP server + opens browser per session
    "playwright-mcp",      # Spawns headless Chromium that survives session exit
]


def cleanup_orphaned_mcp():
    """Kill MCP server processes that are known to outlive their sessions.

    Returns a list of (pattern, kill_count) tuples for logging.
    """
    results = []
    for pattern in LEAKY_MCP_PATTERNS:
        try:
            # Count matching processes first
            count_result = subprocess.run(
                ["pgrep", "-fc", pattern],
                capture_output=True, text=True, timeout=5,
            )
            count = int(count_result.stdout.strip()) if count_result.returncode == 0 else 0

            if count > 0:
                # SIGTERM first for graceful shutdown
                subprocess.run(
                    ["pkill", "-f", pattern],
                    capture_output=True, timeout=5,
                )
                results.append((pattern, count))
        except (subprocess.TimeoutExpired, ValueError, OSError):
            pass
    return results


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

    cleanup_results = cleanup_orphaned_mcp()
    log_session_end(input_data, cleanup_results)
    sys.exit(0)


if __name__ == "__main__":
    main()
