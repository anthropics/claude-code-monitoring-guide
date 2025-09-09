#!/bin/bash

# Simple user_id lookup using session_id correlation
# Gets user_id from real Claude telemetry using session_id from hook

SESSION_ID="$1"

if [[ -n "$SESSION_ID" ]]; then
    # Look up user_id by session_id in real telemetry
    USER_ID=$(curl -s "http://localhost:7112/metrics" 2>/dev/null | \
        grep "session_id=\"$SESSION_ID\"" | \
        grep -o 'user_id="[^"]*"' | \
        cut -d'"' -f2 | \
        head -1)
    
    if [[ -n "$USER_ID" ]]; then
        echo "$USER_ID"
        exit 0
    fi
fi

# Fallback: try to get any current user_id from telemetry
USER_ID=$(curl -s "http://localhost:7112/metrics" 2>/dev/null | \
    grep "claude_code.*user_id=" | \
    grep -o 'user_id="[^"]*"' | \
    cut -d'"' -f2 | \
    head -1)

if [[ -n "$USER_ID" ]]; then
    echo "$USER_ID"
else
    # Final fallback
    echo "$(whoami)"
fi