#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""PostToolUse validator for TypeScript/React files — Alfred-specific hook.

Runs project-specific regex checks on .ts/.tsx files after builder/validator
agents use Write/Edit. This is the AGENT LAYER — it catches project-specific
pattern violations and TypeScript checks offloaded from post_tool_use.py.

Global hook (post_tool_use.py) covers:
  - console.log/error (with Alfred-specific message), missing server-only
    (Vite apps/addins only), default exports

This hook covers:
  - `: any` type usage (TypeScript safety)
  - Hardcoded secrets (API keys, tokens, JWTs)
  - Admin/service-role client without justification
  - Component library compliance (Fluent UI v9 — no @mui)
  - Direct @supabase/supabase-js imports (use wrapper packages)

Reads PostToolUse JSON from stdin. Outputs additionalContext JSON to stdout.
Always exits 0 (non-blocking) — warnings are informational.

CUSTOMIZE: Adapt the checks in check_file() to match your project's patterns.
"""

import json
import re
import sys
from pathlib import Path


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
    is_vite_app = (
        "packages/planner" in file_path
        or "packages/admin-dashboard" in file_path
    )
    is_addin = "connectors/outlook/addin" in file_path
    is_client_file = "'use client'" in content or '"use client"' in content
    is_supabase_package = "packages/supabase" in file_path

    # ── Check 9: `: any` type usage ──────────────────────────────────────
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        # Match `: any`, `as any`, `<any>` but not words containing "any"
        if ": any" in stripped or "as any" in stripped or "<any>" in stripped:
            warnings.append(
                f"Line {i}: `any` type detected — "
                "use proper types or `unknown` instead"
            )
            break  # One warning is enough

    # ── Check 11: Hardcoded secrets ───────────────────────────────────────
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        for pattern, description in SECRET_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                warnings.append(
                    f"Line {i}: Possible hardcoded secret "
                    f"({description}) — use environment variables"
                )
                break
        else:
            continue
        break  # One secret warning is enough

    # ── Check 12: Admin/service-role client without justification ─────────
    if re.search(
        r"service.?role|admin.?client|SUPABASE_SERVICE_ROLE",
        content,
        re.IGNORECASE,
    ):
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # Skip comment lines — they can't be the violation
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            if re.search(
                r"service.?role|admin.?client|SUPABASE_SERVICE_ROLE",
                line,
                re.IGNORECASE,
            ):
                # Check 3 lines above (including current) for justification
                context_start = max(0, i - 4)
                context_lines = "\n".join(lines[context_start:i])
                if not re.search(
                    r"//.*(?:admin|bypass|rls|oauth|callback|seed|webhook)",
                    context_lines,
                    re.IGNORECASE,
                ):
                    warnings.append(
                        f"Line {i}: Service-role/admin client bypasses "
                        "ALL RLS — add comment explaining why"
                    )
                break  # One warning is enough

    # ── Component Library Compliance (Fluent UI v9) ───────────────────────
    #
    # Alfred uses @fluentui/react-components. Block @mui imports in UI files.
    if (is_vite_app or is_addin) and path.suffix == ".tsx":
        if re.search(r"from\s+['\"]@mui/", content):
            warnings.append(
                "Uses @mui — project uses @fluentui/react-components instead. "
                "Replace with the equivalent Fluent UI v9 component."
            )

    # ── Direct Supabase Import Check ──────────────────────────────────────
    #
    # Alfred's packages should import from @alfred/supabase, not directly
    # from @supabase/supabase-js. Direct imports bypass project middleware
    # (auth, logging, error handling).
    if not is_supabase_package:
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            # Match import/require of @supabase/supabase-js but not type-only imports
            if re.search(r"from\s+['\"]@supabase/supabase-js['\"]", line):
                if not re.search(r"import\s+type\b", line):
                    warnings.append(
                        f"Line {i}: Direct @supabase/supabase-js import — "
                        "use @alfred/supabase wrapper package instead"
                    )
                    break

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
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    f"Alfred validator — {Path(file_path).name}:\n"
                    + "\n".join(f"  - {w}" for w in warnings)
                    + "\n(Fix these before marking task complete)"
                ),
            }
        }
        print(json.dumps(output))

    # Always exit 0 — warnings are informational, not blocking
    sys.exit(0)


if __name__ == "__main__":
    main()
