#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
TaskCompleted hook — agent-aware, deduped verification reminder.

Shows a role-specific verification reminder the FIRST time a task ID
is completed, then allows subsequent attempts for the same task.

Uses agent_type from hook event data (new field for subagents) to
provide targeted reminders:
  - builder:     "Did you run tests, typecheck, and commit?"
  - validator:   "Did you write the review file and determine verdict?"
  - auditor:     "Did you write the audit report?"
  - planner:     "Did you validate the phase (no placeholders, TDD ordering)?"
  - orchestrator: Generic verification reminder

Dedup state stored in /tmp/claude-hook-seen.json with 5-minute TTL.
Rate-limited to max 3 blocks per minute to break loops.
"""

import json
import sys
import time
from pathlib import Path

SEEN_FILE = Path("/tmp/claude-hook-seen.json")
MARKER_FILE = Path("/tmp/claude-tasks-active.marker")
TTL_SECONDS = 300  # 5 minutes
MAX_BLOCKS_PER_MINUTE = 3

ROLE_REMINDERS = {
    "builder": (
        "Builder verification: ensure tests pass (pnpm test), "
        "typecheck is clean (pnpm run typecheck), and all changes are "
        "committed (git add -A && git commit) before reporting completion."
    ),
    "validator": (
        "Validator verification: ensure code review file is written, "
        "verdict is determined (PASS/FAIL), and verification ran "
        "(if auto-fixes were applied) before reporting to team-lead."
    ),
    "auditor": (
        "Auditor verification: ensure audit report is written to "
        "reviews/implementation/plan-audit.md and findings "
        "are severity-rated before reporting to team-lead."
    ),
    "planner": (
        "Planner verification: ensure phase file passes validators "
        "(no placeholders, TDD ordering correct, all template sections "
        "present) before marking complete."
    ),
}

DEFAULT_REMINDER = (
    "Verification reminder: ensure tests pass and acceptance criteria "
    "are met before marking complete."
)


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


def get_reminder(agent_type: str) -> str:
    """Get role-specific reminder message."""
    return ROLE_REMINDERS.get(agent_type, DEFAULT_REMINDER)


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        sys.exit(0)

    task_id = input_data.get("task_id", "unknown")
    agent_type = input_data.get("agent_type", "")
    agent_id = input_data.get("agent_id", "")
    now = time.time()
    seen = load_seen()

    # Write marker file so stop_task_check.py knows tasks were used
    try:
        MARKER_FILE.write_text(str(now))
    except OSError:
        pass

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

    reminder = get_reminder(agent_type)
    agent_label = f" ({agent_type} '{agent_id}')" if agent_type else ""

    sys.stderr.write(
        f"[hook] Task '{task_id}'{agent_label} — {reminder} "
        "Re-attempt will be allowed.\n"
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
