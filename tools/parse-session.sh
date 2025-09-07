#!/bin/bash

# Helper functions to parse pipe-delimited session ID
# Format: user|directory|branch|timestamp

get_session_id() {
    cat ".claude/.sessionid" 2>/dev/null || echo "unknown|unknown|unknown|0"
}

get_user() {
    echo "$1" | cut -d'|' -f1
}

get_directory() {
    echo "$1" | cut -d'|' -f2
}

get_branch() {
    echo "$1" | cut -d'|' -f3
}

get_timestamp() {
    echo "$1" | cut -d'|' -f4
}

# Example usage:
# SESSION_ID=$(get_session_id)
# USER=$(get_user "$SESSION_ID")
# DIR=$(get_directory "$SESSION_ID")
# BRANCH=$(get_branch "$SESSION_ID")
# TIME=$(get_timestamp "$SESSION_ID")