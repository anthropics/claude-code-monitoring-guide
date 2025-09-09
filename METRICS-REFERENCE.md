# Muninn Metrics Reference

## Platform Overview

**Muninn** is a universal AI tool observability platform. This reference documents the **Claude Code adapter** metrics - the first implementation of Muninn's extensible monitoring system.

**Future Vision**: Additional adapters for GitHub Copilot, OpenAI API, Cursor, and custom AI tools will add their own metric namespaces to this universal platform.

## 🔑 Breakthrough Innovation: Timestamp-Based Counter System

**What Makes This Work**: Each metric includes a millisecond timestamp to ensure proper counter accumulation across all AI tool adapters.

**The Problem We Solved**: Standard Pushgateway metrics overwrite each other (1→1→1) instead of accumulating (33→37→42).

**Universal Solution**: 
```python
timestamp_id = int(time.time() * 1000)  # millisecond timestamp for uniqueness
url = f'{pushgateway_url}/metrics/job/claude_code_tools/.../ts/{timestamp_id}'
```
*This pattern will be used by all Muninn adapters for consistent time-series data.*

## 📊 Claude Code Adapter Metrics (Production Ready)

### 4 Production Dashboard Categories

The Claude Code adapter captures real usage via hook-based monitoring:

- ✅ **Real-Time**: Every tool use captured instantly
- 📊 **4 Working Dashboards**: Tools, Bash Commands, Agents, MCP  
- 🔧 **Actual Data**: No estimates - real usage counts with proper time-series
- 🔌 **Extensible**: Pattern established for future AI tool adapters

### Official OpenTelemetry Metrics (Reference)

Claude Code can emit official metrics when `CLAUDE_CODE_ENABLE_TELEMETRY=1` is set:

- 🏢 **Official**: Direct from Claude Code telemetry
- 📈 **Precise**: Exact cost, token, and session data
- 🔒 **Enterprise**: May require specific Claude Code plans

---

## Claude Code Adapter Metrics (WORKING NOW)

The Claude Code adapter's production-tool-hook.sh generates these metrics for all 4 dashboards:

### 🔧 Tool Usage Metrics
- **`claude_custom_tool_usage_total`**: Every Read, Write, Edit, Bash, Task, MCP tool use
- **Labels**: session_id, user, tool, operation_type, file_extension

### 💻 Bash Command Metrics  
- **`claude_custom_bash_commands_total`**: Every bash command (git, curl, just, etc.)
- **`claude_custom_just_subcommands_total`**: Just subcommands (status, help, etc.)
- **Labels**: session_id, user, bash_command, just_subcommand

### 🤖 Agent Metrics
- **`claude_custom_agent_usage_total`**: Task tool usage by agent type  
- **`claude_custom_agent_tasks_by_type_total`**: Task categorization
- **`claude_custom_agent_prompt_length_total`**: Prompt length tracking
- **Labels**: session_id, user, agent_type, task_category

### 🔌 MCP Metrics
- **All MCP tools captured via standard tool tracking** (tools starting with `mcp__*`)
- **Current servers**: context7 (8 uses), linear (1 use)
- **Labels**: Same as tool usage metrics

**View Raw Metrics**: http://localhost:7101/metrics

### Cost Metrics

#### `claude_code_cost_usage_USD_total`
- **Type**: Counter
- **Unit**: USD (estimated)
- **Description**: Estimated cost per tool use ($0.001 per tool)
- **Labels**:
  - `model`: Model used (default: "sonnet")
  - `session_id`: Claude Code session identifier
  - `user_id`: Username
  - `tool`: Tool that was used (Read, Write, Bash, etc.)
  - `instance`: Hostname
  - `job`: "claude_code_tools"

**Example Queries**:
```promql
# Total estimated cost
sum(claude_code_cost_usage_USD_total)

# Cost by model
sum by (model) (claude_code_cost_usage_USD_total)

# Cost by user  
sum by (user_id) (claude_code_cost_usage_USD_total)

# Cost by tool
sum by (tool) (claude_code_cost_usage_USD_total)
```

### Token Metrics

#### `claude_code_token_usage_tokens_total`
- **Type**: Counter
- **Unit**: Tokens (estimated)
- **Description**: Estimated token usage per tool (100-800 tokens per tool)
- **Labels**:
  - `type`: Token type (currently only "input")
  - `model`: Model used (default: "sonnet")
  - `session_id`: Claude Code session identifier
  - `user_id`: Username
  - `instance`: Hostname
  - `job`: "claude_code_tools"

**Token Estimates by Tool**:
- Read: 500 tokens
- Write: 800 tokens  
- Edit: 300 tokens
- Bash: 200 tokens
- Grep/Glob: 150 tokens
- Other: 100 tokens

**Example Queries**:
```promql
# Total estimated tokens
sum(claude_code_token_usage_tokens_total)

# Tokens by user
sum by (user_id) (claude_code_token_usage_tokens_total)

# Average tokens per tool use
sum(claude_code_token_usage_tokens_total) / count(claude_code_cost_usage_USD_total)
```

### Session Metrics

#### `claude_code_session_count_total`
- **Type**: Counter
- **Description**: Number of Claude Code sessions
- **Labels**: Standard labels

#### `claude_code_active_sessions`
- **Type**: Gauge
- **Description**: Currently active sessions
- **Labels**: Standard labels

#### `claude_code_active_time_seconds_total`
- **Type**: Counter
- **Unit**: Seconds
- **Description**: Total time spent in active sessions

### Code Generation Metrics

#### `claude_code_lines_of_code_count_total`
- **Type**: Counter
- **Unit**: Lines (estimated)
- **Description**: Estimated lines of code modified/created per file operation
- **Labels**:
  - `type`: Operation type (write, edit, etc.)
  - `file_extension`: File extension (py, js, md, etc.)
  - `session_id`: Claude Code session identifier
  - `user_id`: Username
  - `instance`: Hostname
  - `job`: "claude_code_tools"

**LOC Estimates by Operation**:
- Write (new file): 50 lines
- Edit/MultiEdit: 10 lines

**Example Queries**:
```promql
# Total estimated LOC
sum(claude_code_lines_of_code_count_total)

# LOC by file type
sum by (file_extension) (claude_code_lines_of_code_count_total)

# LOC by operation type
sum by (type) (claude_code_lines_of_code_count_total)
```

### Custom Tracking Metrics

These metrics provide detailed tool usage tracking:

#### `claude_custom_tool_usage_total`
- **Type**: Counter  
- **Description**: Each Claude Code tool use (1 per tool invocation)
- **Labels**: `session_id`, `user`, `tool`, `operation_type`, `file_extension`

#### `claude_custom_bash_commands_total`
- **Type**: Counter
- **Description**: Bash command tracking with command breakdown
- **Labels**: `session_id`, `user`, `bash_command`

#### `claude_custom_action_total`
- **Type**: Counter
- **Description**: Session start/end and custom actions
- **Labels**: `action`, `session_id`, `user`

**Example Queries**:
```promql
# Tool usage breakdown
sum by (tool) (claude_custom_tool_usage_total)

# Most used bash commands  
sum by (bash_command) (claude_custom_bash_commands_total)

# Session activity
sum by (action) (claude_custom_action_total)
```

---

## Official OpenTelemetry Metrics (Reference)

#### `claude_code_code_edit_tool_decision_total`
- **Type**: Counter
- **Description**: Count of code editing tool decisions made
- **Labels**: Standard labels

#### `claude_code_edits_made`
- **Type**: Gauge
- **Description**: Number of code edits made in session
- **Labels**: Standard labels

### Other Metrics

#### `claude_code_commit_count_total`
- **Type**: Counter
- **Description**: Number of git commits created
- **Labels**: Standard labels

#### `claude_code_last_update_timestamp`
- **Type**: Gauge
- **Unit**: Unix timestamp
- **Description**: Last time metrics were updated

## 🏷️ Standard Labels

All metrics include these labels:
- `session_id`: Unique session identifier
- `user_id`: Hashed user identifier  
- `user_email`: User's email address
- `user_account_uuid`: Account UUID
- `organization_id`: Organization UUID
- `terminal_type`: Terminal application (e.g., `WarpTerminal`)
- `model`: Claude model used
- `otel_scope_name`: Always `com.anthropic.claude_code`
- `otel_scope_version`: Claude Code version (e.g., `1.0.90`)

## 📈 Useful Queries

### Cost Analysis
```promql
# Total cost today
increase(sum(claude_code_cost_usage_USD_total)[1d])

# Cost per hour average
rate(sum(claude_code_cost_usage_USD_total)[1h]) * 3600

# Most expensive model
topk(1, sum by (model) (claude_code_cost_usage_USD_total))
```

### Token Efficiency
```promql
# Tokens per dollar
sum(claude_code_token_usage_tokens_total) / sum(claude_code_cost_usage_USD_total)

# Cache hit rate
sum(claude_code_token_usage_tokens_total{type="cacheRead"}) / 
(sum(claude_code_token_usage_tokens_total{type="cacheRead"}) + 
 sum(claude_code_token_usage_tokens_total{type="input"}))
```

### Productivity
```promql
# Lines of code per session
claude_code_lines_of_code_count_total / claude_code_session_count_total

# Average session duration
rate(claude_code_active_time_seconds_total[1h]) / rate(claude_code_session_count_total[1h])
```

## ❌ What's NOT Available

These are **NOT** available in OTEL metrics:
- **Linear ticket IDs** - Not tracked by Claude Code
- **Git branch/commit info** - Not included in telemetry
- **File paths** - Privacy: specific files aren't tracked
- **Code content** - Privacy: actual code isn't sent
- **Tool-specific metrics** - Read/Write/Edit tools aren't individually tracked
- **Error messages** - Errors aren't exposed in metrics
- **Custom metadata** - Can't add your own labels

## 🔧 Extending Muninn Metrics

### Claude Code Adapter
**No**, you cannot add custom metrics to Claude Code's official telemetry. The metrics are emitted directly by Claude Code's internal instrumentation and cannot be extended.

### Universal Platform Options
What you CAN do with Muninn:
- **Process existing metrics** - Create derived metrics in Prometheus
- **Add recording rules** - Pre-calculate complex queries  
- **Build custom exporters** - Read from other sources and correlate
- **Use metric relabeling** - Transform labels in Prometheus
- **Create new adapters** - Build adapters for other AI tools following the Claude pattern

Example recording rule in `prometheus.yml`:
```yaml
groups:
  - name: claude_derived
    interval: 30s
    rules:
      - record: claude:cost_per_hour
        expr: rate(sum(claude_code_cost_usage_USD_total)[1h]) * 3600
      
      - record: claude:tokens_per_dollar
        expr: sum(rate(claude_code_token_usage_tokens_total[5m])) / sum(rate(claude_code_cost_usage_USD_total[5m]))
      
      - record: claude:cache_hit_rate
        expr: |
          sum(claude_code_token_usage_tokens_total{type="cacheRead"}) / 
          sum(claude_code_token_usage_tokens_total{type=~"cacheRead|input"})
```

## 📊 Complete Metrics List

```bash
# Get current list from your Prometheus:
curl -s "http://localhost:7100/api/v1/label/__name__/values" | \
  jq -r '.data[] | select(startswith("claude_code_"))'
```

Current metrics (as of v1.0.90):
1. `claude_code_active_sessions`
2. `claude_code_active_time_seconds_total`
3. `claude_code_code_edit_tool_decision_total`
4. `claude_code_commit_count_total`
5. `claude_code_cost_usage_USD_total`
6. `claude_code_edits_made`
7. `claude_code_last_update_timestamp`
8. `claude_code_lines_of_code_count_total`
9. `claude_code_session_count_total`
10. `claude_code_token_usage_tokens_total`

## 🚀 Getting Started with Muninn

**⚠️ Important**: All commands must be run from the `infrastructure/` directory.

**Option 1: Claude Code Adapter Hook-Based Monitoring (Recommended)**

1. **Setup Muninn platform**:
   ```bash
   # Navigate to infrastructure directory
   cd infrastructure
   
   # Complete setup with health checks
   just setup
   ```

2. **Deploy Claude Code adapter hooks**:
   ```bash  
   # Install Claude Code adapter hooks for current user
   just deploy hooks
   ```

3. **Use Claude Code normally** - metrics are captured automatically by the adapter

4. **View Claude adapter dashboards**:
   ```bash
   # Open Grafana dashboards
   just service console grafana
   ```

**Option 2: Official Claude Code OpenTelemetry (Advanced)**

1. **Enable Claude Code telemetry**:
   ```bash
   export CLAUDE_CODE_ENABLE_TELEMETRY=1
   export OTEL_METRICS_EXPORTER=otlp
   export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:7110
   ```

2. **Start Muninn services**:
   ```bash
   # From infrastructure/ directory
   just up
   ```

3. **Query Claude Code metrics**:
   ```bash
   # Check total cost
   curl -s "http://localhost:7100/api/v1/query?query=sum(claude_code_cost_usage_USD_total)" | jq
   
   # Or use Muninn helper commands
   just test all
   just monitor validate
   ```

## 📝 Notes

- Metrics are emitted every 30 seconds (configurable via `OTEL_METRIC_EXPORT_INTERVAL`)
- All costs are in USD
- Token counts are estimates
- Lines of code is a rough approximation
- Cache tokens are "free" but still counted
- Session IDs are unique per Claude invocation