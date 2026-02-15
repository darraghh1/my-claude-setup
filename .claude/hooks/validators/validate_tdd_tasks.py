#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""Validator: enforces TDD task ordering in plan documents.

Usage:
    uv run .claude/hooks/validators/validate_tdd_tasks.py \
        --directory specs --extension .md \
        --contains-before 'TDD|Write tests|Test Definition' 'Implement|Build|Create'

Finds the most recently modified file matching the extension in the
directory, then verifies:
  1. At least one task/section matches the first pattern (TDD-related)
  2. The first TDD match appears BEFORE the first implementation match

Exits 0 if valid, exits 2 if no TDD task found or if TDD task
appears after implementation task.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Default patterns for TDD tasks and implementation tasks
DEFAULT_TDD_PATTERN = r"(?:TDD|Write tests|Test Definition)"
DEFAULT_IMPL_PATTERN = r"(?:Implement|Build|Create|Code the)"


def find_first_match(lines: list[str], pattern: str) -> tuple[int, str] | None:
    """Find the first line matching a pattern (case-insensitive)."""
    for line_num, line in enumerate(lines, start=1):
        if re.search(pattern, line, re.IGNORECASE):
            return (line_num, line.strip())
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Validate TDD task ordering in plan documents"
    )
    parser.add_argument("--directory", required=True)
    parser.add_argument("--extension", required=True)
    parser.add_argument(
        "--contains-before", nargs=2,
        metavar=("TDD_PATTERN", "IMPL_PATTERN"),
        help="Two regex patterns: first (TDD) must appear before second (implementation).",
    )
    args = parser.parse_args()

    # Read stdin (hook input) — only need cwd
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        hook_input = {}

    cwd = hook_input.get("cwd", ".")
    search_dir = Path(cwd) / args.directory

    if not search_dir.exists():
        sys.exit(0)

    ext = args.extension if args.extension.startswith(".") else f".{args.extension}"
    matching_files = sorted(
        search_dir.glob(f"*{ext}"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    if not matching_files:
        sys.exit(0)

    if args.contains_before:
        tdd_pattern = args.contains_before[0]
        impl_pattern = args.contains_before[1]
    else:
        tdd_pattern = DEFAULT_TDD_PATTERN
        impl_pattern = DEFAULT_IMPL_PATTERN

    target_file = matching_files[0]
    lines = target_file.read_text(encoding="utf-8").splitlines()

    first_tdd = find_first_match(lines, tdd_pattern)
    first_impl = find_first_match(lines, impl_pattern)

    # Validation 1: At least one TDD task must exist
    if first_tdd is None:
        print(
            f"File '{target_file.name}' has no TDD/testing task.",
            file=sys.stderr,
        )
        print(f"  Expected pattern: {tdd_pattern}", file=sys.stderr)
        print(
            "\nEvery plan must include a TDD task "
            "(e.g., 'Write tests', 'Test Definition', or 'TDD').",
            file=sys.stderr,
        )
        if first_impl:
            print(
                f"  Implementation task found at line {first_impl[0]}: "
                f"{first_impl[1][:100]}",
                file=sys.stderr,
            )
        sys.exit(2)

    # Validation 2: TDD task must appear before implementation task
    if first_impl is not None and first_tdd[0] > first_impl[0]:
        print(
            f"File '{target_file.name}' has TDD task AFTER implementation task:",
            file=sys.stderr,
        )
        print(
            f"  Implementation at line {first_impl[0]}: {first_impl[1][:100]}",
            file=sys.stderr,
        )
        print(
            f"  TDD task at line {first_tdd[0]}: {first_tdd[1][:100]}",
            file=sys.stderr,
        )
        print(
            "\nTDD tasks must appear BEFORE implementation tasks. "
            "Tests define behavior first.",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
