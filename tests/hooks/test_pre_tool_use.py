#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///

"""Tests for pre_tool_use.py — security gate hook.

Tests verify that the hook correctly:
  1. Blocks rm -rf on dangerous paths
  2. Allows rm -rf on safe paths (node_modules, .next, dist)
  3. Blocks git push --force (without --force-with-lease)
  4. Blocks DROP DATABASE
  5. Allows normal commands
"""

from conftest import make_bash_input, run_hook

HOOK = "pre_tool_use.py"


def test_blocks_force_push():
    """git push --force should be denied."""
    result = run_hook(HOOK, make_bash_input("git push --force origin main"))

    assert result["hook_output"] is not None
    decision = result["hook_output"].get("permissionDecision", "")
    assert decision == "deny", f"Expected deny, got {decision}"


def test_allows_force_with_lease():
    """git push --force-with-lease should be allowed."""
    result = run_hook(
        HOOK, make_bash_input("git push --force-with-lease origin main")
    )

    if result["hook_output"]:
        decision = result["hook_output"].get("permissionDecision", "")
        assert decision != "deny", "Should not deny --force-with-lease"


def test_blocks_drop_database():
    """DROP DATABASE should be denied."""
    result = run_hook(
        HOOK, make_bash_input("psql -c 'DROP DATABASE production'")
    )

    assert result["hook_output"] is not None
    decision = result["hook_output"].get("permissionDecision", "")
    assert decision == "deny", f"Expected deny, got {decision}"


def test_asks_for_rm_rf_unknown_path():
    """rm -rf on unknown path should ask for confirmation."""
    result = run_hook(HOOK, make_bash_input("rm -rf /home/user/important"))

    assert result["hook_output"] is not None
    decision = result["hook_output"].get("permissionDecision", "")
    assert decision == "ask", f"Expected ask, got {decision}"


def test_allows_rm_rf_node_modules():
    """rm -rf node_modules should be allowed (safe path)."""
    result = run_hook(HOOK, make_bash_input("rm -rf node_modules"))

    if result["hook_output"]:
        decision = result["hook_output"].get("permissionDecision", "")
        assert decision not in ("deny", "ask"), (
            f"Should allow rm -rf node_modules, got {decision}"
        )


def test_allows_rm_rf_next():
    """rm -rf .next should be allowed (safe path)."""
    result = run_hook(HOOK, make_bash_input("rm -rf .next"))

    if result["hook_output"]:
        decision = result["hook_output"].get("permissionDecision", "")
        assert decision not in ("deny", "ask"), (
            f"Should allow rm -rf .next, got {decision}"
        )


def test_allows_normal_git_command():
    """Normal git commands should pass through."""
    result = run_hook(HOOK, make_bash_input("git status"))

    if result["hook_output"]:
        decision = result["hook_output"].get("permissionDecision", "")
        assert decision not in ("deny",), (
            f"Should allow git status, got {decision}"
        )


def test_asks_for_drop_table():
    """DROP TABLE should ask for confirmation."""
    result = run_hook(
        HOOK, make_bash_input("psql -c 'DROP TABLE users'")
    )

    assert result["hook_output"] is not None
    decision = result["hook_output"].get("permissionDecision", "")
    assert decision == "ask", f"Expected ask, got {decision}"


def test_asks_for_truncate():
    """TRUNCATE should ask for confirmation."""
    result = run_hook(
        HOOK, make_bash_input("psql -c 'TRUNCATE TABLE logs'")
    )

    assert result["hook_output"] is not None
    decision = result["hook_output"].get("permissionDecision", "")
    assert decision == "ask", f"Expected ask, got {decision}"


def test_asks_for_git_stash():
    """git stash (except list/show) should ask for confirmation."""
    result = run_hook(HOOK, make_bash_input("git stash"))

    assert result["hook_output"] is not None
    decision = result["hook_output"].get("permissionDecision", "")
    assert decision == "ask", f"Expected ask, got {decision}"


def test_allows_git_stash_list():
    """git stash list should be allowed."""
    result = run_hook(HOOK, make_bash_input("git stash list"))

    if result["hook_output"]:
        decision = result["hook_output"].get("permissionDecision", "")
        assert decision not in ("deny", "ask"), (
            f"Should allow git stash list, got {decision}"
        )


def test_exit_code_zero_on_allow():
    """Hook should exit 0 when allowing a command."""
    result = run_hook(HOOK, make_bash_input("ls -la"))
    assert result["returncode"] == 0
