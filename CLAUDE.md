# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository is a monitoring guide for Claude Code telemetry. It provides a Docker Compose-based observability stack that collects, stores, and visualizes telemetry data from Claude Code sessions.

## Stack Management

```bash
# Start the monitoring stack
docker compose up -d

# Stop the stack
docker compose down

# View logs from the OTEL Collector
docker logs otel-collector

# Check container status
docker compose ps
```

## Architecture

```
Claude Code
  │  (OTLP gRPC / localhost:4317)
  ▼
OpenTelemetry Collector  (otel-collector-config.yaml)
  ├─ metrics ──▶ Prometheus (:9090)
  ├─ logs    ──▶ Loki (:3100)
  └─ traces  ──▶ Tempo (:3200)
                    ▲
                Grafana (:3000) — auto-provisioned dashboards
                    │
                    ├─ render ──▶ Image Renderer (:8081)
                    └─ lifecycle ──▶ DuckDB API (:8082)

Claude Code Hooks (lifecycle-logger.sh)
  └─ events.jsonl ──▶ DuckDB API (:8082) ──▶ Grafana Infinity DS
```

**Key data flow**: Claude Code attaches a `prompt_id` (UUID v4) to every event, enabling end-to-end tracing from `user_prompt → api_request → tool_result`.

## Telemetry Configuration

Telemetry is auto-enabled when running `claude` in this repo via `.claude/settings.json`. The critical env vars are:

- `CLAUDE_CODE_ENABLE_TELEMETRY=1` — enables telemetry export
- `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` — enables Enhanced Telemetry Beta (trace spans: TTFT, tool execution breakdown, permission wait time)
- `OTEL_LOGS_EXPORTER=otlp` — required for Loki event collection (tool_result, api_error, etc.)
- `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=cumulative` — required for correct Prometheus values; without this, delta values break `sum()` and `increase()` queries

To enable globally, copy the same config to `~/.claude/settings.json`.

## Grafana Dashboards

Access Grafana at `http://localhost:3000` (admin/admin). Dashboards are auto-provisioned from `grafana/dashboards/`:

| Dashboard | UID | Purpose |
|---|---|---|
| Prompt Timeline | `claude-code-prompt-timeline` | Trace all events for a single `prompt_id` |
| Session Timeline | `claude-code-session-timeline` | Drill down into a specific session |
| Developer Efficiency | `claude-code-dev-efficiency` | Tool usage, costs, cache hit rates, model cost efficiency |
| Anomaly & Health | `claude-code-anomaly-health` | Failure rates, loop detection, P99 latency, rate limits |
| Working Dashboard | `claude-code-working` | Basic cost/token/session metrics, DAU, cache hit rate |
| ROI & Productivity | `claude-code-roi-productivity` | Cost per commit/PR/LOC, cache efficiency, user productivity |
| Adoption & Usage Patterns | `claude-code-adoption-usage` | DAU/WAU/MAU, terminal/IDE distribution |
| Trace Explorer | `claude-code-trace-explorer` | TTFT, tool execution breakdown, permission wait time (Enhanced Telemetry Beta) |
| Lifecycle Observability | `claude-code-lifecycle` | Per-session skill/command/agent usage (DuckDB + Hooks) |
| Global Usage Tracking | `claude-code-global-usage` | Cross-session skill/command/agent trends, model & project analysis (DuckDB) |

## Verifying Data Collection

```bash
# Check Loki is receiving data
curl -s http://localhost:3100/loki/api/v1/labels | jq .

# Check Prometheus targets
# Open: http://localhost:9090/targets

# Test OTEL Collector is reachable
curl -v http://localhost:4317

# Test telemetry with console output (no stack needed)
OTEL_METRICS_EXPORTER=console OTEL_METRIC_EXPORT_INTERVAL=1000 claude -p "test"
```

## Key LogQL Queries (Loki)

```logql
# All Claude Code events
{service_name="claude-code"} | json | drop __error__, __error_details__

# Events for a specific prompt
{service_name="claude-code"} | json | drop __error__, __error_details__ | prompt_id=`<prompt-id>`

# Tool failures only
{service_name="claude-code"} | json | drop __error__, __error_details__ | event_name=`tool_result` | success=`false`
```

## Event Schema

| Event | Key Fields |
|---|---|
| `user_prompt` | `prompt_id`, `session_id`, `prompt_length` |
| `api_request` | `model`, `cost_usd`, `duration_ms`, `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_creation_tokens` |
| `tool_result` | `tool_name`, `success`, `duration_ms`, `tool_result_size_bytes` |
| `system_prompt` | `system_prompt_hash`, `system_prompt_length`, `session_id` |
| `hook_execution_complete` | `hook_name`, `num_success`, `num_blocking`, `session_id` |
| `feedback_survey` | `survey_type` (`post_compact`), `prompt_id`, `session_id` |

## Trace Spans (Enhanced Telemetry Beta)

Requires `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`. These spans are sent to Tempo via OTLP.

| Span Name | Key Attributes |
|---|---|
| `claude_code.interaction` | Root span for a full user interaction (prompt → response) |
| `claude_code.llm_request` | LLM API call. `ttft_ms`, `model`, `input_tokens`, `output_tokens` |
| `claude_code.tool` | Tool invocation. `tool_name`, `result_tokens` |
| `claude_code.tool.execution` | Tool execution phase. `tool_name`, `success`, `error` |
| `claude_code.tool.blocked_on_user` | Permission wait. `decision` (accept/reject/timeout) |

## Key TraceQL Queries

```traceql
# All interaction traces
{resource.service.name="claude-code" && name="claude_code.interaction"}

# LLM requests with TTFT
{resource.service.name="claude-code" && name="claude_code.llm_request"}

# Tool executions
{resource.service.name="claude-code" && name="claude_code.tool.execution"}

# Permission wait times
{resource.service.name="claude-code" && name="claude_code.tool.blocked_on_user"}

# Slow LLM requests (> 10s)
{resource.service.name="claude-code" && name="claude_code.llm_request" && duration > 10s}
```

## Lifecycle Observability (DuckDB + Hooks)

Hook-based tracking of session lifecycle events. Data flows:
`Claude Code hooks → JSONL (data/lifecycle/events.jsonl) → DuckDB API (:8082) → Grafana`

### Tracked Events

| Event | Hook | Captured Data |
|---|---|---|
| Session start/end | SessionStart, SessionEnd | source, model, cwd |
| Skill invocations | PreToolUse[Skill] | skill_name, args |
| Agent spawns | PreToolUse[Agent], SubagentStart/Stop | agent_type, model, transcript |
| User prompts | UserPromptSubmit | prompt text, `/command` detection |

### DuckDB API Endpoints (localhost:8082)

| Endpoint | Purpose |
|---|---|
| `GET /api/stats` | Overall statistics |
| `GET /api/sessions` | Session summaries with skill/agent/command counts |
| `GET /api/skills` | Skill usage aggregation |
| `GET /api/commands` | Slash-command usage |
| `GET /api/agents` | Agent type distribution |
| `GET /api/models` | Model usage distribution |
| `GET /api/projects` | Project (cwd) usage with skill/agent counts |
| `GET /api/timeline?session_id=X` | All events for a session |
| `POST /api/query` | Arbitrary SELECT queries |

### Verifying Lifecycle Data

```bash
# Check events are being written
tail -f data/lifecycle/events.jsonl | jq .

# Check DuckDB API
curl http://localhost:8082/api/stats | jq .
curl http://localhost:8082/api/sessions | jq .
```
