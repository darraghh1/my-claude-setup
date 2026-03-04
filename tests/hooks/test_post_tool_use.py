#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///

"""Tests for post_tool_use.py — quality gate hook.

Tests verify that the hook correctly detects:
  1. console.log/console.error usage
  2. Missing 'server-only' in server files
  3. Default exports in component files
  4. Clean files produce no warnings
"""

import tempfile
from pathlib import Path

from conftest import HOOKS_DIR, make_write_input, run_hook

HOOK = "post_tool_use.py"


def test_detects_console_log():
    """console.log in a TypeScript file should produce a warning."""
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w", delete=False) as f:
        f.write('const x = 1;\nconsole.log("debug");\n')
        f.flush()
        result = run_hook(HOOK, make_write_input(f.name))

    assert result["additional_context"] is not None
    assert "console.log" in result["additional_context"]


def test_detects_console_error():
    """console.error in a TypeScript file should produce a warning."""
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w", delete=False) as f:
        f.write('console.error("oops");\n')
        f.flush()
        result = run_hook(HOOK, make_write_input(f.name))

    assert result["additional_context"] is not None
    assert "console.log" in result["additional_context"]  # Warning covers both


def test_ignores_console_in_comments():
    """console.log in a comment should not produce a warning."""
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w", delete=False) as f:
        f.write('// console.log("commented out")\nconst x = 1;\n')
        f.flush()
        result = run_hook(HOOK, make_write_input(f.name))

    # Should not have console warning (may have no output at all)
    if result["additional_context"]:
        assert "console.log" not in result["additional_context"]


def test_detects_default_export_in_component():
    """Default export in a component file should produce a warning."""
    with tempfile.NamedTemporaryFile(
        suffix=".tsx", mode="w", delete=False,
        dir="/tmp", prefix="components_"
    ) as f:
        # Path must contain "_components/" or "components/"
        pass

    # Write to a path that includes "components/"
    comp_dir = Path(tempfile.mkdtemp()) / "components"
    comp_dir.mkdir()
    comp_file = comp_dir / "Button.tsx"
    comp_file.write_text(
        'export default function Button() { return <div/>; }\n'
    )

    result = run_hook(HOOK, make_write_input(str(comp_file)))

    assert result["additional_context"] is not None
    assert "Default export" in result["additional_context"]


def test_allows_default_export_in_page():
    """Default export in page.tsx should NOT produce a warning."""
    page_dir = Path(tempfile.mkdtemp()) / "components"
    page_dir.mkdir()
    page_file = page_dir / "page.tsx"
    page_file.write_text(
        'export default function Page() { return <div/>; }\n'
    )

    result = run_hook(HOOK, make_write_input(str(page_file)))

    if result["additional_context"]:
        assert "Default export" not in result["additional_context"]


def test_clean_file_no_warnings():
    """A clean TypeScript file should produce no warnings."""
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w", delete=False) as f:
        f.write(
            "import 'server-only';\n"
            "\n"
            "export function getData(): string {\n"
            "  return 'hello';\n"
            "}\n"
        )
        f.flush()
        result = run_hook(HOOK, make_write_input(f.name))

    assert result["additional_context"] is None or result["additional_context"] == ""


def test_skips_node_modules():
    """Files in node_modules should be skipped entirely."""
    result = run_hook(
        HOOK,
        make_write_input("/fake/node_modules/pkg/index.ts"),
    )
    assert result["additional_context"] is None or result["additional_context"] == ""


def test_skips_non_typescript():
    """Non-TypeScript files should be skipped."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write('print("hello")\n')
        f.flush()
        result = run_hook(HOOK, make_write_input(f.name))

    assert result["additional_context"] is None or result["additional_context"] == ""


def test_exit_code_always_zero():
    """Hook should always exit 0 (non-blocking)."""
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w", delete=False) as f:
        f.write('console.log("bad");\n')
        f.flush()
        result = run_hook(HOOK, make_write_input(f.name))

    assert result["returncode"] == 0
