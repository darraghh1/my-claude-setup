#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
UserPromptSubmit hook — logs prompts and stores last prompt
for status line display.

Flags:
  --store-last-prompt  Store prompt in session file for status line
"""

import argparse
import json
import sys
from pathlib import Path

from utils.constants import LOG_DIR

# Session data lives alongside logs under .claude/data/
_SESSIONS_DIR = LOG_DIR.parent / "sessions"


def log_user_prompt(input_data):
    """Log user prompt metadata to logs directory."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "user_prompt_submit.json"

    if log_file.exists():
        with open(log_file, "r") as f:
            try:
                log_data = json.load(f)
            except (json.JSONDecodeError, ValueError):
                log_data = []
    else:
        log_data = []

    prompt = input_data.get("prompt", "")
    log_entry = {
        "session_id": input_data.get("session_id", "unknown"),
        "hook_event_name": input_data.get(
            "hook_event_name", "UserPromptSubmit"
        ),
        "prompt_length": len(prompt),
        "prompt_preview": prompt[:120] if prompt else "",
    }
    log_data.append(log_entry)

    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)


def store_last_prompt(session_id, prompt):
    """Store prompt in session file for status line display."""
    _SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    session_file = _SESSIONS_DIR / f"{session_id}.json"

    if session_file.exists():
        try:
            with open(session_file, "r") as f:
                session_data = json.load(f)
        except (json.JSONDecodeError, ValueError):
            session_data = {
                "session_id": session_id,
                "prompts": [],
            }
    else:
        session_data = {
            "session_id": session_id,
            "prompts": [],
        }

    session_data["prompts"].append(prompt)

    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2)


def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--store-last-prompt",
            action="store_true",
            help="Store last prompt for status line",
        )
        args = parser.parse_args()

        input_data = json.loads(sys.stdin.read())

        log_user_prompt(input_data)

        if args.store_last_prompt:
            session_id = input_data.get("session_id", "unknown")
            prompt = input_data.get("prompt", "")
            store_last_prompt(session_id, prompt)

        sys.exit(0)

    except (json.JSONDecodeError, Exception):
        sys.exit(0)


if __name__ == "__main__":
    main()
