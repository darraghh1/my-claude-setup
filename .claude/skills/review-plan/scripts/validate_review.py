#!/usr/bin/env python3
"""
Validate a plan review file against PLAN-REVIEW-TEMPLATE.md structure.

Usage:
    python scripts/validate_review.py <review-file-path> [--variant=A|B]

Variant A: plan.md review (template compliance only)
Variant B: phase review (template + codebase compliance)

Auto-detects variant from file content if not specified.

Returns exit code 0 if valid, 1 if issues found.

The user depends on this script to catch review format inconsistencies
that would otherwise slip through prose-based validation.
"""

import re
import sys
from pathlib import Path

# Variant A: plan.md review sections
PLAN_SECTIONS = [
    "Template Compliance",
    "Critical Issues",
    "Verdict",
]

PLAN_TEMPLATE_ITEMS = [
    "YAML Frontmatter",
    "Executive Summary",
    "Phasing Strategy",
    "Phase Table",
    "Architectural North Star",
    "Project Framework Alignment",
    "Security Requirements",
    "Implementation Standards",
    "Success Metrics",
    "Global Decision Log",
    "Resources & References",
]

# Variant B: phase review sections
PHASE_SECTIONS = [
    "Part 1: Template Compliance",
    "Part 2: Codebase Compliance",
    "Critical Issues Detail",
    "Fixes Applied",
    "Next Steps",
    "Verdict",
]

PHASE_TEMPLATE_ITEMS = [
    "YAML Frontmatter",
    "Overview",
    "Context & Workflow",
    "Prerequisites & Clarifications",
    "Requirements",
    "Decision Log",
    "Implementation Steps",
    "Step 0: TDD",
    "Verifiable Acceptance Criteria",
    "Quality Assurance",
    "Dependencies",
    "Completion Gate",
]

# Required header fields (both variants)
REQUIRED_HEADERS = [
    "Date:",
    "Verdict:",
]

# Required verdict fields
PLAN_VERDICT_FIELDS = [
    "Template Score:",
    "Ready:",
]

PHASE_VERDICT_FIELDS = [
    "Template Score:",
    "Codebase Score:",
    "Ready:",
]


def detect_variant(content: str) -> str:
    """Auto-detect whether this is a plan.md review (A) or phase review (B)."""
    if "Part 2: Codebase Compliance" in content:
        return "B"
    if "Template Score:" in content and "Codebase Score:" not in content:
        return "A"
    # Default to B (phase review) since it's more common
    return "B"


def validate_plan_review(content: str, file_path: str) -> list[str]:
    """Validate variant A (plan.md review)."""
    issues = []
    lines = content.split("\n")
    header_block = "\n".join(lines[:10])

    for field in REQUIRED_HEADERS:
        if field not in header_block:
            issues.append(f"Missing header field: {field}")

    for section in PLAN_SECTIONS:
        if section not in content:
            issues.append(f"Missing section: ## {section}")

    # Check template compliance table has all items
    for item in PLAN_TEMPLATE_ITEMS:
        if item not in content:
            issues.append(
                f"Missing template item in compliance table: {item}"
            )

    # Check verdict fields
    verdict_match = re.search(
        r"## Verdict\s*\n(.*?)(?:\n## |\Z)",
        content,
        re.DOTALL,
    )
    if verdict_match:
        verdict_block = verdict_match.group(1)
        for field in PLAN_VERDICT_FIELDS:
            if field not in verdict_block:
                issues.append(f"Verdict missing field: {field}")

    # Check template score format
    score_match = re.search(r"Template Score:\*?\*?\s*(\d+)/11", content)
    if not score_match:
        issues.append(
            "Template Score should be in X/11 format "
            "(11 sections in plan template)"
        )

    return issues


def validate_phase_review(content: str, file_path: str) -> list[str]:
    """Validate variant B (phase review)."""
    issues = []
    lines = content.split("\n")
    header_block = "\n".join(lines[:10])

    for field in REQUIRED_HEADERS:
        if field not in header_block:
            issues.append(f"Missing header field: {field}")

    for section in PHASE_SECTIONS:
        if section not in content:
            issues.append(f"Missing section: ## {section}")

    # Check template compliance table has all items
    for item in PHASE_TEMPLATE_ITEMS:
        if item not in content:
            issues.append(
                f"Missing template item in compliance table: {item}"
            )

    # Check verdict fields
    verdict_match = re.search(
        r"## Verdict\s*\n(.*?)(?:\n## |\Z)",
        content,
        re.DOTALL,
    )
    if verdict_match:
        verdict_block = verdict_match.group(1)
        for field in PHASE_VERDICT_FIELDS:
            if field not in verdict_block:
                issues.append(f"Verdict missing field: {field}")

    # Check template score format
    score_match = re.search(r"Template Score:\*?\*?\s*(\d+)/12", content)
    if not score_match:
        issues.append(
            "Template Score should be in X/12 format "
            "(12 sections in phase template)"
        )

    # Check for reference files used
    if "Reference files used:" not in content:
        if "reference" not in content.lower():
            issues.append(
                "Part 2 should list reference files used "
                "for codebase comparison"
            )

    # Check for forbidden patterns
    if "Positive Observations" in content:
        issues.append(
            "Contains 'Positive Observations' section "
            "(not in template — remove it)"
        )
    if "Additional Observations" in content:
        issues.append(
            "Contains 'Additional Observations' section "
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
            break

    return issues


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python validate_review.py <review-file> "
            "[--variant=A|B]"
        )
        sys.exit(2)

    file_path = sys.argv[1]
    path = Path(file_path)

    if not path.exists():
        print(f"File not found: {file_path}")
        sys.exit(2)

    content = path.read_text(encoding="utf-8")

    # Detect or parse variant
    variant = None
    for arg in sys.argv[2:]:
        if arg.startswith("--variant="):
            variant = arg.split("=")[1].upper()

    if variant is None:
        variant = detect_variant(content)

    if variant == "A":
        issues = validate_plan_review(content, file_path)
    else:
        issues = validate_phase_review(content, file_path)

    variant_name = (
        "plan.md review" if variant == "A" else "phase review"
    )

    if issues:
        print(
            f"FAIL: {len(issues)} issue(s) found in {file_path} "
            f"(variant {variant}: {variant_name}):\n"
        )
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        sys.exit(1)
    else:
        print(
            f"PASS: {file_path} matches {variant_name} template "
            f"structure."
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
