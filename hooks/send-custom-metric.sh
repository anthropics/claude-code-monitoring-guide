#!/bin/bash

# Simple Custom Metric Sender for Claude Code
# Sends metrics directly to Prometheus Pushgateway (easier than OTEL)

PUSHGATEWAY_URL="http://localhost:7101/metrics"
JOB_NAME="claude_custom"
INSTANCE=$(hostname)

# Function to send a metric to Pushgateway
send_metric() {
    local metric_name=$1
    local metric_value=$2
    local metric_type=${3:-"gauge"}
    local labels=$4
    
    # Build the metric string
    local metric_data="# TYPE ${metric_name} ${metric_type}\n"
    
    if [ -n "$labels" ]; then
        metric_data+="${metric_name}{${labels}} ${metric_value}"
    else
        metric_data+="${metric_name} ${metric_value}"
    fi
    
    # Send to pushgateway
    echo -e "$metric_data" | curl -s --data-binary @- "${PUSHGATEWAY_URL}/job/${JOB_NAME}/instance/${INSTANCE}" >/dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "✅ Sent metric: ${metric_name}=${metric_value}"
    else
        echo "❌ Failed to send metric: ${metric_name}"
    fi
}

# Parse session ID if pipe-delimited format (user|directory|branch|timestamp)
parse_session_id() {
    local session_id="$1"
    if [[ "$session_id" == *"|"* ]]; then
        export PARSED_USER=$(echo "$session_id" | cut -d'|' -f1)
        export PARSED_DIR=$(echo "$session_id" | cut -d'|' -f2)
        export PARSED_BRANCH=$(echo "$session_id" | cut -d'|' -f3)
        export PARSED_TIME=$(echo "$session_id" | cut -d'|' -f4)
    else
        export PARSED_USER=${USER:-"unknown"}
        export PARSED_DIR="unknown"
        export PARSED_BRANCH="unknown"
        export PARSED_TIME=$(date +%s)
    fi
}

# Track compaction
track_compact() {
    local session_id=${2:-${CLAUDE_SESSION_ID:-"unknown"}}
    parse_session_id "$session_id"
    local timestamp=$(date +%s)
    
    # Build labels with session correlation
    local labels="session_id=\"$session_id\",user=\"$PARSED_USER\",directory=\"$PARSED_DIR\",branch=\"$PARSED_BRANCH\""
    
    # Increment compact counter
    send_metric "claude_custom_compact_total" "1" "counter" "$labels"
    
    # Also track as event with timestamp
    send_metric "claude_custom_compact_timestamp" "$timestamp" "gauge" "$labels"
}

# Track tool usage
track_tool_usage() {
    local tool_name="$2"
    local file_ext="$3"
    local session_id="$4"
    parse_session_id "$session_id"
    
    local tool_labels="tool=\"$tool_name\""
    if [[ -n "$file_ext" && "$file_ext" != "unknown" ]]; then
        tool_labels+=",file_extension=\"$file_ext\""
    fi
    
    local labels="session_id=\"$session_id\",user=\"$PARSED_USER\",directory=\"$PARSED_DIR\",branch=\"$PARSED_BRANCH\",$tool_labels"
    
    send_metric "claude_custom_tool_usage_total" "1" "counter" "$labels"
}

# Track custom action
track_action() {
    local action_type=$1
    local session_id=${CLAUDE_SESSION_ID:-"unknown"}
    local user=${USER:-"unknown"}
    
    send_metric "claude_custom_action_total" "1" "counter" "action=\"$action_type\",session_id=\"$session_id\",user=\"$user\""
}

# Track Linear ticket work
track_linear_ticket() {
    local ticket_id=$1
    local session_id=${CLAUDE_SESSION_ID:-"unknown"}
    local user=${USER:-"unknown"}
    
    send_metric "claude_custom_linear_work" "1" "counter" "ticket=\"$ticket_id\",session_id=\"$session_id\",user=\"$user\""
}

# Track file operations
track_file_op() {
    local operation=$1  # edit, create, delete
    local file_path=$2
    local session_id=${CLAUDE_SESSION_ID:-"unknown"}
    
    # Extract file extension
    local extension="${file_path##*.}"
    
    send_metric "claude_custom_file_operations_total" "1" "counter" "operation=\"$operation\",extension=\"$extension\",session_id=\"$session_id\""
}

# Track agent completion
track_agent_complete() {
    local complete_time="$2"
    local session_id="$3"
    parse_session_id "$session_id"
    
    local labels="session_id=\"$session_id\",user=\"$PARSED_USER\",directory=\"$PARSED_DIR\",branch=\"$PARSED_BRANCH\""
    
    # Track total agent completions
    send_metric "claude_custom_agent_complete_total" "1" "counter" "$labels"
    
    # Also track completion timestamp
    send_metric "claude_custom_agent_timestamp" "$complete_time" "gauge" "$labels"
}

# Main logic
case "${1:-}" in
    compact)
        track_compact "$@"
        ;;
    tool_usage)
        track_tool_usage "$@"
        ;;
    agent_complete)
        track_agent_complete "$@"
        ;;
    action)
        track_action "${2:-unknown}"
        ;;
    linear)
        track_linear_ticket "${2:-unknown}"
        ;;
    file)
        track_file_op "${2:-unknown}" "${3:-unknown}"
        ;;
    test)
        echo "Testing custom metrics..."
        track_compact
        track_action "test_action"
        track_linear_ticket "TEST-123"
        track_file_op "edit" "test.py"
        echo ""
        echo "Check metrics at: http://localhost:7101/metrics"
        echo "Or in Prometheus: http://localhost:7100/graph?g0.expr=claude_custom"
        ;;
    *)
        echo "Custom Metric Sender for Claude Code"
        echo ""
        echo "Usage: $0 {compact|tool_usage|action|linear|file|test} [args...]"
        echo ""
        echo "Examples:"
        echo "  $0 compact SESSION_ID                          # Track compaction with session correlation"
        echo "  $0 tool_usage TOOL_NAME FILE_EXT SESSION_ID    # Track tool usage (Edit, Write, Bash)"
        echo "  $0 action 'save_file'                          # Track custom action"
        echo "  $0 linear 'ENG-123'                            # Track Linear ticket work"
        echo "  $0 file 'edit' 'main.py'                       # Track file operation"
        echo "  $0 test                                         # Send test metrics"
        echo ""
        echo "Session ID Format: user|directory|branch|timestamp"
        echo "Example: 'chadwalters|myproject|main|1725653400'"
        exit 1
        ;;
esac