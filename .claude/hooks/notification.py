#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Notification hook — plays attention sound when Claude needs user input.

Filters to only fire on actionable events where the user needs to
respond: permission prompts (approve/deny destructive commands) and
elicitation dialogs (AskUserQuestion choices).

Ignores idle_prompt, auth_success, and other notification types
that don't require immediate user attention.
"""

import json
import sys

from utils.notify import notify

# Only play sounds for events that require user action
ACTIONABLE_TYPES = frozenset({
    "permission_prompt",   # destructive command approval
    "elicitation_dialog",  # AskUserQuestion choices
})


def main():
    try:
        input_data = json.loads(sys.stdin.read())
        event_type = input_data.get("type", "")

        if event_type in ACTIONABLE_TYPES:
            notify("attention")
    except (json.JSONDecodeError, Exception):
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
