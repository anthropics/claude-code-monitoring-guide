#!/bin/bash

# Tool usage hook - Tracks tool usage events
# Can be used for Edit, Write, Bash, and other tools
# Receives tool name and file path (when applicable)

TOOL_NAME="${1:-unknown}"
FILE_PATH="${2:-}"

# Source session parsing functions
source "$(dirname "$0")/parse-session.sh"

# Get current session ID and parse components
SESSION_ID=$(get_session_id)
USER=$(get_user "$SESSION_ID")
DIR=$(get_directory "$SESSION_ID")
BRANCH=$(get_branch "$SESSION_ID")
TIME=$(get_timestamp "$SESSION_ID")

# Build metric with tool-specific data (run in background to not block)
if [[ -n "$FILE_PATH" ]]; then
  # For Edit/Write tools - include file extension
  FILE_EXT="${FILE_PATH##*.}"
  /Users/chadwalters/source/work/claude-code-monitoring-guide/send-custom-metric.sh tool_usage "$TOOL_NAME" "$FILE_EXT" "$SESSION_ID" &
else
  # For Bash and other tools - just tool name
  /Users/chadwalters/source/work/claude-code-monitoring-guide/send-custom-metric.sh tool_usage "$TOOL_NAME" "unknown" "$SESSION_ID" &
fi

# Log for debugging
echo "[$(date)] Tool used: $TOOL_NAME ($FILE_PATH) - $SESSION_ID" >> ".claude/session.log"