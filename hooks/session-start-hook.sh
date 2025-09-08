#!/bin/bash

# SessionStart hook - Creates project-local session correlation ID
# Format: user|directory|branch|timestamp

# Build session ID with pipe-delimited format for easy parsing
USER_NAME="$USER"
PROJ_DIR=$(basename "$PWD")
GIT_BRANCH=$(git branch --show-current 2>/dev/null || echo "no-git")
START_TIME=$(date +%s)

# Create pipe-delimited session ID
SESSION_ID="${USER_NAME}|${PROJ_DIR}|${GIT_BRANCH}|${START_TIME}"

# Create project .claude directory
mkdir -p ".claude"
echo "$SESSION_ID" > ".claude/.sessionid"

# Ensure .claude/ is gitignored
if [[ -f ".gitignore" ]]; then
  grep -q "^\.claude/$" ".gitignore" || echo ".claude/" >> ".gitignore"
elif [[ -d ".git" ]]; then
  echo ".claude/" > ".gitignore"
fi

# Send session start metric with session correlation (use absolute path, run in background)
/Users/chadwalters/source/work/claude-code-monitoring-guide/hooks/send-custom-metric.sh action session_start "$SESSION_ID" &

# Log for debugging
echo "[$(date)] Session started: $SESSION_ID" >> ".claude/session.log"