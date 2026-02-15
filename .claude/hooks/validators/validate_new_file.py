#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""Validator: checks that a new file was created in a directory.

Usage:
    uv run .claude/hooks/validators/validate_new_file.py \
        --directory specs --extension .md

Scans the directory for files matching the extension.
Exits 0 if at least one file exists, exits 2 if none found.
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Validate a new file was created"
    )
    parser.add_argument("--directory", required=True)
    parser.add_argument("--extension", required=True)
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
    matching_files = list(search_dir.glob(f"*{ext}"))

    if not matching_files:
        print(f"No {ext} files found in '{args.directory}'", file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
