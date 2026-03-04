"""Shared test fixtures for hook tests.

Provides helpers to simulate hook stdin/stdout interaction.
Hooks read JSON from stdin and optionally write JSON to stdout.
"""

import json
import subprocess
import sys
from pathlib import Path

# Hooks directory
HOOKS_DIR = Path(__file__).resolve().parent.parent.parent / ".claude" / "hooks"


def run_hook(
    hook_path: str | Path,
    input_data: dict,
    args: list[str] | None = None,
    timeout: int = 10,
) -> dict:
    """Run a hook script with JSON input and capture output.

    Args:
        hook_path: Path to the hook script (relative to HOOKS_DIR or absolute)
        input_data: Dict to serialize as JSON stdin
        args: Additional CLI arguments
        timeout: Timeout in seconds

    Returns:
        Dict with keys:
            - returncode: Process exit code
            - stdout: Raw stdout string
            - stderr: Raw stderr string
            - output: Parsed JSON from stdout (or None if not valid JSON)
            - hook_output: The hookSpecificOutput dict (or None)
            - additional_context: The additionalContext string (or None)
            - warnings: List of warning strings extracted from additionalContext
    """
    if isinstance(hook_path, str):
        hook_path = HOOKS_DIR / hook_path

    cmd = [sys.executable, str(hook_path)]
    if args:
        cmd.extend(args)

    result = subprocess.run(
        cmd,
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(HOOKS_DIR),
        env={
            "PATH": "/usr/bin:/usr/local/bin",
            "HOME": str(Path.home()),
            "PYTHONPATH": str(HOOKS_DIR),
        },
    )

    parsed_output = None
    hook_output = None
    additional_context = None
    warnings = []

    if result.stdout.strip():
        try:
            parsed_output = json.loads(result.stdout.strip())
            hook_output = parsed_output.get("hookSpecificOutput", {})
            additional_context = hook_output.get("additionalContext", "")
            # Extract warning lines from additionalContext
            if additional_context:
                for line in additional_context.split("\n"):
                    line = line.strip()
                    if line.startswith("- "):
                        warnings.append(line[2:].strip())
        except json.JSONDecodeError:
            pass

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "output": parsed_output,
        "hook_output": hook_output,
        "additional_context": additional_context,
        "warnings": warnings,
    }


def make_write_input(
    file_path: str,
    content: str = "",
    session_id: str = "test-session",
) -> dict:
    """Create a PostToolUse input for a Write operation."""
    return {
        "tool_name": "Write",
        "tool_input": {
            "file_path": file_path,
            "content": content,
        },
        "tool_output": "",
        "session_id": session_id,
        "hook_event_name": "PostToolUse",
    }


def make_edit_input(
    file_path: str,
    old_string: str = "",
    new_string: str = "",
    session_id: str = "test-session",
) -> dict:
    """Create a PostToolUse input for an Edit operation."""
    return {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": file_path,
            "old_string": old_string,
            "new_string": new_string,
        },
        "tool_output": "",
        "session_id": session_id,
        "hook_event_name": "PostToolUse",
    }


def make_bash_input(
    command: str,
    session_id: str = "test-session",
) -> dict:
    """Create a PreToolUse input for a Bash operation."""
    return {
        "tool_name": "Bash",
        "tool_input": {
            "command": command,
            "description": "test command",
        },
        "session_id": session_id,
        "hook_event_name": "PreToolUse",
    }
