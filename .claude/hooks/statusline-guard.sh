#!/bin/bash
# Status line guard — lightweight agent detection wrapper.
#
# Detects teammate agents and renders a minimal status line instead
# of invoking the full HUD plugin.
#
# Detection: The first session_id seen is stored as the "main" session.
# Any different session_id is treated as an agent and gets a lightweight
# status line instead of the full HUD.
#
# Usage in settings.json:
#   "statusLine": {
#     "type": "command",
#     "command": "bash /path/to/.claude/hooks/statusline-guard.sh"
#   }

set -euo pipefail

MAIN_SESSION_FILE="/tmp/statusline-main-session"

# Full HUD command — update this if you change your HUD plugin
FULL_HUD_DIR=$(ls -td ~/.claude/plugins/cache/claude-ultimate-hud/claude-ultimate-hud/*/ 2>/dev/null | head -1)
FULL_HUD_CMD="${HOME}/.bun/bin/bun ${FULL_HUD_DIR}src/index.ts"

# Read stdin (Claude Code passes JSON with model, context_window, cost, etc.)
INPUT=$(cat)

# Extract session_id
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)

# --- Detection ---

IS_AGENT=false

# Method 1: agent_id/agent_type in stdin (future-proof — when Claude adds these)
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // empty' 2>/dev/null)
AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty' 2>/dev/null)
if [ -n "$AGENT_ID" ] || [ -n "$AGENT_TYPE" ]; then
  IS_AGENT=true
fi

# Method 2: session_id comparison — first session seen is "main"
if [ "$IS_AGENT" = false ] && [ -n "$SESSION_ID" ]; then
  if [ ! -f "$MAIN_SESSION_FILE" ]; then
    # First invocation — this is the main session
    echo "$SESSION_ID" > "$MAIN_SESSION_FILE"
  else
    MAIN_SESSION=$(cat "$MAIN_SESSION_FILE" 2>/dev/null)
    if [ "$SESSION_ID" != "$MAIN_SESSION" ]; then
      IS_AGENT=true
    fi
  fi
fi

# --- Render ---

if [ "$IS_AGENT" = true ]; then
  # Lightweight agent status line
  MODEL=$(echo "$INPUT" | jq -r '.model.display_name // "?"' 2>/dev/null)
  COST=$(echo "$INPUT" | jq -r '.cost.total_cost_usd // 0' 2>/dev/null)
  CTX_SIZE=$(echo "$INPUT" | jq -r '.context_window.context_window_size // 0' 2>/dev/null)
  CTX_USED=$(echo "$INPUT" | jq -r '.context_window.used_percentage // 0' 2>/dev/null)
  WT_BRANCH=$(echo "$INPUT" | jq -r '.worktree.branch // empty' 2>/dev/null)

  COST_FMT=$(printf '$%.2f' "$COST" 2>/dev/null || echo '$0.00')
  CTX_PCT="${CTX_USED:-0}"

  LABEL="${AGENT_TYPE:-agent}"
  [ -n "$AGENT_ID" ] && LABEL="${AGENT_ID}"

  LINE="${LABEL} | ${MODEL} | ctx:${CTX_PCT}% | ${COST_FMT}"
  [ -n "$WT_BRANCH" ] && LINE="${LINE} | ${WT_BRANCH}"

  echo "$LINE"
else
  # Full HUD for main session
  echo "$INPUT" | $FULL_HUD_CMD
fi
