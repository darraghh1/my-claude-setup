#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
PreToolUse hook — blocks dangerous commands and logs tool calls.

Security:
  Reads blocked command patterns from config/blocked-commands.json.
  Each entry has a regex pattern, optional safe_patterns, a reason,
  and an action ("deny" to hard-block, "ask" to prompt the user).
  Commands matching a pattern are intercepted UNLESS they also
  match a safe_pattern.

Logging:
  Logs a structured summary of every tool call to the session
  log directory.
"""

import json
import re
import sys
from pathlib import Path
from utils.constants import ensure_session_log_dir

CONFIG_PATH = Path(__file__).parent / "config" / "blocked-commands.json"


def load_blocked_commands():
    """Load blocked command patterns from config file."""
    if not CONFIG_PATH.exists():
        return []
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []


def check_blocked_commands(command):
    """
    Check if a Bash command matches any blocked pattern.

    Returns (action, reason) tuple where action is None (safe),
    "deny" (hard block), or "ask" (prompt user for permission).
    Each config entry can set "action": "ask" or "deny" (default).
    """
    rules = load_blocked_commands()
    normalized = " ".join(command.lower().split())

    for rule in rules:
        pattern = rule.get("pattern", "")
        if not pattern:
            continue

        if not re.search(pattern, normalized):
            continue

        # Matched a dangerous pattern — check safe_patterns
        safe_patterns = rule.get("safe_patterns", [])
        is_safe = any(
            re.search(sp, normalized) for sp in safe_patterns
        )

        if not is_safe:
            action = rule.get("action", "deny")
            reason = rule.get("reason", "Command blocked.")
            return action, reason

    return None, None


def permission_decision(action, reason):
    """
    Output a PreToolUse permission decision.

    action: "deny" (hard block) or "ask" (prompt user)
    """
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": action,
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


def summarize_tool_input(tool_name, tool_input):
    """Create a compact summary of key fields for logging."""
    summary = {"tool_name": tool_name}

    if tool_name == "Bash":
        summary["command"] = tool_input.get("command", "")[:200]
        if tool_input.get("description"):
            summary["description"] = (
                tool_input["description"][:100]
            )
        if tool_input.get("timeout"):
            summary["timeout"] = tool_input["timeout"]
        if tool_input.get("run_in_background"):
            summary["run_in_background"] = True

    elif tool_name == "Write":
        summary["file_path"] = tool_input.get("file_path", "")
        content = tool_input.get("content", "")
        summary["content_length"] = len(content)

    elif tool_name == "Edit":
        summary["file_path"] = tool_input.get("file_path", "")
        summary["replace_all"] = tool_input.get(
            "replace_all", False
        )

    elif tool_name == "Read":
        summary["file_path"] = tool_input.get("file_path", "")
        if tool_input.get("offset"):
            summary["offset"] = tool_input["offset"]
        if tool_input.get("limit"):
            summary["limit"] = tool_input["limit"]

    elif tool_name == "Glob":
        summary["pattern"] = tool_input.get("pattern", "")
        if tool_input.get("path"):
            summary["path"] = tool_input["path"]

    elif tool_name == "Grep":
        summary["pattern"] = tool_input.get("pattern", "")
        if tool_input.get("path"):
            summary["path"] = tool_input["path"]
        if tool_input.get("glob"):
            summary["glob"] = tool_input["glob"]

    elif tool_name == "WebFetch":
        summary["url"] = tool_input.get("url", "")
        summary["prompt"] = tool_input.get("prompt", "")[:100]

    elif tool_name == "WebSearch":
        summary["query"] = tool_input.get("query", "")

    elif tool_name == "Task":
        desc = tool_input.get("description", "")
        summary["description"] = desc[:100]
        summary["subagent_type"] = tool_input.get(
            "subagent_type", ""
        )
        if tool_input.get("model"):
            summary["model"] = tool_input["model"]
        if tool_input.get("run_in_background"):
            summary["run_in_background"] = True

    elif tool_name == "Skill":
        summary["skill"] = tool_input.get("skill", "")
        if tool_input.get("args"):
            summary["args"] = tool_input["args"][:100]

    elif tool_name.startswith("mcp__"):
        summary["mcp_tool"] = tool_name
        summary["input_keys"] = list(tool_input.keys())[:10]

    return summary


def main():
    try:
        input_data = json.load(sys.stdin)

        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # Check blocked commands for Bash tools
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            action, reason = check_blocked_commands(command)
            if action:
                permission_decision(action, reason)

        # Log tool call summary
        session_id = input_data.get("session_id", "unknown")
        log_dir = ensure_session_log_dir(session_id)
        log_path = log_dir / "pre_tool_use.json"

        if log_path.exists():
            with open(log_path, "r") as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []

        log_entry = {
            "tool_name": tool_name,
            "tool_use_id": input_data.get("tool_use_id", ""),
            "session_id": session_id,
            "hook_event_name": input_data.get(
                "hook_event_name", "PreToolUse"
            ),
            "tool_summary": summarize_tool_input(
                tool_name, tool_input
            ),
        }
        log_data.append(log_entry)

        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)

        sys.exit(0)

    except (json.JSONDecodeError, Exception):
        sys.exit(0)


if __name__ == "__main__":
    main()
