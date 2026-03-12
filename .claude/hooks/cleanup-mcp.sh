#!/usr/bin/env bash
# SessionEnd hook — kill MCP processes known to orphan after session exit.
# draw.io MCP spawns an HTTP server + browser per session that survives stdin close.
# This prevents slow memory accumulation that leads to system OOM.
#
# Drain stdin (hook protocol sends JSON) then clean up.

cat > /dev/null  # consume stdin

# Only kill draw.io — other MCP servers (context7, tavily, etc.) are lightweight
# stdio processes that clean up properly when their parent exits.
if pgrep -f "next-ai-drawio-mcp" > /dev/null 2>&1; then
    pkill -f "next-ai-drawio-mcp" 2>/dev/null
fi
