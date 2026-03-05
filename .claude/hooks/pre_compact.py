#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
PreCompact hook — injects agent-aware recovery context before compaction.

When context is about to be compacted, this hook:
1. Reads agent_id and agent_type from the hook event (new fields for subagents)
2. Injects additionalContext with recovery instructions so the agent
   knows who it is and how to resume after compaction
3. Optionally backs up the transcript

The additionalContext survives compaction — it's injected as a system message
that the compacted summary includes. This is the primary compact recovery
mechanism for team agents.

Flags:
  --backup   Create transcript backup before compaction
  --verbose  Print status messages to stderr
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime

from utils.constants import LOG_DIR, log_jsonl


ROLE_RECOVERY_HINTS = {
    "builder": (
        "You are a BUILDER agent. Your workflow skill is builder-workflow. "
        "Your tasks are prefixed with [Step]. "
        "Resume: TaskList → filter by owner (your name) → find in_progress → TaskGet → "
        "read metadata for phase/group/skill/parent_task_id → continue implementation. "
        "Do NOT restart the phase."
    ),
    "validator": (
        "You are a VALIDATOR agent. Your workflow skill is validator-workflow. "
        "Your tasks are prefixed with [Review]. "
        "Resume: TaskList → filter by owner (your name) → find in_progress → TaskGet → "
        "read metadata for phase/group/parent_task_id → continue validation. "
        "Do NOT restart the review."
    ),
    "auditor": (
        "You are an AUDITOR agent. Your workflow skill is auditor-workflow. "
        "Your tasks are prefixed with [Audit]. You are READ-ONLY — do not modify source code. "
        "Resume: TaskList → filter by owner (your name) → find in_progress → TaskGet → "
        "read metadata for group/parent_task_id → continue audit."
    ),
    "planner": (
        "You are a PLANNER agent. Your workflow skill is planner-workflow. "
        "Your tasks are prefixed with [Plan]. "
        "Resume: TaskList → filter by owner (your name) → find in_progress → TaskGet → "
        "read metadata for parent_task_id → continue planning. "
        "Do NOT restart the planning process."
    ),
}

DEFAULT_RECOVERY_HINT = (
    "Resume: TaskList → find in_progress or first pending → TaskGet → "
    "read description and metadata → continue from that task. "
    "The task list is your source of truth, not your memory."
)


def build_recovery_context(input_data: dict) -> str | None:
    """Build agent-aware recovery context for injection."""
    agent_id = input_data.get("agent_id", "")
    agent_type = input_data.get("agent_type", "")
    team_name = input_data.get("team_name", "")

    # Only inject recovery context if we have agent identity info
    if not agent_id and not agent_type:
        return None

    parts = ["CONTEXT COMPACTED — Recovery instructions:"]

    if agent_id:
        parts.append(f"Agent name: {agent_id}")
    if agent_type:
        parts.append(f"Agent type: {agent_type}")
    if team_name:
        parts.append(f"Team: {team_name}")

    # Add role-specific recovery hint
    hint = ROLE_RECOVERY_HINTS.get(agent_type, DEFAULT_RECOVERY_HINT)
    parts.append("")
    parts.append(hint)

    return "\n".join(parts)


def log_pre_compact(input_data: dict) -> None:
    """Log pre-compact event to JSONL."""
    session_id = input_data.get("session_id", "unknown")
    log_jsonl("PreCompact", session_id, {
        "trigger": input_data.get("trigger", "unknown"),
        "agent_id": input_data.get("agent_id", ""),
        "agent_type": input_data.get("agent_type", ""),
        "team_name": input_data.get("team_name", ""),
        "custom_instructions": input_data.get("custom_instructions", ""),
    })


def backup_transcript(transcript_path: str, trigger: str, custom_instructions: str = "") -> str | None:
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
            help="Print verbose output to stderr",
        )
        args = parser.parse_args()

        input_data = json.loads(sys.stdin.read())

        session_id = input_data.get("session_id", "unknown")
        transcript_path = input_data.get("transcript_path", "")
        trigger = input_data.get("trigger", "unknown")
        custom_instructions = input_data.get("custom_instructions", "")

        # Log the event
        log_pre_compact(input_data)

        # Backup transcript if requested
        backup_path = None
        if args.backup and transcript_path:
            backup_path = backup_transcript(
                transcript_path, trigger, custom_instructions
            )

        # Build and inject recovery context for agents
        recovery_context = build_recovery_context(input_data)

        if recovery_context:
            # Print to stdout — becomes additionalContext that survives compaction
            print(recovery_context)

        if args.verbose:
            agent_id = input_data.get("agent_id", "")
            agent_type = input_data.get("agent_type", "")

            if agent_id or agent_type:
                msg = (
                    f"[hook] PreCompact: agent={agent_id} type={agent_type} "
                    f"trigger={trigger} — recovery context injected"
                )
            elif trigger == "manual":
                msg = f"[hook] PreCompact: manual compaction (session: {session_id[:8]}...)"
            else:
                msg = f"[hook] PreCompact: auto-compaction (session: {session_id[:8]}...)"

            if backup_path:
                msg += f"\n  Transcript backed up to: {backup_path}"

            sys.stderr.write(msg + "\n")

        sys.exit(0)

    except (json.JSONDecodeError, Exception):
        sys.exit(0)


if __name__ == "__main__":
    main()
