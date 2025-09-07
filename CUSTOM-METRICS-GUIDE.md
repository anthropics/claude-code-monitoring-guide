# Custom Metrics for Claude Code - Complete Guide

## 🎯 YES, You Can Add Your Own Metrics!

While you can't modify Claude Code's built-in telemetry, you **CAN** create your own metrics stream that:
- Uses the same OTEL Collector / Prometheus / Grafana stack
- Correlates with Claude's metrics via session IDs
- Tracks whatever you want (compactions, Linear tickets, file operations, etc.)

## 🏗️ Architecture

```
Claude Code → Built-in OTEL Metrics → ┐
                                       ├→ OTEL Collector → Prometheus → Grafana
Your Hooks  → Custom Metrics ─────────┘
```

## 🚀 Current Implementation

**Automatic Tool Tracking (Already Active)**

The repository includes `production-tool-hook.sh` that automatically captures every Claude Code tool use:

- ✅ **Auto-installed**: Run `just deploy hooks` to install
- 📊 **Dashboard Ready**: Generates metrics for both stock and custom dashboards  
- 🔄 **No Manual Work**: Captures Read, Write, Edit, Bash, etc. automatically

**Metrics Generated**:
- `claude_code_cost_usage_USD_total` - Estimated costs
- `claude_code_token_usage_tokens_total` - Estimated token usage
- `claude_code_lines_of_code_count_total` - Lines of code metrics
- `claude_custom_tool_usage_total` - Detailed tool usage tracking

**View Current Metrics**:
```bash
# Check what's being captured
curl -s http://localhost:7101/metrics | grep claude

# Test the hooks
just test hooks

# View in dashboards  
just service console grafana
```

---

## 🛠️ Adding Custom Metrics

### Option 1: Simple Bash Script (Manual Tracking)

We've created `send-custom-metric.sh` that sends metrics directly to Prometheus Pushgateway:

```bash
# Test it works
./hooks/send-custom-metric.sh test

# Track a compaction
./hooks/send-custom-metric.sh compact

# Track a Linear ticket
./hooks/send-custom-metric.sh linear 'ENG-123'

# Track file operation
./hooks/send-custom-metric.sh file 'edit' 'main.py'
```

### Option 2: Python with Full OTEL (More Powerful)

Use `custom-metrics-sender.py` for richer metrics with OpenTelemetry:

```bash
# Install dependencies (one time)
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc

# Use it
python custom-metrics-sender.py compact
python custom-metrics-sender.py action 'file_save'
python custom-metrics-sender.py timing 'build' 45.2
```

## 🪝 Hooking Into Claude Events

### Available Hook Points

Claude Code supports these hooks (check with `/doctor`):
- `PreToolUse` - Before tool execution  
- `PostToolUse` - After tool execution
- `Compact` - When conversation is compacted
- `ToolUse` - When tools are used (Edit, Write, etc.)

### Example: Track Compactions

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Compact": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/send-custom-metric.sh compact"
          }
        ]
      }
    ]
  }
}
```

## 📊 Correlating with Claude's Metrics

### ✅ Direct Session Correlation (Current Implementation)
Our hooks now have **direct access** to `session_id` from Claude Code JSON data and use it to correlate with real telemetry:

**How it works:**
1. Claude Code hook receives JSON with `session_id` 
2. Hook calls `get_claude_user_id_simple.sh` with the `session_id`
3. Script queries metrics for real telemetry with matching `session_id`
4. Hook metrics use the same `user_id` as real Claude telemetry

**Direct Session Queries:**
   ```promql
   # All metrics for a specific session
   {session_id="bb6e40fd-c85d-414c-a26f-6c97e36bb384"}
   
   # Cost for a specific session across hook and real metrics
   claude_code_cost_usage_USD_total{session_id="bb6e40fd-c85d-414c-a26f-6c97e36bb384"}
   ```

### Alternative Correlation Methods (Legacy)
For custom metrics that don't have session_id access:

1. **Use Timestamp Correlation**
   ```promql
   # Find Claude metrics around the same time as your custom metric
   claude_code_cost_usage_USD_total 
     and on() 
   (claude_custom_compact_timestamp > time() - 60)
   ```

2. **Use User + Time Window**
   ```promql
   # Correlate by user and time window
   sum by (user) (
     increase(claude_code_cost_usage_USD_total[1h])
   ) 
   and 
   sum by (user) (
     increase(claude_custom_compact_total[1h])
   )
   ```

## 📈 Example Custom Metrics

### Compactions Per Day
```promql
# How many times each user compacted per day
sum by (user) (
  increase(claude_custom_compact_total[1d])
)
```

### Linear Ticket Costs (if tracking)
```promql
# Cost per Linear ticket (requires correlation)
sum by (ticket) (
  claude_custom_linear_work
) * 
(sum(claude_code_cost_usage_USD_total) / sum(claude_code_session_count_total))
```

### File Operations by Type
```promql
# Which file types are edited most
topk(10, 
  sum by (extension) (
    claude_custom_file_operations_total
  )
)
```

## 🎯 Ideas for Custom Metrics

### Development Workflow
- **Compactions**: `claude_custom_compact_total`
- **Test runs**: `claude_custom_test_run_total{status="pass|fail"}`
- **Builds triggered**: `claude_custom_build_total{result="success|failure"}`
- **Git operations**: `claude_custom_git_operations{operation="commit|push|pull"}`

### Project Tracking
- **Linear tickets**: `claude_custom_linear_work{ticket="ENG-123"}`
- **PRs created**: `claude_custom_pr_created{repo="main"}`
- **Features completed**: `claude_custom_feature_complete{feature="auth"}`

### Quality Metrics
- **Errors encountered**: `claude_custom_errors{type="syntax|runtime"}`
- **Refactoring sessions**: `claude_custom_refactor_total`
- **Code review iterations**: `claude_custom_review_iterations`

## 🔧 Advanced: Creating a Metric Aggregator

You could create a daemon that:
1. Watches Claude's SQLite database (if it gets updated)
2. Reads git history
3. Monitors file changes
4. Sends aggregated custom metrics

Example structure:
```bash
#!/bin/bash
# claude-metrics-aggregator.sh

while true; do
  # Check for new sessions
  SESSION_COUNT=$(some_check)
  
  # Check git commits
  COMMIT_COUNT=$(git rev-list --count HEAD)
  
  # Send metrics
  ./hooks/send-custom-metric.sh action "aggregate"
  
  sleep 60
done
```

## 🎨 Creating Custom Dashboards

Once you have custom metrics, create dashboards that combine them:

```json
{
  "panels": [
    {
      "title": "Compactions vs Cost",
      "targets": [
        {
          "expr": "sum(rate(claude_custom_compact_total[1h]))"
        },
        {
          "expr": "sum(rate(claude_code_cost_usage_USD_total[1h]))"
        }
      ]
    }
  ]
}
```

## ⚠️ Important Notes

1. **Don't break your status line** - Hooks can interfere with custom status lines
2. **Keep hooks fast** - Slow hooks will slow down Claude
3. **Handle errors gracefully** - Don't let metric sending break your workflow
4. **Consider batching** - Don't send metrics on every tiny event

## 🚦 Testing Your Setup

```bash
# 1. Send test metric
./hooks/send-custom-metric.sh test

# 2. Check it arrived at Pushgateway
curl -s http://localhost:7101/metrics | grep claude_custom

# 3. Query in Prometheus
curl -s "http://localhost:7100/api/v1/query?query=claude_custom_compact_total"

# 4. See in Grafana
# Add a panel with query: claude_custom_*
```

## 💡 The Power of This Approach

You now have:
- **Claude's built-in metrics** (cost, tokens, sessions)
- **Your custom metrics** (compactions, Linear tickets, etc.)
- **Same visualization** (all in Grafana)
- **Correlation possible** (via time, user, or custom session IDs)

This gives you the complete picture of your Claude Code usage!

## 🎯 Next Steps

1. Decide what you want to track
2. Add hooks to `~/.claude/settings.json`
3. Start collecting custom metrics
4. Build dashboards combining both metric streams
5. Get insights no one else has!

Remember: You're not modifying Claude's telemetry, you're **augmenting** it with your own data stream. This is powerful!