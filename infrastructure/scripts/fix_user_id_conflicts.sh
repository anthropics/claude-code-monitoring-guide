#!/bin/bash

# Fix user_id conflicts by identifying active Claude sessions and old processes

echo "🔍 CLAUDE CODE USER ID CONFLICT RESOLVER"
echo "========================================"
echo ""

# Check running Claude processes
echo "🚀 ACTIVE CLAUDE CODE SESSIONS:"
CLAUDE_PROCESSES=$(ps aux | grep -E "^\w+\s+\d+.*claude\s*$" | grep -v grep)

if [[ -n "$CLAUDE_PROCESSES" ]]; then
    echo "$CLAUDE_PROCESSES" | while read line; do
        PID=$(echo "$line" | awk '{print $2}')
        START_TIME=$(echo "$line" | awk '{print $9}')
        TERMINAL=$(echo "$line" | awk '{print $7}')
        echo "   • PID: $PID | Started: $START_TIME | Terminal: $TERMINAL"
    done
    
    CLAUDE_COUNT=$(echo "$CLAUDE_PROCESSES" | wc -l | xargs)
    echo "   Total Claude sessions: $CLAUDE_COUNT"
else
    echo "   No active Claude sessions found"
fi

echo ""

# Check for old monitoring daemons
echo "🤖 OLD MONITORING DAEMONS:"
DAEMON_PROCESSES=$(ps aux | grep -E "(claude-developer-metrics|claude-session-extractor)" | grep -v grep)

if [[ -n "$DAEMON_PROCESSES" ]]; then
    echo "$DAEMON_PROCESSES" | while read line; do
        PID=$(echo "$line" | awk '{print $2}')
        SCRIPT=$(echo "$line" | awk '{print $11}' | xargs basename)
        echo "   • PID: $PID | Script: $SCRIPT"
    done
    echo "   ⚠️  These may be generating metrics with old user_id logic"
else
    echo "   No old daemon processes found"
fi

echo ""

# Show current user_id configuration
echo "⚙️  CURRENT CONFIGURATION:"
echo "   User_id script: get_claude_user_id_simple.sh (session-based correlation)"
echo "   System username: $(whoami)"
echo "   Hook path in settings: $(grep -o '"[^"]*production-tool-hook.sh"' ~/.claude/settings.json 2>/dev/null | tr -d '"' || echo "Not found")"

echo ""

# Show metrics breakdown
echo "📊 CURRENT METRICS BREAKDOWN:"
curl -s "http://localhost:7100/api/v1/query?query=count%20by%20(user_id,job)(claude_code_cost_usage_USD_total)" 2>/dev/null | \
jq -r '.data.result[] | "\(.metric.user_id) (\(.metric.job)): \(.value[1])"' 2>/dev/null | \
while read line; do
    echo "   $line metrics"
done

echo ""
echo "💡 SOLUTIONS:"
echo "   1. MAIN FIX: Session-based correlation (get_claude_user_id_simple.sh)"
echo "      • Uses session_id to correlate hook data with real telemetry"
echo "      • No hardcoded user data - works generically for any team member"
echo ""
echo "   2. To fix conflicting user_ids from active sessions:"
echo "      • Close all other Claude Code windows/terminals" 
echo "      • They will restart with the updated hook configuration"
echo ""
echo "   3. To kill old monitoring daemons (if any):"
if [[ -n "$DAEMON_PROCESSES" ]]; then
    echo "$DAEMON_PROCESSES" | while read line; do
        PID=$(echo "$line" | awk '{print $2}')
        echo "      kill $PID"
    done
else
    echo "      No daemons to kill"
fi
echo ""
echo "   4. To see live metrics as they're generated:"
echo "      • Watch: curl -s http://localhost:7101/metrics | grep claude_code_cost_usage"
echo "      • All new metrics should consistently use hashed user_id (no more username fallbacks)"
echo ""
echo "🎯 EXPECTED RESULT:"
echo "   • Dashboard shows 1 user (hook metrics use same user_id as real telemetry)"
echo "   • All new metrics use consistent hashed user_id via session correlation"
echo "   • Generic solution works for entire team without hardcoding"