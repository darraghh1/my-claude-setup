#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
SessionStart hook — injects git context and logs session start.

Provides Claude with immediate situational awareness by injecting
the current git branch and dirty file count. This saves a round-trip
that would otherwise be spent on `git status` at the start of every
conversation.
"""

import json
import subprocess
import sys

from utils.constants import LOG_DIR


def get_git_context() -> str | None:
    """
    Get current git branch and working tree status.

    Returns a compact context string, or None if git isn't available
    or we're not in a repo.
    """
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if branch.returncode != 0:
            return None

        branch_name = branch.stdout.strip()

        # Count dirty files (staged + unstaged + untracked)
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=5,
        )
        dirty_files = len([
            line for line in status.stdout.strip().split("\n")
            if line.strip()
        ]) if status.stdout.strip() else 0

        parts = [f"Git branch: {branch_name}"]
        if dirty_files:
            parts.append(
                f"{dirty_files} uncommitted file(s) in working tree"
            )

        return " | ".join(parts)

    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def log_session_start(input_data):
    """Log session start event."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "session_start.json"

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
            "hook_event_name", "SessionStart"
        ),
        "source": input_data.get("source", "unknown"),
        "model": input_data.get("model", ""),
        "agent_type": input_data.get("agent_type", ""),
    }
    log_data.append(log_entry)

    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)


def main():
    try:
        input_data = json.loads(sys.stdin.read())
        log_session_start(input_data)

        # --- Context injection ---
        git_context = get_git_context()
        if git_context:
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": git_context,
                }
            }
            print(json.dumps(output))

    except (json.JSONDecodeError, Exception):
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
