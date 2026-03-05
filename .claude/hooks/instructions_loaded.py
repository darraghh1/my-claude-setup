#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
InstructionsLoaded hook — logs which rules/instructions loaded for each session.

Fires when Claude Code finishes loading instructions (rules, CLAUDE.md, etc.).
Logs the loaded instruction names and paths so you can verify what context
each agent actually receives (especially useful for debugging teammate rule loading).

Stdin JSON includes:
  - session_id: current session identifier
  - instructions: list of loaded instruction objects (name, path, type, etc.)
  - agent_id: (for subagents) agent name
  - agent_type: (for subagents) agent role
"""

import json
import sys

from utils.constants import log_jsonl


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, Exception):
        sys.exit(0)

    session_id = input_data.get("session_id", "unknown")
    agent_id = input_data.get("agent_id", "")
    agent_type = input_data.get("agent_type", "")
    instructions = input_data.get("instructions", [])

    # Extract instruction names/paths for logging
    instruction_summary = []
    for inst in instructions:
        if isinstance(inst, dict):
            name = inst.get("name", inst.get("path", "unknown"))
            inst_type = inst.get("type", "")
            instruction_summary.append(f"{name} ({inst_type})" if inst_type else name)
        elif isinstance(inst, str):
            instruction_summary.append(inst)

    log_jsonl("InstructionsLoaded", session_id, {
        "agent_id": agent_id,
        "agent_type": agent_type,
        "count": len(instructions),
        "instructions": instruction_summary,
    })

    # Log to stderr for visibility when debugging
    label = f"{agent_type}:{agent_id}" if agent_id else "main"
    sys.stderr.write(
        f"[hook] InstructionsLoaded ({label}): "
        f"{len(instructions)} instruction(s) loaded\n"
    )

    sys.exit(0)


if __name__ == "__main__":
    main()
