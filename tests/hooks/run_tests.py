#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///

"""Test runner for hook tests.

Usage: uv run tests/hooks/run_tests.py
"""

import sys
from pathlib import Path

if __name__ == "__main__":
    test_dir = Path(__file__).parent
    sys.exit(
        __import__("pytest").main(
            [str(test_dir), "-v", "--tb=short", *sys.argv[1:]]
        )
    )
