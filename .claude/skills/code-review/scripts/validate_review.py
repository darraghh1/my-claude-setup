#!/usr/bin/env python3
"""
Validate a code review file against CODE-REVIEW-TEMPLATE.md structure.

Usage:
    python scripts/validate_review.py <review-file-path>

Returns exit code 0 if valid, 1 if issues found.
Prints a summary of missing sections and format issues.

The user depends on this script to catch review format inconsistencies
that would otherwise slip through prose-based validation. Without it,
review files have inconsistent structure, making cross-phase comparison
impossible.
"""

import re
import sys
from pathlib import Path

# Required sections in the code review template (in order)
REQUIRED_SECTIONS = [
    "Part 1: Completeness Check",
    "Part 2: Code Quality",
    "Part 3: Security Assessment",
    "Action Items",
    "Fixes Applied",
    "Next Steps",
    "Verdict",
]

# Required subsections under Part 2
REQUIRED_SUBSECTIONS = [
    "Critical Issues",
    "High Priority Issues",
    "Medium Priority Issues",
    "Low Priority Issues",
]

# Required header fields
REQUIRED_HEADERS = [
    "Date:",
    "Phase File:",
    "Files Reviewed:",
    "Reference Files:",
    "Verdict:",
]

# Required verdict fields
REQUIRED_VERDICT_FIELDS = [
    "Completeness:",
    "Issues:",
    "Auto-fixed:",
    "Ready for Completion:",
]


def validate_review(file_path: str) -> list[str]:
    """Validate a code review file. Returns list of issues."""
    issues = []
    path = Path(file_path)

    if not path.exists():
        return [f"File not found: {file_path}"]

    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Check header fields
    header_block = "\n".join(lines[:15])
    for field in REQUIRED_HEADERS:
        if field not in header_block:
            issues.append(f"Missing header field: {field}")

    # Check required sections
    for section in REQUIRED_SECTIONS:
        if section not in content:
            issues.append(f"Missing section: ## {section}")

    # Check Part 2 subsections
    for subsection in REQUIRED_SUBSECTIONS:
        if subsection not in content:
            issues.append(f"Missing subsection: ### {subsection}")

    # Check verdict section has required fields
    verdict_match = re.search(
        r"## Verdict\s*\n(.*?)(?:\n## |\Z)",
        content,
        re.DOTALL,
    )
    if verdict_match:
        verdict_block = verdict_match.group(1)
        for field in REQUIRED_VERDICT_FIELDS:
            if field not in verdict_block:
                issues.append(f"Verdict missing field: {field}")
    else:
        issues.append("Could not parse Verdict section")

    # Check for forbidden patterns
    if "Positive Observations" in content:
        issues.append(
            "Contains 'Positive Observations' section "
            "(not in template — remove it)"
        )
    if "Technical Excellence" in content:
        issues.append(
            "Contains 'Technical Excellence' section "
            "(not in template — remove it)"
        )

    # Check status values are lowercase
    status_matches = re.findall(
        r"\|\s*(PASS|FAIL|Pass|Fail)\s*\|", content
    )
    for match in status_matches:
        if match != match.lower():
            issues.append(
                f"Status '{match}' should be lowercase: "
                f"'{match.lower()}'"
            )
            break  # One warning is enough

    # Check completeness table exists
    if "| # | Step/Requirement | Status | Notes |" not in content:
        # Allow slight variations
        if not re.search(
            r"\|\s*#\s*\|\s*Step", content, re.IGNORECASE
        ):
            issues.append(
                "Missing completeness check table "
                "(Part 1 should have a step/requirement table)"
            )

    # Check security assessment table exists
    if "| Check | Status | Notes |" not in content:
        if not re.search(
            r"\|\s*Check\s*\|\s*Status", content, re.IGNORECASE
        ):
            issues.append(
                "Missing security assessment table "
                "(Part 3 should have a check/status table)"
            )

    return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_review.py <review-file-path>")
        sys.exit(2)

    file_path = sys.argv[1]
    issues = validate_review(file_path)

    if issues:
        print(f"FAIL: {len(issues)} issue(s) found in {file_path}:\n")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        sys.exit(1)
    else:
        print(f"PASS: {file_path} matches template structure.")
        sys.exit(0)


if __name__ == "__main__":
    main()
