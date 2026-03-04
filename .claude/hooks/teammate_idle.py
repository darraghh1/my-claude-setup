#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
TeammateIdle hook — deduped idle notification.

Teammates going idle is NORMAL between turns. This hook warns once
per agent per 5-minute window, then allows all subsequent idles.
Never blocks (exit 0) — blocking idle transitions causes infinite
loops where the teammate can never stop.

Previous version unconditionally blocked (exit 2) every idle event,
causing 15-20 hours of wasted compute across sessions.
"""

import json
import sys
import time
from pathlib import Path

SEEN_FILE = Path("/tmp/claude-hook-idle-seen.json")
TTL_SECONDS = 300  # 5 minutes


def load_seen() -> dict:
    """Load seen-set, pruning expired entries."""
    try:
        data = json.loads(SEEN_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        data = {"agents": {}}

    now = time.time()

    # Prune expired entries
    agents = {
        k: v for k, v in data.get("agents", {}).items()
        if now - v < TTL_SECONDS
    }

    return {"agents": agents}


def save_seen(data: dict) -> None:
    """Save seen-set atomically."""
    try:
        SEEN_FILE.write_text(json.dumps(data))
    except OSError:
        pass


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        sys.exit(0)

    agent_name = input_data.get("agent_name", "unknown")
    now = time.time()
    seen = load_seen()

    # Already notified about this agent recently — allow silently
    if agent_name in seen["agents"]:
        sys.exit(0)

    # First idle for this agent in the window — log info, allow
    seen["agents"][agent_name] = now
    save_seen(seen)

    sys.stderr.write(
        f"[hook] Teammate '{agent_name}' going idle. "
        "If they have in_progress tasks, send them a message "
        "to continue work.\n"
    )
    # Exit 0 — NEVER block idle transitions. Blocking causes loops.
    sys.exit(0)


if __name__ == "__main__":
    main()
