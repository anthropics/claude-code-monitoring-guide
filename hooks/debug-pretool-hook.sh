#!/bin/bash
# Debug hook to see exactly what data PreToolUse receives

echo "[DEBUG PRE] PreToolUse Hook Fired at $(date)" >> ".claude/debug.log"
echo "[DEBUG PRE] Arguments received:" >> ".claude/debug.log"
echo "[DEBUG PRE] \$0 = $0" >> ".claude/debug.log"
echo "[DEBUG PRE] \$1 = $1" >> ".claude/debug.log" 
echo "[DEBUG PRE] \$2 = $2" >> ".claude/debug.log"
echo "[DEBUG PRE] \$3 = $3" >> ".claude/debug.log"
echo "[DEBUG PRE] All args: $@" >> ".claude/debug.log"
echo "[DEBUG PRE] Environment variables:" >> ".claude/debug.log"
echo "[DEBUG PRE] CLAUDE_FILE_PATHS = $CLAUDE_FILE_PATHS" >> ".claude/debug.log"
echo "[DEBUG PRE] CLAUDE_TOOL_OUTPUT = $CLAUDE_TOOL_OUTPUT" >> ".claude/debug.log"
echo "[DEBUG PRE] CLAUDE_TOOL_NAME = $CLAUDE_TOOL_NAME" >> ".claude/debug.log"
echo "[DEBUG PRE] PWD = $PWD" >> ".claude/debug.log"
echo "[DEBUG PRE] ---" >> ".claude/debug.log"

exit 0