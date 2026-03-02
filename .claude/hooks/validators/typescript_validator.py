#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""PostToolUse validator for TypeScript/React files — config-driven hook.

Runs project-specific regex checks on .ts/.tsx files after builder/validator
agents use Write/Edit. This is the PROJECT LAYER — it catches project-specific
pattern violations and TypeScript checks offloaded from post_tool_use.py.

Global hook (post_tool_use.py) covers:
  - console.log/error, missing server-only, use-client, default exports

This hook covers:
  Universal (always run):
    - `: any` type usage (TypeScript safety)
    - Hardcoded secrets (API keys, tokens, JWTs)
    - Admin/service-role client without justification
  Config-driven (from project-checks.json):
    - Component library compliance (blockedImports)
    - Wrapper import enforcement (wrapperImports)
    - Env var prefix checks (envVarChecks)
    - Wrong import path aliases (wrongImportPaths)
    - Client/server mismatch detection (clientServerMismatch)
    - Server action wrapper enforcement (serverActionWrapper)
    - Export naming conventions (exportNaming)
    - Directory naming conventions (directoryNaming)
    - Page wrapper enforcement (pageWrapper)

Configuration: reads project-checks.json for project-specific values.
When config is absent, only universal checks run (any, secrets, admin client).

Reads PostToolUse JSON from stdin. Outputs additionalContext JSON to stdout.
Always exits 0 (non-blocking) — warnings are informational.
"""

import json
import re
import sys
from pathlib import Path


PROJECT_CHECKS_CONFIG = (
    Path(__file__).parent.parent / "config" / "project-checks.json"
)

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


def load_project_config() -> dict:
    """Load project-specific check configuration.

    Returns empty dict when config file is absent — callers use
    .get() with defaults so only universal checks run.
    """
    if not PROJECT_CHECKS_CONFIG.exists():
        return {}
    try:
        with open(PROJECT_CHECKS_CONFIG, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {}


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

    config = load_project_config()

    # Determine if file is in a frontend app path.
    # null/absent = all paths are frontend. Set = only those paths.
    frontend_paths = config.get("frontendAppPaths")
    in_frontend_app = (
        frontend_paths is None
        or any(p in file_path for p in frontend_paths)
    )

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

    # ── Component Library Compliance (config-driven) ──────────────────────
    #
    # Only checks files within frontendAppPaths. Each blockedImports entry
    # specifies a pattern to flag and a message with the preferred alternative.
    blocked_imports = config.get("blockedImports", [])
    if in_frontend_app and path.suffix == ".tsx":
        for blocked in blocked_imports:
            pat = blocked.get("pattern", "")
            msg = blocked.get("message", "blocked by project config")
            if pat and re.search(
                r"from\s+['\"]" + re.escape(pat), content
            ):
                warnings.append(f"Uses {pat} — {msg}")

    # ── Wrapper Import Enforcement (config-driven) ────────────────────────
    #
    # Flags direct imports of packages that should go through a project
    # wrapper (e.g., @supabase/supabase-js → @alfred/supabase).
    # Type-only imports are allowed. skipPaths excludes the wrapper package itself.
    wrapper_imports = config.get("wrapperImports", [])
    for wrapper in wrapper_imports:
        direct = wrapper.get("direct", "")
        wrapper_pkg = wrapper.get("wrapper", "")
        skip_paths = wrapper.get("skipPaths", [])
        if not direct:
            continue
        if any(sp in file_path for sp in skip_paths):
            continue
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            if re.search(
                r"from\s+['\"]" + re.escape(direct) + r"['\"]", line
            ):
                if not re.search(r"import\s+type\b", line):
                    warnings.append(
                        f"Line {i}: Direct {direct} import — "
                        f"use {wrapper_pkg} wrapper package instead"
                    )
                    break

    # ── Env Var Checks (config-driven) ────────────────────────────────
    #
    # Flags wrong environment variable patterns in specific paths.
    # Example: Vite apps using NEXT_PUBLIC_ instead of VITE_ prefix.
    env_var_checks = config.get("envVarChecks", [])
    for check in env_var_checks:
        paths = check.get("paths", [])
        pattern = check.get("pattern", "")
        msg = check.get("message", "wrong env var pattern")
        if not pattern or not any(p in file_path for p in paths):
            continue
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            if re.search(pattern, line):
                warnings.append(f"Line {i}: {msg}")
                break

    # ── Wrong Import Paths (config-driven) ────────────────────────────
    #
    # Flags incorrect path aliases (e.g., ~/app/ when ~/home/ is correct).
    wrong_import_paths = config.get("wrongImportPaths", [])
    for entry in wrong_import_paths:
        pattern = entry.get("pattern", "")
        msg = entry.get("message", "wrong import path")
        if not pattern:
            continue
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            if re.search(r"from\s+['\"]" + re.escape(pattern), line):
                warnings.append(f"Line {i}: {msg}")
                break

    # ── Client/Server Mismatch (config-driven) ────────────────────────
    #
    # Flags server functions used in client files and client hooks used
    # in server files. Uses 'use client' directive to determine file type.
    cs_config = config.get("clientServerMismatch")
    if cs_config:
        is_client_file = "'use client'" in content or '"use client"' in content
        server_fns = cs_config.get("serverFunctions", [])
        client_hooks = cs_config.get("clientHooks", [])
        if is_client_file:
            # Client file — flag server function usage
            for fn in server_fns:
                for i, line in enumerate(lines, 1):
                    if fn in line:
                        stripped = line.strip()
                        if stripped.startswith("//") or stripped.startswith("*"):
                            continue
                        warnings.append(
                            f"Line {i}: `{fn}` in client file — "
                            + cs_config.get(
                                "serverInClientMessage",
                                "use client-side alternative",
                            )
                        )
                        break
        else:
            # Server file — flag client hook usage
            for hook in client_hooks:
                for i, line in enumerate(lines, 1):
                    if hook in line:
                        stripped = line.strip()
                        if stripped.startswith("//") or stripped.startswith("*"):
                            continue
                        # Skip imports — only flag actual usage
                        if re.search(r"import\b", line):
                            continue
                        warnings.append(
                            f"Line {i}: `{hook}` in server file — "
                            + cs_config.get(
                                "clientInServerMessage",
                                "use server-side alternative",
                            )
                        )
                        break

    # ── Server Action Wrapper (config-driven) ──────────────────────────
    #
    # Requires a wrapper function (e.g., enhanceAction) in server action
    # files and optionally checks for a schema option.
    sa_config = config.get("serverActionWrapper")
    has_use_server = "'use server'" in content or '"use server"' in content
    if sa_config and has_use_server:
        wrapper_fn = sa_config.get("function", "")
        if wrapper_fn and wrapper_fn not in content:
            warnings.append(
                sa_config.get("message", f"Missing {wrapper_fn} wrapper")
            )
        elif wrapper_fn and sa_config.get("requireSchema", False):
            # Wrapper is present — check each call has schema:
            for i, line in enumerate(lines, 1):
                if wrapper_fn in line and "schema" not in line:
                    # Look ahead a few lines for schema in a multi-line call
                    lookahead = "\n".join(lines[i - 1 : i + 4])
                    if "schema" not in lookahead:
                        warnings.append(
                            f"Line {i}: "
                            + sa_config.get(
                                "schemaMissingMessage",
                                f"{wrapper_fn}() missing schema option",
                            )
                        )
                        break

    # ── Export Naming Conventions (config-driven) ──────────────────────
    #
    # Requires specific suffixes on exported functions/consts in certain paths.
    # Example: server action exports must end with "Action" or "Schema".
    export_naming = config.get("exportNaming", [])
    for rule in export_naming:
        paths = rule.get("paths", [])
        allowed = rule.get("allowed", [])
        msg = rule.get("message", "export naming violation")
        if not paths or not any(p in file_path for p in paths):
            continue
        if not allowed:
            continue
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            # Match exported names: export const/function/async function NAME
            m = re.match(
                r"export\s+(?:const|function|async\s+function)\s+(\w+)", stripped
            )
            if m:
                name = m.group(1)
                if not any(name.endswith(suffix) for suffix in allowed):
                    warnings.append(f"Line {i}: `{name}` — {msg}")
                    break

    # ── Directory Naming Conventions (config-driven) ───────────────────
    #
    # Flags files that live in incorrectly named directories.
    # Example: _lib/schemas/ should be _lib/schema/ (singular).
    directory_naming = config.get("directoryNaming", [])
    for rule in directory_naming:
        pattern = rule.get("pattern", "")
        msg = rule.get("message", "directory naming violation")
        if pattern and pattern in file_path:
            warnings.append(f"{msg} (found in path: {pattern})")
            break

    # ── Page Wrapper (config-driven) ──────────────────────────────────
    #
    # Requires a wrapper function on the default export of page files.
    # Example: export default withI18n(PageComponent)
    pw_config = config.get("pageWrapper")
    if pw_config:
        pw_paths = pw_config.get("paths", [])
        pw_fn = pw_config.get("function", "")
        pw_msg = pw_config.get("message", f"wrap page export with {pw_fn}")
        is_page_file = path.name in ("page.tsx", "page.ts")
        in_pw_paths = not pw_paths or any(p in file_path for p in pw_paths)
        if is_page_file and pw_fn and in_pw_paths:
            if pw_fn not in content:
                warnings.append(pw_msg)

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
                    f"Project validator — {Path(file_path).name}:\n"
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
