#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Stop hook — transcript export and notification.

Exports JSONL transcript to chat.json and plays completion sound.
"""

import argparse
import json
import sys
from pathlib import Path
from utils.constants import ensure_session_log_dir
from utils.notify import notify


def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--chat", action="store_true",
            help="Copy transcript to chat.json"
        )
        args = parser.parse_args()

        input_data = json.load(sys.stdin)

        # If stop_hook_active, exit to prevent infinite loops
        if input_data.get("stop_hook_active", False):
            sys.exit(0)

        session_id = input_data.get("session_id", "unknown")
        log_dir = ensure_session_log_dir(session_id)
        log_path = log_dir / "stop.json"

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
                "hook_event_name", "Stop"
            ),
            "stop_hook_active": False,
        }
        log_data.append(log_entry)

        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)

        # Convert JSONL transcript to chat.json
        if args.chat and "transcript_path" in input_data:
            transcript = Path(input_data["transcript_path"])
            if transcript.exists():
                chat_data = []
                try:
                    with open(transcript, "r") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    chat_data.append(
                                        json.loads(line)
                                    )
                                except json.JSONDecodeError:
                                    pass

                    chat_file = log_dir / "chat.json"
                    with open(chat_file, "w") as f:
                        json.dump(chat_data, f, indent=2)
                except Exception:
                    pass

        notify("complete")
        sys.exit(0)

    except (json.JSONDecodeError, Exception):
        sys.exit(0)


if __name__ == "__main__":
    main()
