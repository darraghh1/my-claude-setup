#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
PostToolUseFailure hook — logs failed tool calls and injects
guidance back into Claude's context via additionalContext.

Pattern-matches on error messages to provide actionable advice
that prevents blind retries and steers toward the right fix.
"""

import json
import sys
from utils.constants import ensure_session_log_dir


def get_failure_guidance(tool_name, tool_input, error):
    """
    Return actionable guidance based on the failure pattern.

    The returned string is injected into Claude's context via
    additionalContext, influencing the next decision.
    """
    error_lower = error.lower() if error else ""

    # Hook blocked the tool call
    if "hook" in error_lower and "denied" in error_lower:
        return (
            "This was blocked by a PreToolUse hook rule in "
            ".claude/hooks/config/blocked-commands.json. "
            "Do NOT retry the same command. Use a different "
            "approach or ask the user if they want to allow it."
        )

    # User denied permission
    if "permission" in error_lower and "denied" in error_lower:
        return (
            "The user denied this tool call. Do NOT retry "
            "the same action. Ask the user what they would "
            "like you to do instead."
        )

    # Sibling tool call cascade failure
    if "sibling tool call" in error_lower:
        return (
            "This failed because a parallel sibling tool "
            "call errored. Retry this tool call individually."
        )

    # File not found
    if tool_name in ("Read", "Edit", "Write"):
        file_path = tool_input.get("file_path", "")

        if "not found" in error_lower or "no such file" in error_lower:
            return (
                f"File not found: {file_path}. "
                "Use Glob to search for the correct path "
                "before retrying."
            )

        # Edit string not found or not unique
        if tool_name == "Edit" and (
            "not found" in error_lower
            or "not unique" in error_lower
        ):
            return (
                "The Edit target string was not found or "
                "not unique in the file. Read the file first "
                "to see its current contents, then retry "
                "with the exact string from the file."
            )

        # Must read before editing
        if "read" in error_lower and "before" in error_lower:
            return (
                "You must Read the file before using Edit "
                "or Write. Read the file first, then retry."
            )

    # Bash failures
    if tool_name == "Bash":
        # Timeout
        if "timeout" in error_lower or "timed out" in error_lower:
            return (
                "Command timed out. Consider: increasing the "
                "timeout parameter, using run_in_background: "
                "true, or breaking into smaller steps."
            )

        # Generic non-zero exit — nudge to analyze
        if error:
            return (
                "Bash command failed. Analyze the error "
                "output before retrying. Do NOT run the same "
                "command unchanged."
            )

    # MCP tool failures
    if tool_name.startswith("mcp__"):
        return (
            "MCP tool failed. Check that tool parameters "
            "are correct and the MCP server is running."
        )

    return None


def main():
    try:
        input_data = json.load(sys.stdin)

        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        session_id = input_data.get("session_id", "unknown")
        error = input_data.get("tool_error", "")

        # --- Logging ---
        log_dir = ensure_session_log_dir(session_id)
        log_path = log_dir / "post_tool_use_failure.json"

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
                "hook_event_name", "PostToolUseFailure"
            ),
            "error": error,
        }

        if tool_name == "Bash":
            log_entry["command"] = (
                tool_input.get("command", "")[:300]
            )
        elif tool_name in ("Write", "Edit", "Read"):
            log_entry["file_path"] = tool_input.get(
                "file_path", ""
            )
        elif tool_name.startswith("mcp__"):
            parts = tool_name.split("__")
            if len(parts) >= 3:
                log_entry["mcp_server"] = parts[1]
                log_entry["mcp_tool_name"] = "__".join(
                    parts[2:]
                )
            log_entry["input_keys"] = (
                list(tool_input.keys())[:10]
            )

        log_data.append(log_entry)

        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)

        # --- Guidance injection ---
        guidance = get_failure_guidance(
            tool_name, tool_input, error
        )

        if guidance:
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUseFailure",
                    "additionalContext": guidance,
                }
            }
            print(json.dumps(output))

        sys.exit(0)

    except (json.JSONDecodeError, Exception):
        sys.exit(0)


if __name__ == "__main__":
    main()
