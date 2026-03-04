#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
TaskCompleted hook — deduped verification reminder.

Shows a verification reminder the FIRST time a task ID is completed,
then allows subsequent attempts for the same task. This prevents
infinite loops where the hook blocks → Claude reacts → retries →
hook blocks again.

Dedup state stored in /tmp/claude-hook-seen.json with 5-minute TTL.
Rate-limited to max 3 blocks per minute to break loops.
"""

import json
import sys
import time
from pathlib import Path

SEEN_FILE = Path("/tmp/claude-hook-seen.json")
TTL_SECONDS = 300  # 5 minutes
MAX_BLOCKS_PER_MINUTE = 3


def load_seen() -> dict:
    """Load seen-set, pruning expired entries."""
    try:
        data = json.loads(SEEN_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        data = {"tasks": {}, "blocks": []}

    now = time.time()

    # Prune expired task entries
    tasks = {
        k: v for k, v in data.get("tasks", {}).items()
        if now - v < TTL_SECONDS
    }

    # Prune block timestamps older than 60 seconds
    blocks = [
        t for t in data.get("blocks", [])
        if now - t < 60
    ]

    return {"tasks": tasks, "blocks": blocks}


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

    task_id = input_data.get("task_id", "unknown")
    now = time.time()
    seen = load_seen()

    # Rate limit: if we've blocked 3+ times in the last minute,
    # allow everything to break potential loops
    if len(seen["blocks"]) >= MAX_BLOCKS_PER_MINUTE:
        sys.stderr.write(
            f"[hook] Rate limit hit — allowing task '{task_id}' completion "
            "(loop protection).\n"
        )
        sys.exit(0)

    # Dedup: if we've already reminded about this task, allow it
    if task_id in seen["tasks"]:
        sys.stderr.write(
            f"[hook] Task '{task_id}' already reminded — allowing completion.\n"
        )
        sys.exit(0)

    # First time seeing this task: record it, block with reminder
    seen["tasks"][task_id] = now
    seen["blocks"].append(now)
    save_seen(seen)

    sys.stderr.write(
        f"[hook] Task '{task_id}' — verification reminder: "
        "ensure tests pass and acceptance criteria are met "
        "before marking complete. Re-attempt will be allowed.\n"
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
