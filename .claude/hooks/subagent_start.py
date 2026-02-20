#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
SubagentStart hook — injects project rules and logs subagent launches.

Subagents don't inherit CLAUDE.md, full rule files, skill registries,
or MCP tools. This hook compensates by injecting context at spawn time
(the only fresh injection point — everything else is stale parent cache).

Context injection is tiered by agent type:
- builder/validator: Full rule files (read from disk) + skill registry
- All others: Condensed bullet-list summary

See docs/teams-research.md for the full context injection analysis.
"""

import json
import pathlib
import sys
from utils.constants import ensure_session_log_dir

# Agent types that get full rule injection.
# These do real implementation work where rule compliance prevents tech debt.
IMPLEMENTATION_AGENTS = {"builder", "validator"}

# Rule files to skip for implementation agents.
# git-workflow: builders don't commit. mcp-tools: builders don't have MCP tools.
SKIP_RULES = {"git-workflow", "mcp-tools"}

# Compact project rules for lightweight subagents (explore, general-purpose, etc.).
# Keep this concise — it's the minimum needed to avoid common violations.
COMPACT_RULES = """\
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

SKILL_REGISTRY = """\
AVAILABLE SKILLS (invoke via Skill tool — your spawn prompt specifies which to use):
- postgres-expert: Database migrations, RLS policies, functions, triggers
- server-action-builder: Server Actions with Zod validation, auth, service integration
- service-builder: Pure services with injected dependencies
- react-form-builder: Forms with react-hook-form, shadcn/ui, Zod
- playwright-e2e: End-to-end test code for critical user flows
- vercel-react-best-practices: React/Next.js performance patterns
- web-design-guidelines: UI/UX compliance review
"""


def find_rules_dir():
    """Find rules directory — check user-level first (works across all projects),
    then fall back to project-level."""
    user_rules = pathlib.Path.home() / ".claude" / "rules"
    if user_rules.exists():
        return user_rules

    project_rules = pathlib.Path(".claude/rules")
    if project_rules.exists():
        return project_rules

    return None


def read_rules(rules_dir):
    """Read all rule files from disk, skipping irrelevant ones.
    Returns formatted string with all rules."""
    sections = []
    for rule_file in sorted(rules_dir.glob("*.md")):
        if rule_file.stem in SKIP_RULES:
            continue
        try:
            content = rule_file.read_text().strip()
            if content:
                sections.append(f"## {rule_file.stem}\n\n{content}")
        except OSError:
            continue

    if not sections:
        return ""

    return "\n\n---\n\n".join(sections)


def build_implementation_context():
    """Build full context for builder/validator agents:
    compact rules + skill registry + full rule files from disk."""
    parts = [COMPACT_RULES, SKILL_REGISTRY]

    rules_dir = find_rules_dir()
    if rules_dir:
        full_rules = read_rules(rules_dir)
        if full_rules:
            parts.append(
                "PROJECT RULES — FULL (read fresh from disk at spawn time):\n\n"
                + full_rules
            )

    return "\n\n".join(parts)


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

        is_impl_agent = agent_type in IMPLEMENTATION_AGENTS

        log_entry = {
            "session_id": session_id,
            "hook_event_name": input_data.get(
                "hook_event_name", "SubagentStart"
            ),
            "agent_id": input_data.get("agent_id", ""),
            "agent_type": agent_type,
            "context_injected": True,
            "injection_tier": "full" if is_impl_agent else "compact",
        }
        log_data.append(log_entry)

        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)

        # --- Context injection ---
        # Builder/validator agents get full rules (read from disk) + skill registry.
        # All other agents get the condensed bullet list.
        if is_impl_agent:
            context = build_implementation_context()
        else:
            context = COMPACT_RULES

        output = {
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": context,
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    except (json.JSONDecodeError, Exception):
        sys.exit(0)


if __name__ == "__main__":
    main()
