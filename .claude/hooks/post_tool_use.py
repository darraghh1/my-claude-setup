#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
PostToolUse hook — quality gates + logging for completed tool calls.

After Write/Edit on TypeScript files, scans for common CLAUDE.md
violations and injects warnings via additionalContext so Claude
fixes them immediately rather than waiting for verification.

Quality checks (TypeScript/TSX files only):
  1. console.log / console.error usage (should use createLogger())
  2. Missing `import 'server-only'` in server files (Vite apps and addins only)
  3. [MOVED] `: any` type — now owned by typescript_validator.py
  4. [DISABLED] React hooks without 'use client' — Alfred has no Next.js App Router
  5. Default exports for non-page/layout components
  6. [MOVED] Hardcoded secrets — now owned by typescript_validator.py
  7. [MOVED] Service-role / admin client — now owned by typescript_validator.py

TypeScript pattern checks (any, secrets, admin client) are owned by
typescript_validator.py to avoid duplicate warnings when both hooks run.
"""

import json
import re
import sys
from pathlib import Path
from utils.constants import ensure_session_log_dir, log_jsonl

EXCLUDES_CONFIG_PATH = (
    Path(__file__).parent / "config" / "quality-check-excludes.json"
)

# File extensions to run quality checks on
TS_EXTENSIONS = frozenset({".ts", ".tsx"})

# Directories that indicate server-side code
SERVER_INDICATORS = frozenset({
    "server",
    "_lib/server",
    "server-actions",
    "api",
    "actions",
})

# Files/dirs to skip quality checks (generated code, config, etc.)
SKIP_PATTERNS = frozenset({
    "node_modules",
    ".next",
    "dist",
    "database.types",
    ".gen.",
    "vitest.",
    "__tests__",
    "__mocks__",
})

# Regex patterns for hardcoded secrets — each is (pattern, description)
SECRET_PATTERNS = (
    (r"""['"]sk-[a-zA-Z0-9_-]{20,}['"]""", "API key (sk-...)"),
    (r"""['"]sk_live_[a-zA-Z0-9_-]+['"]""", "Stripe live key"),
    (r"""['"]sk_test_[a-zA-Z0-9_-]+['"]""", "Stripe test key"),
    (r"""['"]ghp_[a-zA-Z0-9]+['"]""", "GitHub personal access token"),
    (r"""['"]eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.""", "JWT token"),
    (
        r"""(?:api[_-]?key|apikey|secret|password|token)\s*[:=]\s*['"][^'"]{8,}['"]""",
        "Possible hardcoded secret",
    ),
)

# React hooks that require 'use client' directive
REACT_HOOK_RE = re.compile(
    r"\buse(State|Effect|Ref|Callback|Memo|Context|Reducer|Transition)\b"
)


def load_excluded_paths() -> list[str]:
    """Load project-specific path exclusions from config file."""
    if not EXCLUDES_CONFIG_PATH.exists():
        return []
    try:
        with open(EXCLUDES_CONFIG_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []


def should_skip(file_path: str) -> bool:
    """Check if file should be skipped for quality checks."""
    if any(p in file_path for p in SKIP_PATTERNS):
        return True
    excluded = load_excluded_paths()
    return any(p in file_path for p in excluded)


def is_server_file(file_path: str) -> bool:
    """Heuristic: is this likely a server-side file?"""
    path_lower = file_path.lower()
    # Explicit server directories
    if any(ind in path_lower for ind in SERVER_INDICATORS):
        return True
    # Files with server action naming
    if "server-action" in path_lower:
        return True
    # Loader files
    if path_lower.endswith(".loader.ts"):
        return True
    # Service files
    if path_lower.endswith(".service.ts"):
        return True
    return False


def check_typescript_quality(
    file_path: str,
    edited_range: tuple[int, int] | None = None,
) -> list[str]:
    """
    Scan a TypeScript file for common CLAUDE.md violations.

    Returns a list of warning strings. Empty list = no issues.

    If edited_range is set (start_line, end_line inclusive),
    line-level warnings outside the range are filtered out.
    File-level warnings (no line number) always pass through.
    """
    warnings = []
    path_obj = Path(file_path)
    ext = path_obj.suffix

    try:
        content = path_obj.read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError, OSError):
        return warnings

    lines = content.split("\n")
    is_server = is_server_file(file_path)

    # Classify app context for framework-specific checks
    is_vite_app = (
        "packages/planner" in file_path
        or "packages/admin-dashboard" in file_path
    )
    is_addin = "connectors/outlook/addin" in file_path

    # ── Check 1: console.log / console.error ──────────────────────────
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Skip comments
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        if "console.log(" in stripped or "console.error(" in stripped:
            warnings.append(
                f"Line {i}: console.log/error detected — "
                "use createLogger() from @alfred/shared"
            )
            break  # One warning is enough to trigger fix

    # ── Check 2: Missing 'server-only' in server files ────────────────
    # Only applies to Next.js/Vite apps and addins — not Node.js/Express services
    if is_server and (is_vite_app or is_addin):
        has_server_only = any(
            "server-only" in line
            for line in lines[:10]  # Check first 10 lines
        )
        has_use_server = any(
            "'use server'" in line or '"use server"' in line
            for line in lines[:5]
        )
        # 'use server' files don't need 'server-only' import
        if not has_server_only and not has_use_server:
            warnings.append(
                "Server file missing `import 'server-only'` — "
                "without it, server code can leak to the client bundle"
            )

    # ── Check 3: [MOVED to typescript_validator.py] ─────────────────────
    # `: any` type check moved to avoid duplicate warnings when both hooks run.

    # ── Check 4: [DISABLED] React hooks without 'use client' ──────────
    # Alfred has no Next.js App Router apps — all React is Vite.
    # 'use client' is a Next.js App Router directive; it's meaningless in Vite.

    # ── Check 5: Default exports for non-page/layout components ───────
    is_page = path_obj.name == "page.tsx"
    is_layout = path_obj.name == "layout.tsx"
    is_component = "_components/" in file_path or "components/" in file_path
    if (
        ext == ".tsx"
        and not is_page
        and not is_layout
        and is_component
        and re.search(r"^export\s+default\s+", content, re.MULTILINE)
    ):
        warnings.append(
            "Default export in component file — "
            "prefer named exports (except page/layout)"
        )

    # ── Check 6: [MOVED to typescript_validator.py] ───────────────────
    # Hardcoded secrets check moved to avoid duplicate warnings.

    # ── Check 7: [MOVED to typescript_validator.py] ───────────────────
    # Admin/service-role client check moved to avoid duplicate warnings.

    # Filter line-level warnings to edited range (Edit operations only)
    if edited_range is not None:
        line_re = re.compile(r"^Line (\d+):")
        filtered = []
        for w in warnings:
            m = line_re.match(w)
            if m:
                line_num = int(m.group(1))
                if edited_range[0] <= line_num <= edited_range[1]:
                    filtered.append(w)
            else:
                # File-level warnings always pass through
                filtered.append(w)
        warnings = filtered

    return warnings


def main():
    try:
        input_data = json.load(sys.stdin)

        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        session_id = input_data.get("session_id", "unknown")

        # --- Quality checks for Write/Edit on TS files ---
        quality_warnings = []

        if tool_name in ("Write", "Edit"):
            file_path = tool_input.get("file_path", "")
            ext = Path(file_path).suffix

            if ext in TS_EXTENSIONS and not should_skip(file_path):
                # For Edit, scope warnings to the edited region
                edited_range = None
                if tool_name == "Edit":
                    new_string = tool_input.get("new_string", "")
                    try:
                        content = Path(file_path).read_text(
                            encoding="utf-8"
                        )
                        pos = content.find(new_string)
                        if pos >= 0:
                            start_line = (
                                content[:pos].count("\n") + 1
                            )
                            end_line = (
                                start_line + new_string.count("\n")
                            )
                            edited_range = (start_line, end_line)
                    except (FileNotFoundError, OSError):
                        pass  # Fall back to full-file scan

                quality_warnings = check_typescript_quality(
                    file_path, edited_range=edited_range
                )

        # --- Logging ---
        log_dir = ensure_session_log_dir(session_id)
        log_path = log_dir / "post_tool_use.json"

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
                "hook_event_name", "PostToolUse"
            ),
        }

        if quality_warnings:
            log_entry["quality_warnings"] = quality_warnings

        # For MCP tools, log server and tool separately
        if tool_name.startswith("mcp__"):
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

        # JSONL append-only log (grep-able across sessions)
        jsonl_data = {"tool": tool_name}
        if quality_warnings:
            jsonl_data["warnings"] = quality_warnings
        log_jsonl("PostToolUse", session_id, jsonl_data)

        # --- MCP output trimming ---
        # Large MCP tool outputs flood context and degrade
        # response quality. Trim outputs that exceed the
        # threshold to prevent context bloat.
        mcp_output = {}
        if tool_name.startswith("mcp__"):
            tool_output = input_data.get("tool_output", "")
            if isinstance(tool_output, str):
                output_len = len(tool_output)
            else:
                output_len = len(json.dumps(tool_output))

            MCP_TRIM_THRESHOLD = 15000  # chars
            if output_len > MCP_TRIM_THRESHOLD:
                if isinstance(tool_output, str):
                    trimmed = tool_output[:MCP_TRIM_THRESHOLD]
                else:
                    trimmed = json.dumps(tool_output)[
                        :MCP_TRIM_THRESHOLD
                    ]
                mcp_output["updatedMCPToolOutput"] = (
                    trimmed
                    + f"\n\n[OUTPUT TRIMMED: {output_len} chars "
                    f"exceeded {MCP_TRIM_THRESHOLD} threshold. "
                    "Use more targeted queries to reduce output.]"
                )

        # --- Context injection for quality warnings ---
        output = {}
        if quality_warnings or mcp_output:
            hook_output = {
                "hookEventName": "PostToolUse",
            }

            if quality_warnings:
                context = (
                    "PostToolUse quality check found issues in "
                    f"{tool_input.get('file_path', 'unknown')}:\n"
                    + "\n".join(
                        f"  - {w}" for w in quality_warnings
                    )
                    + "\nFix these before continuing."
                )
                hook_output["additionalContext"] = context

            if mcp_output:
                hook_output.update(mcp_output)

            output = {
                "hookSpecificOutput": hook_output
            }
            print(json.dumps(output))

        sys.exit(0)

    except (json.JSONDecodeError, Exception):
        sys.exit(0)


if __name__ == "__main__":
    main()
