# Claude Code Monitoring Guide

A guide for collecting and visualizing telemetry data from Claude Code to monitor costs, efficiency, and anomalies.

[日本語](README_JA.md)

## Architecture

```
Claude Code
  │  (OTLP gRPC / localhost:4317)
  ▼
OpenTelemetry Collector
  ├─ metrics ──▶ Prometheus (:9090)
  ├─ logs    ──▶ Loki (:3100)
  └─ traces  ──▶ Tempo (:3200)
                    ▲
                Grafana (:3000) ─ unified visualization across all data sources
                    │
                    └─ lifecycle ──▶ DuckDB API (:8082)

Claude Code Hooks (lifecycle-logger.sh)
  └─ events.jsonl ──▶ DuckDB API (:8082) ──▶ Grafana Infinity DS
```

Claude Code attaches a `prompt.id` (UUID v4) to every event. This ID is the key to tracing the entire processing flow from `user_prompt → api_request → tool_result`.

## Prerequisites

- Docker / Docker Compose
- Claude Code installed

## Setup

### 1. Start the Monitoring Stack

```bash
git clone https://github.com/samuraikun/claude-code-monitoring-guide
cd claude-code-monitoring-guide
docker compose up -d
```

Services started:

| Service | Port | Role |
|---|---|---|
| OpenTelemetry Collector | 4317 (gRPC), 4318 (HTTP) | Receives and forwards telemetry |
| Prometheus | 9090 | Metrics storage |
| Loki | 3100 | Log/event storage |
| Tempo | 3200 | Trace storage |
| Grafana | 3000 | Visualization (admin/admin) |
| DuckDB API | 8082 | Lifecycle event storage & query (Go + DuckDB) |

### 2. Configure Claude Code Telemetry

When you launch `claude` in this repository, telemetry is automatically enabled via `.claude/settings.json`.

```json
{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "CLAUDE_CODE_ENHANCED_TELEMETRY_BETA": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
    "OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE": "cumulative"
  }
}
```

To use this in other repositories, add the same configuration to `~/.claude/settings.json` (global settings).

### 3. Verify

```bash
# Start Claude Code and do some work
claude

# Check if data is arriving at Loki
curl -s http://localhost:3100/loki/api/v1/labels | jq .

# View logs in Grafana: http://localhost:3000
# Explore → Loki → {service_name="claude-code"}
```

## Grafana Dashboards

After starting Grafana, navigate to `http://localhost:3000` and the following dashboards will be automatically provisioned in the **Claude Code** folder.

---

### Prompt Timeline

**UID**: `claude-code-prompt-timeline`

A trace-equivalent view showing all events for a single prompt in chronological order.

**How to use**:
1. Copy a `prompt_id` from the "Recent Prompts" panel
2. Paste it into the "Prompt ID" input at the top
3. Review the `user_prompt → api_request → tool_result` flow

**Panels**:

| Panel | Type | Description |
|---|---|---|
| Recent Prompts | Logs | List of recent prompts. Copy prompt_id from here |
| Prompt Event Timeline | Logs | All events for the selected prompt_id in chronological order |
| API Requests for Prompt | Table | Model, cost, token count, latency |
| Tool Executions for Prompt | Table | Tool name, success/failure, duration, result size |

---

### Session Timeline

**UID**: `claude-code-session-timeline`

Drill-down view for a specific session, showing all events, prompts, and tool usage within the session.

**How to use**:
1. Copy a `session_id` from the "Recent Sessions" panel
2. Paste it into the "Session ID" input at the top
3. Review all prompts, costs, and tool usage within the session

**Panels**:

| Panel | Type | Description |
|---|---|---|
| Recent Sessions | Table | List of recent sessions with prompt counts and costs |
| Session Event Stream | Logs | All events for the selected session_id in chronological order |
| Prompts in Session — Turn Count | Table | Per-prompt turn counts within the session |
| Prompts in Session — Cost | Table | Per-prompt costs within the session |
| Tool Usage in Session | Bar chart | Tool usage distribution within the session |
| Cache Performance in Session | Time series | Cache read vs creation tokens within the session |

---

### Developer Efficiency

**UID**: `claude-code-dev-efficiency`

Dashboard for understanding tool usage patterns, costs, cache efficiency, and model performance.

**Panels**:

| Panel | Type | Description |
|---|---|---|
| Tool Usage Distribution | Bar chart | Total executions per tool. High Bash ratio may indicate vague prompts |
| Bash vs Total Tool Executions | Time series | Ratio of Bash to total tool executions over time |
| Top 10 Sessions by Cost | Table | Highest-cost sessions (USD) |
| Top 10 Prompts by Turn Count | Table | Highest turn-count prompts. Over 10 may indicate loops or inefficiency |
| Cache Performance | Time series | Cache Read (green) vs Cache Creation (orange). More green = more efficient |
| Prompt Activity Over Time | Time series | Number of prompts over time (usage frequency patterns) |
| Token Usage by Model | Time series | Token consumption by model over time |
| Code Edit Approvals by Language | Bar chart | Code edit approvals by programming language |
| Code Edit Decisions by Source | Bar chart | Breakdown of edit decisions: config (auto-approve) vs user actions |
| Fast Mode Usage Rate | Stat | Percentage of API requests using Fast Mode |
| Model Cost Efficiency (Output Tokens / $) | Time series | Output tokens per dollar by model — higher is more efficient |
| Tool Success Rate Trend by Tool | Time series | Success rate over time per tool for reliability tracking |

---

### Anomaly & Health

**UID**: `claude-code-anomaly-health`

Dashboard for anomaly detection and health monitoring.

**Panels**:

| Panel | Type | Description |
|---|---|---|
| Tool Failure Rate | Time series | Tool failure count over time. Consecutive failures are a sign of needed intervention |
| API Request Duration (p50/p95) | Time series | p95 over 30s may indicate API delays or stuck processes |
| Loop Detection — High Turn Count | Table | Top 20 prompts by turn count. Over 10 requires review |
| Large Tool Results (> 100KB) | Logs | Detects unintended large data reads |
| Tool Failure Count by Tool Name | Table | Failure count per tool |
| Max Tool Result Size by Tool | Table | Maximum output size per tool |
| API Errors by Status Code | Bar chart | API error counts by HTTP status code (429, 500, etc.) |
| High Retry Prompts (Top 10) | Table | Prompts with the most retry attempts |
| Tool Decision Rate (Accept vs Reject) | Time series | Tool execution approval/rejection rate over time |
| API Request Duration (p99/p95) | Time series | P99 latency — large gap with p95 indicates specific request bottlenecks |
| Rate Limit & Server Error Frequency | Time series | 429 (rate limit), 500 (server error), 529 (overloaded) trends over time |
| Average Retry Attempts | Stat | Average retry count on API errors. 3+ indicates capacity issues |
| Tool Rejections by Source | Bar chart | Breakdown of tool rejections by source (config, user_reject, etc.) |

---

### Working Dashboard

**UID**: `claude-code-working`

General-purpose dashboard showing basic metrics such as cost, tokens, session count, and key KPIs.

**Panels**:

| Panel | Type | Description |
|---|---|---|
| Total Cost / Active Users / Total Tokens / Lines of Code | Stat | Top-level KPI cards |
| Cost by Model | Pie chart | Cost breakdown by model |
| Token Usage by Type | Pie chart | Token breakdown (input, output, cacheRead, cacheCreation) |
| Cost by User / Lines of Code by Type | Table | Per-user costs, LOC by type (added/removed) |
| Active Time (Total) / Active Time by Type | Stat + Pie | Total and breakdown of active time |
| Cost by Organization | Table | Per-organization costs |
| Tool Results / API Errors | Logs | Raw log panels for tool results and API errors |
| Sessions / Commits / Pull Requests | Stat | Session and output count KPIs |
| Cost per Commit | Stat | AI cost per git commit — core ROI metric |
| DAU (Daily Active Users) | Stat | Unique users with sessions in the last 24h |
| Cache Hit Rate | Stat | cache_read_tokens / (input_tokens + cache_read_tokens) |

---

### ROI & Productivity

**UID**: `claude-code-roi-productivity`

Dashboard for measuring return on investment and developer productivity.

**Panels**:

| Panel | Type | Description |
|---|---|---|
| Cost per Commit | Stat | AI cost per commit — core ROI metric |
| Cost per PR | Stat | AI cost per pull request |
| Cost per LOC (Added) | Stat | AI cost per line of code added |
| LOC per Session | Stat | Lines of code per session — productivity indicator |
| Commits per Session | Stat | Commits per session — output indicator |
| User Wait Time Ratio | Stat | CLI processing time / total active time — measures AI wait time |
| Cache Hit Rate | Stat | Cache read tokens as a percentage of total input |
| Estimated Cache Savings | Stat | Estimated cost savings from cache hits |
| Cache Hit Rate Trend | Time series | Cache hit rate over time |
| Cache Hit Rate by Model | Bar chart | Cache efficiency comparison across models |
| Cost Efficiency Trend | Time series | Cost/Commit and Cost/PR trends over time |
| Lines of Code Trend by Type | Time series | LOC added/removed over time |
| User Productivity Summary | Table | Per-user cost, commits, and LOC comparison |

---

### Adoption & Usage Patterns

**UID**: `claude-code-adoption-usage`

Dashboard for tracking organizational adoption and usage patterns.

**Panels**:

| Panel | Type | Description |
|---|---|---|
| DAU / WAU / MAU | Stat | Daily, weekly, and monthly active users |
| Fast Mode Usage Rate | Stat | Percentage of API requests using Fast Mode |
| Model Usage Over Time | Time series | API request count by model over time |
| Sessions Over Time | Time series | Session count trends |
| Terminal / IDE Distribution | Pie chart | Session distribution by terminal type (VSCode, JetBrains, terminal, etc.) |
| Organization Cost Trend | Time series | Cost trends by organization |
| Fast Mode vs Normal Mode Over Time | Time series | Fast Mode adoption tracking |
| Prompt Activity Over Time | Time series | Prompt count trends for peak usage analysis |
| User Adoption Summary | Table | Per-user sessions, cost, and active time |

---

### Trace Explorer

**UID**: `claude-code-trace-explorer`

Dashboard for exploring Enhanced Telemetry Beta trace spans including TTFT, tool execution breakdown, and permission wait times. Requires `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`.

**Panels**:

| Panel | Type | Description |
|---|---|---|
| TTFT (Time to First Token) - P50/P95/P99 | Time series | Time to first token distribution for LLM requests |
| TTFT by Model | Bar chart | Average TTFT comparison across models |
| Tool Permission Wait Time (P50/P95) | Time series | Time spent waiting for user permission decisions |
| Permission Decision Distribution | Bar chart | Distribution of accept/reject/timeout decisions |
| Interaction Duration Breakdown | Time series (stacked) | LLM request vs tool execution vs permission wait |
| Tool Result Token Consumption | Bar chart | Token consumption by tool — identifies costly tools |
| Tool Execution Details | Table | Recent tool execution spans with duration/success/error |
| Recent Interaction Traces | Table | Recent interaction traces — click traceID for waterfall view |

---

### Lifecycle Observability

**UID**: `claude-code-lifecycle`

Dashboard for tracking which skills, commands, and agents are used per Claude Code session. Powered by DuckDB + Claude Code Hooks.

**How to use**:
1. View overview stats and usage breakdown across all sessions
2. Click a `session_id` in the Session List to drill down
3. Review the Session Event Timeline showing the full lifecycle

**Panels**:

| Panel | Type | Description |
|---|---|---|
| Total Sessions / Skill Invocations / Agent Spawns / Command Invocations / Unique Skills / Unique Agent Types | Stat | Overview KPI cards — filterable by session_id |
| Top Skills by Usage | Bar chart | Skill invocation count ranking (e.g., commit, review) |
| Command Distribution | Bar chart | Slash-command usage (detected from UserPromptSubmit) |
| Agent Types | Bar chart | Agent type spawn count (Explore, Plan, general-purpose) |
| Session List | Table | All sessions with model, prompt/skill/agent/command counts. Click session_id to drill down |
| Session Event Timeline | Table | All lifecycle events for a session in chronological order |

---

### Global Usage Tracking

**UID**: `claude-code-global-usage`

Dashboard for tracking cross-session skill, command, and agent usage trends across all Claude Code sessions. Includes model and project-level analysis.

**Panels**:

| Panel | Type | Description |
|---|---|---|
| Total Sessions / Skill Invocations / Agent Spawns / Commands / Unique Skills / Unique Agent Types | Stat | Global KPI cards (no session filter) |
| Daily Sessions / Daily Skill Invocations / Daily Agent Spawns | Time series (bar) | Usage trends over time |
| Top Skills / Top Commands / Top Agent Types | Bar chart | Cross-session usage rankings |
| Model Usage | Bar chart | Session count by LLM model |
| Top Projects | Table | Session/skill/agent counts per working directory |

## Trace Spans (Enhanced Telemetry Beta)

Requires `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`. These spans are sent to Tempo via OTLP.

| Span Name | Key Attributes |
|---|---|
| `claude_code.interaction` | Root span for a full user interaction (prompt to response) |
| `claude_code.llm_request` | LLM API call. `ttft_ms`, `model`, `input_tokens`, `output_tokens` |
| `claude_code.tool` | Tool invocation. `tool_name`, `result_tokens` |
| `claude_code.tool.execution` | Tool execution phase. `tool_name`, `success`, `error` |
| `claude_code.tool.blocked_on_user` | Permission wait. `decision` (accept/reject/timeout) |

## File Structure

```
.
├── docker-compose.yml              # Monitoring stack definition
├── otel-collector-config.yaml      # OTEL Collector configuration
├── prometheus.yml                  # Prometheus scrape configuration
├── tempo.yaml                      # Tempo configuration
├── .claude/
│   └── settings.json               # Claude Code telemetry settings (auto-enabled)
├── grafana/
│   ├── dashboards/
│   │   ├── prompt-timeline.json    # Prompt Timeline dashboard
│   │   ├── session-timeline.json   # Session Timeline dashboard
│   │   ├── developer-efficiency.json # Developer Efficiency dashboard
│   │   ├── anomaly-health.json     # Anomaly & Health dashboard
│   │   ├── working-dashboard.json  # Basic metrics dashboard
│   │   ├── roi-productivity.json   # ROI & Productivity dashboard
│   │   ├── adoption-usage.json     # Adoption & Usage Patterns dashboard
│   │   ├── trace-explorer.json    # Trace Explorer dashboard (Enhanced Telemetry Beta)
│   │   ├── lifecycle-observability.json # Lifecycle Observability dashboard (DuckDB + Hooks)
│   │   └── global-usage.json          # Global Usage Tracking dashboard (DuckDB)
│   └── provisioning/
│       ├── dashboards/
│       │   └── dashboards.yaml     # Dashboard auto-provisioning config
│       └── datasources/
│           └── datasources.yaml    # Data source config (Prometheus/Loki/Tempo/DuckDB)
├── duckdb-api/
│   ├── Dockerfile                  # Go multi-stage build
│   ├── main.go                     # HTTP server + API handlers
│   ├── db.go                       # DuckDB connection + JSONL importer
│   ├── schema.sql                  # DuckDB table definitions
│   └── go.mod / go.sum             # Go module dependencies
├── hooks/
│   └── lifecycle-logger.sh         # Hook script for lifecycle event capture
├── claude_code_roi_full.md         # Detailed ROI measurement guide
├── troubleshooting.md              # Troubleshooting
└── report-generation-prompt.md    # Automated report generation prompt template
```

## Key Metrics and Log Events

Claude Code sends the following events via OTLP:

| Event | Description |
|---|---|
| `user_prompt` | Prompt submission. Includes `prompt_id` / `session_id` / `prompt_length` |
| `api_request` | API request. Includes `model` / `cost_usd` / `duration_ms` / `input_tokens` / `output_tokens` / `cache_read_tokens` / `cache_creation_tokens` / `speed` |
| `tool_result` | Tool execution result. Includes `tool_name` / `success` / `duration_ms` / `tool_result_size_bytes` |
| `api_error` | API error. Includes `status_code` / `attempt` / `prompt_id` |
| `tool_decision` | Tool execution approval/rejection. Includes `decision` (accept/reject) / `source` (config/user_reject/etc.) |
| `system_prompt` | System prompt tracking. Includes `system_prompt_hash` / `system_prompt_length` |
| `hook_execution_complete` | Hook execution result. Includes `hook_name` / `num_success` / `num_blocking` |
| `feedback_survey` | Feedback survey (including compact conversation detection). Includes `survey_type` (`post_compact`) |

Basic Loki queries:

```logql
# View all events
{service_name="claude-code"} | json | drop __error__, __error_details__

# Trace events for a specific prompt_id
{service_name="claude-code"} | json | drop __error__, __error_details__ | prompt_id=`<your-prompt-id>`

# Filter only tool failures
{service_name="claude-code"} | json | drop __error__, __error_details__ | event_name=`tool_result` | success=`false`
```

## Troubleshooting

See [troubleshooting.md](troubleshooting.md) for details.

**Common issues**:

- **No data arriving at Loki**: Check that `OTEL_LOGS_EXPORTER=otlp` is set
- **Inaccurate Prometheus values**: `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=cumulative` is required
- **Telemetry not enabled**: Run `docker compose ps` to verify containers are running and `curl http://localhost:4317` to check the port is open

## Contributing

If you have improvements or additional use cases based on your implementation experience, please open an Issue or PR.

Original guide by [Kashyap Coimbatore Murali](https://www.linkedin.com/in/kashyap-murali/)
