#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""PostToolUse validator for TypeScript/React files — agent-specific hook.

Runs project-specific regex checks on .ts/.tsx files after builder/validator
agents use Write/Edit. This is the AGENT LAYER — it catches project-specific
pattern violations that the global post_tool_use.py hook doesn't cover.

Global hook (post_tool_use.py) covers:
  - console.log/error, `any` types, missing server-only, React hooks without
    use client, default exports, hardcoded secrets, admin client usage

This hook covers PROJECT-SPECIFIC patterns:
  - Wrong import paths (direct vs wrapper packages)
  - Missing framework wrappers (auth, validation, etc.)
  - Naming conventions specific to the project
  - Component library compliance

Reads PostToolUse JSON from stdin. Prints warnings to stdout.
Always exits 0 (non-blocking) — warnings are informational.

CUSTOMIZE: Adapt the checks in check_file() to match your project's patterns.
See DigitalMastery's version for a MakerKit-specific example, or Alfred's
version for a pnpm monorepo example.
"""

import json
import re
import sys
from pathlib import Path


def check_file(file_path: str) -> list[str]:
    """Run project-specific checks on a TypeScript/React file."""
    warnings: list[str] = []
    path = Path(file_path)

    if not path.exists() or path.suffix not in (".ts", ".tsx"):
        return warnings

    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return warnings

    lines = content.splitlines()

    # Skip test files — different rules apply
    is_test_file = (
        "__tests__" in file_path
        or file_path.endswith(".test.ts")
        or file_path.endswith(".test.tsx")
    )
    if is_test_file:
        return warnings

    # Classify the file
    is_server_file = any(
        keyword in file_path
        for keyword in ("server-actions", "service", "loader", "api/")
    )
    is_client_file = "'use client'" in content or '"use client"' in content
    is_server_action_file = "server-actions" in file_path

    # ── CUSTOMIZE: Project-Specific Import Paths ─────────────────────────
    #
    # Check for direct imports that should use project wrappers instead.
    # Example: Direct @supabase/ imports when your project has wrapper packages.
    #
    # for i, line in enumerate(lines, 1):
    #     stripped = line.strip()
    #     if stripped.startswith("//") or stripped.startswith("*"):
    #         continue
    #     if re.search(r"from\s+['\"]@supabase/", line):
    #         if not re.search(r"import\s+type\b", line):
    #             warnings.append(
    #                 f"  Line {i}: Direct @supabase/ import — use your project's "
    #                 f"wrapper package instead (e.g., @myproject/supabase)"
    #             )

    # ── CUSTOMIZE: Wrong Import Path Aliases ─────────────────────────────
    #
    # Check for wrong path aliases (e.g., ~/app/home/ instead of ~/home/).
    #
    # for i, line in enumerate(lines, 1):
    #     if re.search(r"from\s+['\"]~/app/", line):
    #         warnings.append(
    #             f"  Line {i}: Wrong path `~/app/...` — use `~/home/...`"
    #         )

    # ── CUSTOMIZE: Component Library Compliance ──────────────────────────
    #
    # Check for usage of raw HTML or other UI libraries when your project
    # uses a specific component library.
    #
    # Example for Fluent UI v9:
    # if is_client_file and path.suffix == ".tsx":
    #     if re.search(r"from\s+['\"]@mui/", content):
    #         warnings.append(
    #             "  Uses @mui — project uses @fluentui/react-components instead"
    #         )

    # ── CUSTOMIZE: Server Action Patterns ────────────────────────────────
    #
    # Check for missing auth wrappers in server actions.
    #
    # if is_server_action_file:
    #     has_use_server = bool(
    #         re.search(r"""^['"]use server['"]""", content, re.MULTILINE)
    #     )
    #     if has_use_server and "enhanceAction" not in content:
    #         warnings.append(
    #             "  Server action missing auth wrapper"
    #         )

    # ── CUSTOMIZE: Naming Conventions ────────────────────────────────────
    #
    # Check for export naming conventions (e.g., Action suffix on server actions).
    #
    # if is_server_action_file:
    #     for i, line in enumerate(lines, 1):
    #         match = re.search(r"export\s+const\s+(\w+)\s*=", line)
    #         if match:
    #             name = match.group(1)
    #             if not name.endswith("Action") and not name.endswith("Schema"):
    #                 warnings.append(
    #                     f"  Line {i}: Export `{name}` should end with 'Action'"
    #                 )

    return warnings


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path or not file_path.endswith((".ts", ".tsx")):
        sys.exit(0)

    warnings = check_file(file_path)

    if warnings:
        print(f"Project validator — {Path(file_path).name}:")
        for warning in warnings:
            print(warning)
        print("(Fix these before marking task complete)")

    # Always exit 0 — warnings are informational, not blocking
    sys.exit(0)


if __name__ == "__main__":
    main()
