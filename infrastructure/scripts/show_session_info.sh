#!/bin/bash

# Show information about the current Claude Code session and user mapping

echo "🔍 Claude Code Session Information"
echo "=================================="
echo ""

# Current environment info
echo "📍 CURRENT ENVIRONMENT:"
echo "   User ID script: get_claude_user_id_simple.sh (session-based correlation)"
echo "   System username: $(whoami)"
echo "   Working directory: $(pwd)"
echo ""

# Check hook configuration
echo "🪝 HOOK CONFIGURATION:"
if [[ -f ~/.claude/settings.json ]]; then
    echo "   Claude settings found: ~/.claude/settings.json"
    if grep -q "production-tool-hook.sh" ~/.claude/settings.json; then
        echo "   ✅ Production hook installed"
        HOOK_PATH=$(grep -o '"[^"]*production-tool-hook.sh"' ~/.claude/settings.json | tr -d '"')
        echo "   Hook path: $HOOK_PATH"
    else
        echo "   ❌ Production hook not found in settings"
    fi
else
    echo "   ❌ No Claude settings file found"
fi
echo ""

# Active sessions from metrics
echo "📊 ACTIVE SESSIONS FROM METRICS:"
echo "   Prometheus endpoint: http://localhost:7100"
echo ""

# Query recent sessions and their user mappings
curl -s "http://localhost:7100/api/v1/query?query=claude_code_cost_usage_USD_total" 2>/dev/null | \
jq -r '.data.result[] | "\(.metric.session_id) | \(.metric.user_id) | \(.metric.job) | \(.metric.tool // "N/A")"' 2>/dev/null | \
sort | uniq -c | sort -nr | head -10 | while read count session_user_job_tool; do
    session=$(echo "$session_user_job_tool" | cut -d'|' -f1 | xargs)
    user=$(echo "$session_user_job_tool" | cut -d'|' -f2 | xargs) 
    job=$(echo "$session_user_job_tool" | cut -d'|' -f3 | xargs)
    tool=$(echo "$session_user_job_tool" | cut -d'|' -f4 | xargs)
    
    if [[ ${#user} -gt 20 ]]; then
        user_display="${user:0:12}...${user: -8}"
    else
        user_display="$user"
    fi
    
    printf "   %2d × Session: %s | User: %-20s | Source: %-15s | Tool: %s\n" "$count" "${session:0:8}..." "$user_display" "$job" "$tool"
done

echo ""
echo "💡 INTERPRETATION:"
echo "   - 'claude_code_tools' = Hook metrics (our script)"
echo "   - 'otel-collector' = Real Claude Code telemetry"  
echo "   - 'chadwalters' = Old username-based user_id (legacy data)"
echo "   - 'Long hash' = Correct hashed user_id (all new metrics use this)"
echo ""
echo "✅ STATUS: Using session-based correlation (get_claude_user_id_simple.sh)"
echo "   • Hook uses session_id to find user_id from real telemetry"
echo "   • All metrics use same hashed user_id consistently"
echo "   • Generic solution works for any team member"