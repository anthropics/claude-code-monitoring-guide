#!/bin/bash
# Debug hook to see exactly what data PostToolUse receives

echo "[DEBUG] PostToolUse Hook Fired at $(date)" >> ".claude/debug.log"
echo "[DEBUG] Arguments received:" >> ".claude/debug.log"
echo "[DEBUG] \$0 = $0" >> ".claude/debug.log"
echo "[DEBUG] \$1 = $1" >> ".claude/debug.log" 
echo "[DEBUG] \$2 = $2" >> ".claude/debug.log"
echo "[DEBUG] \$3 = $3" >> ".claude/debug.log"
echo "[DEBUG] All args: $@" >> ".claude/debug.log"
echo "[DEBUG] Environment variables:" >> ".claude/debug.log"
echo "[DEBUG] CLAUDE_FILE_PATHS = $CLAUDE_FILE_PATHS" >> ".claude/debug.log"
echo "[DEBUG] CLAUDE_TOOL_OUTPUT = $CLAUDE_TOOL_OUTPUT" >> ".claude/debug.log"
echo "[DEBUG] CLAUDE_TOOL_NAME = $CLAUDE_TOOL_NAME" >> ".claude/debug.log"
echo "[DEBUG] PWD = $PWD" >> ".claude/debug.log"
echo "[DEBUG] ---" >> ".claude/debug.log"

exit 0