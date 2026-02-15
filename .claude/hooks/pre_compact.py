#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
PreCompact hook — logs compaction events and optionally backs
up the transcript before context is compressed.

Flags:
  --backup   Create transcript backup before compaction
  --verbose  Print status messages
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime

from utils.constants import LOG_DIR


def log_pre_compact(input_data, custom_instructions):
    """Log pre-compact event."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "pre_compact.json"

    if log_file.exists():
        with open(log_file, "r") as f:
            try:
                log_data = json.load(f)
            except (json.JSONDecodeError, ValueError):
                log_data = []
    else:
        log_data = []

    log_entry = {
        "session_id": input_data.get("session_id", "unknown"),
        "hook_event_name": input_data.get(
            "hook_event_name", "PreCompact"
        ),
        "trigger": input_data.get("trigger", "unknown"),
        "custom_instructions": custom_instructions,
    }
    log_data.append(log_entry)

    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)


def backup_transcript(transcript_path, trigger, custom_instructions=""):
    """Create a backup of the transcript before compaction."""
    try:
        if not os.path.exists(transcript_path):
            return None

        backup_dir = LOG_DIR / "transcript_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = os.path.basename(transcript_path).rsplit(".", 1)[0]

        suffix = ""
        if custom_instructions:
            sanitized = re.sub(
                r"[^a-zA-Z0-9]", "_", custom_instructions[:30]
            ).strip("_")
            if sanitized:
                suffix = f"_{sanitized}"

        backup_name = (
            f"{session_name}_pre_compact_{trigger}{suffix}_{timestamp}.jsonl"
        )
        backup_path = backup_dir / backup_name

        shutil.copy2(transcript_path, backup_path)
        return str(backup_path)

    except Exception:
        return None


def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--backup",
            action="store_true",
            help="Create backup of transcript before compaction",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Print verbose output",
        )
        args = parser.parse_args()

        input_data = json.loads(sys.stdin.read())

        session_id = input_data.get("session_id", "unknown")
        transcript_path = input_data.get("transcript_path", "")
        trigger = input_data.get("trigger", "unknown")
        custom_instructions = input_data.get(
            "custom_instructions", ""
        )

        log_pre_compact(input_data, custom_instructions)

        backup_path = None
        if args.backup and transcript_path:
            backup_path = backup_transcript(
                transcript_path, trigger, custom_instructions
            )

        if args.verbose:
            if trigger == "manual":
                message = (
                    f"Preparing for manual compaction "
                    f"(session: {session_id[:8]}...)"
                )
                if custom_instructions:
                    message += (
                        f"\nCustom instructions: "
                        f"{custom_instructions[:100]}..."
                    )
            else:
                message = (
                    f"Auto-compaction triggered "
                    f"(session: {session_id[:8]}...)"
                )

            if backup_path:
                message += f"\nTranscript backed up to: {backup_path}"

            print(message)

        sys.exit(0)

    except (json.JSONDecodeError, Exception):
        sys.exit(0)


if __name__ == "__main__":
    main()
