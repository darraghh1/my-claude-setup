#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
SubagentStart hook — injects project rules and logs subagent launches.

Subagents don't inherit CLAUDE.md or project rules. This hook injects
critical coding standards via additionalContext so every subagent
follows the same rules as the main session.
"""

import json
import sys
from utils.constants import ensure_session_log_dir

# Compact project rules for subagent context injection.
# Keep this concise — it's injected into every subagent's context.
PROJECT_RULES = """\
PROJECT RULES (injected by SubagentStart hook — subagents don't inherit CLAUDE.md):
- Use a proper logger — NEVER console.log/console.error in production code
- Add `import 'server-only'` at top of all server-side files
- Never use `any` — use proper types or `unknown`
- All Server Actions must have Zod validation + authentication checks
- All new tables MUST have RLS policies
- Service pattern: private class + exported factory function
- Check your component library before building custom UI
- Use `react-hook-form` + Zod for form validation
- Interfaces over types for object shapes; export all types
- Prefer single state object over multiple useState calls
- Import order: React > third-party > internal packages > local
"""


def main():
    try:
        input_data = json.load(sys.stdin)

        session_id = input_data.get("session_id", "unknown")
        agent_type = input_data.get("agent_type", "")

        # --- Logging ---
        log_dir = ensure_session_log_dir(session_id)
        log_path = log_dir / "subagent_start.json"

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
                "hook_event_name", "SubagentStart"
            ),
            "agent_id": input_data.get("agent_id", ""),
            "agent_type": agent_type,
            "context_injected": True,
        }
        log_data.append(log_entry)

        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)

        # --- Context injection ---
        # Inject project rules so subagents follow the same
        # coding standards as the main session.
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": PROJECT_RULES,
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    except (json.JSONDecodeError, Exception):
        sys.exit(0)


if __name__ == "__main__":
    main()
