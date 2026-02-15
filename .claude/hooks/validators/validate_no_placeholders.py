#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""Validator: checks that files do NOT contain placeholder patterns.

Usage:
    uv run .claude/hooks/validators/validate_no_placeholders.py \
        --directory specs --extension .md \
        --not-contains '[To be detailed]' \
        --not-contains 'TODO: flesh out'

Finds the most recently modified file matching the extension in the
directory, then checks it does NOT contain any of the forbidden
placeholder patterns. Exits 0 if clean, exits 2 with descriptive
error listing all found placeholders and their line numbers.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Default placeholder patterns to detect skeleton/unfinished content
DEFAULT_PATTERNS = [
    r"\[To be detailed",
    r"TODO:\s*flesh out",
    r"\[placeholder\]",
    r"\bTBD\b",
    r"\[INSERT",
    r"<describe",
    r"<list",
    r"<clearly",
]


def main():
    parser = argparse.ArgumentParser(
        description="Validate file does not contain placeholder patterns"
    )
    parser.add_argument("--directory", required=True)
    parser.add_argument("--extension", required=True)
    parser.add_argument(
        "--not-contains", action="append",
        help="Forbidden pattern (repeatable, regex). If omitted, uses built-in defaults.",
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

    patterns = args.not_contains if args.not_contains else DEFAULT_PATTERNS

    target_file = matching_files[0]
    lines = target_file.read_text(encoding="utf-8").splitlines()

    found_placeholders: list[tuple[int, str, str]] = []
    for line_num, line in enumerate(lines, start=1):
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                found_placeholders.append((line_num, pattern, line.strip()))

    if found_placeholders:
        print(
            f"File '{target_file.name}' contains skeleton/placeholder content:",
            file=sys.stderr,
        )
        for line_num, pattern, line_text in found_placeholders:
            print(f"  Line {line_num}: matched '{pattern}'", file=sys.stderr)
            print(f"    > {line_text[:120]}", file=sys.stderr)
        print(
            "\nPlease flesh out all placeholder sections before finalizing.",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
