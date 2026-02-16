#!/usr/bin/env python3
"""SVG validation script for hand-crafted SVG diagrams.

Checks structural correctness: viewBox, overlapping elements,
and unresolved internal references (markers, gradients, filters).

Uses only Python stdlib — no external dependencies.
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
NS_MAP = {"svg": SVG_NS}

# Overlap thresholds
RECT_OVERLAP_RATIO = 0.50  # flag if intersection > 50% of smaller rect
RECT_AREA_RATIO = 4.0  # skip pairs where one rect is 4x+ larger (parent container)
TEXT_X_PROXIMITY = 50  # px — texts must be within this horizontal distance
TEXT_Y_MIN_SEP = 12  # px — default minimum vertical separation
DEFAULT_FONT_SIZE = 13  # px — assumed when no font-size attribute present


def ns(tag: str) -> str:
    """Return both namespaced and plain tag for searching."""
    return tag


def find_all(root: ET.Element, tag: str) -> list[ET.Element]:
    """Find all elements matching tag, with or without SVG namespace."""
    results = []
    results.extend(root.iter(f"{{{SVG_NS}}}{tag}"))
    results.extend(root.iter(tag))
    # Deduplicate (in case xmlns is absent and both match the same elements)
    seen_ids = set()
    unique = []
    for el in results:
        el_id = id(el)
        if el_id not in seen_ids:
            seen_ids.add(el_id)
            unique.append(el)
    return unique


def parse_url_ref(value: str) -> str | None:
    """Extract ID from url(#xxx) pattern."""
    m = re.match(r'url\(#([^)]+)\)', value or "")
    return m.group(1) if m else None


def collect_defined_ids(root: ET.Element) -> set[str]:
    """Collect all elements with an 'id' attribute."""
    ids = set()
    for el in root.iter():
        eid = el.get("id")
        if eid:
            ids.add(eid)
    return ids


# ─── Check functions ───────────────────────────────────────────


def check_viewbox(root: ET.Element) -> tuple[bool, str]:
    """Verify viewBox exists on root <svg> with valid dimensions."""
    vb = root.get("viewBox")
    if not vb:
        return False, "viewBox missing on root <svg>"

    # Parse space-separated or comma-separated
    parts = re.split(r"[,\s]+", vb.strip())
    if len(parts) != 4:
        return False, f"viewBox has {len(parts)} values (expected 4): {vb}"

    try:
        values = [float(p) for p in parts]
    except ValueError:
        return False, f"viewBox contains non-numeric values: {vb}"

    _, _, w, h = values
    if w <= 0 or h <= 0:
        return False, f"viewBox has non-positive dimensions: {w}x{h}"
    if w > 5000 or h > 5000:
        return False, f"viewBox dimensions exceed 5000px: {w}x{h}"

    return True, f"viewBox exists: {vb}"


def check_overlapping_rects(root: ET.Element) -> tuple[bool, str]:
    """Detect significantly overlapping rectangles (skip parent containers)."""
    rects = []
    for el in find_all(root, "rect"):
        try:
            x = float(el.get("x", 0))
            y = float(el.get("y", 0))
            w = float(el.get("width", 0))
            h = float(el.get("height", 0))
        except (ValueError, TypeError):
            continue
        if w > 0 and h > 0:
            rects.append((x, y, w, h, el.get("id", f"rect@{x},{y}")))

    overlaps = []
    for i in range(len(rects)):
        x1, y1, w1, h1, id1 = rects[i]
        area1 = w1 * h1
        for j in range(i + 1, len(rects)):
            x2, y2, w2, h2, id2 = rects[j]
            area2 = w2 * h2

            # Skip parent-child pairs (one is much larger)
            smaller = min(area1, area2)
            larger = max(area1, area2)
            if larger / smaller >= RECT_AREA_RATIO:
                continue

            # Calculate intersection
            ix1 = max(x1, x2)
            iy1 = max(y1, y2)
            ix2 = min(x1 + w1, x2 + w2)
            iy2 = min(y1 + h1, y2 + h2)

            if ix1 < ix2 and iy1 < iy2:
                intersection = (ix2 - ix1) * (iy2 - iy1)
                ratio = intersection / smaller
                if ratio > RECT_OVERLAP_RATIO:
                    overlaps.append(
                        f'"{id1}" ({x1},{y1} {w1}x{h1}) and '
                        f'"{id2}" ({x2},{y2} {w2}x{h2}) — '
                        f'{ratio:.0%} overlap'
                    )

    if overlaps:
        detail = "; ".join(overlaps)
        return False, f"Overlapping rectangles: {detail}"
    return True, "No overlapping rectangles detected"


def _get_font_size(el: ET.Element) -> float:
    """Extract font-size from element attribute, defaulting to DEFAULT_FONT_SIZE."""
    fs = el.get("font-size")
    if fs:
        # Strip 'px' suffix if present
        fs = fs.replace("px", "").strip()
        try:
            return float(fs)
        except ValueError:
            pass
    return DEFAULT_FONT_SIZE


def check_overlapping_text(root: ET.Element) -> tuple[bool, str]:
    """Detect text elements that are too close together vertically.

    Uses font-size-aware thresholds: the minimum baseline separation
    equals the font-size of the lower text element, since its ascenders
    need clearance from the upper text's descenders.
    """
    texts = []
    for el in find_all(root, "text"):
        try:
            x = float(el.get("x", 0))
            y = float(el.get("y", 0))
        except (ValueError, TypeError):
            continue
        label = el.text or ""
        # Also check for child tspan text
        if not label.strip():
            for child in el:
                if child.text:
                    label = child.text
                    break
        font_size = _get_font_size(el)
        texts.append((x, y, label.strip(), font_size))

    overlaps = []
    for i in range(len(texts)):
        x1, y1, label1, fs1 = texts[i]
        for j in range(i + 1, len(texts)):
            x2, y2, label2, fs2 = texts[j]
            # Only compare texts at similar x positions
            if abs(x1 - x2) <= TEXT_X_PROXIMITY:
                sep = abs(y1 - y2)
                # Min separation = font-size of the lower text (larger y)
                lower_fs = fs2 if y2 > y1 else fs1
                min_sep = lower_fs
                if 0 < sep < min_sep:
                    overlaps.append(
                        f'"{label1}" at ({x1},{y1}) and '
                        f'"{label2}" at ({x2},{y2}) — {sep:.0f}px apart'
                    )

    if overlaps:
        detail = "; ".join(overlaps)
        return False, f"Overlapping text: {detail}"
    return True, "No overlapping text detected"


def check_marker_refs(root: ET.Element) -> tuple[bool, str]:
    """Verify every marker-end/marker-start/marker-mid references a defined marker."""
    defined = set()
    for el in find_all(root, "marker"):
        mid = el.get("id")
        if mid:
            defined.add(mid)

    missing = []
    for el in root.iter():
        for attr in ("marker-end", "marker-start", "marker-mid"):
            ref = parse_url_ref(el.get(attr))
            if ref and ref not in defined:
                missing.append(f"{attr}=url(#{ref})")

    if missing:
        return False, f"Unresolved marker refs: {', '.join(missing)}"
    return True, "All marker references resolve"


def check_gradient_refs(root: ET.Element) -> tuple[bool, str]:
    """Verify every fill=url(#xxx) references a defined gradient/pattern."""
    all_ids = collect_defined_ids(root)

    missing = []
    for el in root.iter():
        ref = parse_url_ref(el.get("fill"))
        if ref and ref not in all_ids:
            tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
            missing.append(f'{tag} fill=url(#{ref})')

    if missing:
        return False, f"Unresolved gradient/fill refs: {', '.join(missing)}"
    return True, "All gradient/fill references resolve"


def check_filter_refs(root: ET.Element) -> tuple[bool, str]:
    """Verify every filter=url(#xxx) references a defined filter."""
    defined = set()
    for el in find_all(root, "filter"):
        fid = el.get("id")
        if fid:
            defined.add(fid)

    missing = []
    for el in root.iter():
        ref = parse_url_ref(el.get("filter"))
        if ref and ref not in defined:
            tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
            missing.append(f'{tag} filter=url(#{ref})')

    if missing:
        return False, f"Unresolved filter refs: {', '.join(missing)}"
    return True, "All filter references resolve"


# ─── Main ──────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a hand-crafted SVG diagram")
    parser.add_argument("svg_file", help="Path to the SVG file to validate")
    args = parser.parse_args()

    try:
        tree = ET.parse(args.svg_file)
    except ET.ParseError as e:
        print(f"[FAIL] SVG parse error: {e}")
        return 1
    except FileNotFoundError:
        print(f"[FAIL] File not found: {args.svg_file}")
        return 1

    root = tree.getroot()

    checks = [
        ("viewBox", check_viewbox),
        ("Overlapping rects", check_overlapping_rects),
        ("Overlapping text", check_overlapping_text),
        ("Marker references", check_marker_refs),
        ("Gradient references", check_gradient_refs),
        ("Filter references", check_filter_refs),
    ]

    passed = 0
    total = len(checks)
    failures = 0

    for name, fn in checks:
        ok, msg = fn(root)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {msg}")
        if ok:
            passed += 1
        else:
            failures += 1

    print("────────────────────────────")
    if failures == 0:
        print(f"Result: PASS ({passed}/{total} checks passed)")
        return 0
    else:
        print(f"Result: FAIL ({failures} failure{'s' if failures != 1 else ''} in {total} checks)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
