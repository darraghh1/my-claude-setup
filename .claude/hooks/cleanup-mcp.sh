#!/usr/bin/env bash
# SessionEnd hook (user-level) — fallback MCP cleanup.
#
# The project-level session_end.py does session-aware cleanup (only kills
# MCP processes owned by THIS Claude session). This script runs as a
# catch-all safety net, reading MCP server patterns dynamically from
# ~/.claude/settings.json rather than hardcoding server names.
#
# Note: this uses pkill -f (kills ALL matching processes), so it's less
# precise than the Python version. It only fires after session_end.py,
# so in practice it just catches stragglers.

cat > /dev/null  # consume stdin (hook protocol sends JSON)

SETTINGS="$HOME/.claude/settings.json"
[ -f "$SETTINGS" ] || exit 0

# Extract MCP package patterns from settings.json using Python (always available)
# Reads mcpServers.*.args, strips flags and version suffixes, outputs one pattern per line
patterns=$(python3 -c "
import json, sys
try:
    cfg = json.load(open('$SETTINGS'))
    for srv in cfg.get('mcpServers', {}).values():
        for arg in srv.get('args', []):
            if arg.startswith('-'):
                continue
            # Strip version suffix
            if arg.startswith('@'):
                slash = arg.find('/')
                if slash > 0:
                    rest = arg[slash+1:]
                    at = rest.find('@')
                    name = rest[:at] if at > 0 else rest
                    if len(name) > 3:
                        print(name)
            else:
                at = arg.find('@')
                name = arg[:at] if at > 0 else arg
                if name:
                    print(name)
            break
except Exception:
    pass
" 2>/dev/null)

# Kill matching processes (safety net — session_end.py handles most cases)
while IFS= read -r pattern; do
    [ -z "$pattern" ] && continue
    if pgrep -f "$pattern" > /dev/null 2>&1; then
        pkill -f "$pattern" 2>/dev/null
    fi
done <<< "$patterns"
