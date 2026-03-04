#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///

"""Tests for typescript_validator.py — project-specific TypeScript checks.

Tests verify that the validator correctly detects:
  1. `: any` type usage
  2. Hardcoded secrets (API keys, tokens)
  3. Admin/service-role client without justification
  4. Clean files produce no warnings
"""

import tempfile

from conftest import make_write_input, run_hook

HOOK = "validators/typescript_validator.py"


def test_detects_any_type():
    """: any in TypeScript should produce a warning."""
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w", delete=False) as f:
        f.write("function foo(x: any): void { }\n")
        f.flush()
        result = run_hook(HOOK, make_write_input(f.name))

    assert result["additional_context"] is not None
    assert "any" in result["additional_context"].lower()


def test_detects_as_any():
    """as any cast should produce a warning."""
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w", delete=False) as f:
        f.write("const x = something as any;\n")
        f.flush()
        result = run_hook(HOOK, make_write_input(f.name))

    assert result["additional_context"] is not None
    assert "any" in result["additional_context"].lower()


def test_ignores_any_in_comments():
    """: any in comments should not produce a warning."""
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w", delete=False) as f:
        f.write("// TODO: fix this any type later\nconst x: string = 'hello';\n")
        f.flush()
        result = run_hook(HOOK, make_write_input(f.name))

    if result["additional_context"]:
        assert "any" not in result["additional_context"].lower()


def test_detects_openai_api_key():
    """Hardcoded OpenAI API key should produce a warning."""
    # Build key dynamically to avoid tripping GitHub push protection
    fake_key = "sk-" + "proj-abc123def456ghi789jkl012mno345"
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w", delete=False) as f:
        f.write(f'const key = "{fake_key}";\n')
        f.flush()
        result = run_hook(HOOK, make_write_input(f.name))

    assert result["additional_context"] is not None
    assert "secret" in result["additional_context"].lower() or "key" in result["additional_context"].lower()


def test_detects_stripe_live_key():
    """Hardcoded Stripe live key should produce a warning."""
    # Build key dynamically to avoid tripping GitHub push protection
    fake_key = "sk" + "_live_51HzQBCA12345678901234567890"
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w", delete=False) as f:
        f.write(f'const stripe = "{fake_key}";\n')
        f.flush()
        result = run_hook(HOOK, make_write_input(f.name))

    assert result["additional_context"] is not None
    assert "secret" in result["additional_context"].lower() or "Stripe" in result["additional_context"]


def test_detects_github_token():
    """Hardcoded GitHub PAT should produce a warning."""
    # Build token dynamically to avoid tripping GitHub push protection
    fake_token = "ghp_" + "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef12"
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w", delete=False) as f:
        f.write(f'const token = "{fake_token}";\n')
        f.flush()
        result = run_hook(HOOK, make_write_input(f.name))

    assert result["additional_context"] is not None
    assert "secret" in result["additional_context"].lower() or "token" in result["additional_context"].lower()


def test_detects_admin_client_without_justification():
    """service-role usage without justification comment should warn."""
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w", delete=False) as f:
        f.write(
            "import { createClient } from '@supabase/supabase-js';\n"
            "\n"
            "const admin = createClient(url, process.env.SUPABASE_SERVICE_ROLE_KEY!);\n"
        )
        f.flush()
        result = run_hook(HOOK, make_write_input(f.name))

    assert result["additional_context"] is not None
    assert "service-role" in result["additional_context"].lower() or "admin" in result["additional_context"].lower()


def test_allows_admin_client_with_justification():
    """service-role usage WITH justification comment should not warn."""
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w", delete=False) as f:
        f.write(
            "import { createClient } from '@supabase/supabase-js';\n"
            "\n"
            "// admin — OAuth callback requires bypassing RLS\n"
            "const admin = createClient(url, process.env.SUPABASE_SERVICE_ROLE_KEY!);\n"
        )
        f.flush()
        result = run_hook(HOOK, make_write_input(f.name))

    if result["additional_context"]:
        ctx = result["additional_context"].lower()
        assert "service-role" not in ctx or "admin" not in ctx


def test_clean_file_no_warnings():
    """A clean TypeScript file should produce no warnings."""
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w", delete=False) as f:
        f.write(
            "export interface User {\n"
            "  id: string;\n"
            "  name: string;\n"
            "}\n"
            "\n"
            "export function formatUser(user: User): string {\n"
            "  return user.name;\n"
            "}\n"
        )
        f.flush()
        result = run_hook(HOOK, make_write_input(f.name))

    assert result["additional_context"] is None or result["additional_context"] == ""


def test_skips_test_files():
    """Test files should be skipped entirely."""
    with tempfile.NamedTemporaryFile(
        suffix=".test.ts", mode="w", delete=False
    ) as f:
        f.write("const x: any = 'allowed in tests';\n")
        f.flush()
        result = run_hook(HOOK, make_write_input(f.name))

    assert result["additional_context"] is None or result["additional_context"] == ""


def test_exit_code_always_zero():
    """Validator should always exit 0 (non-blocking)."""
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w", delete=False) as f:
        f.write("const x: any = 'bad';\n")
        f.flush()
        result = run_hook(HOOK, make_write_input(f.name))

    assert result["returncode"] == 0
