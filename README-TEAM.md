# Claude Code Monitoring - Degree Analytics Team Guide

## 🎯 What This ACTUALLY Does

This monitoring system tracks **REAL** Claude Code usage via OpenTelemetry:
- **Real-time cost tracking** per session and model
- **Token usage** (input/output/cache)
- **Lines of code generated**
- **Session counts and duration**

## ⚠️ What It DOESN'T Do

- **No Linear integration** (not available in OTEL metrics)
- **No per-developer comparison** (all metrics are per session)
- **No SQLite mining** (Claude uses OTEL now, not SQLite)

## 🚀 Quick Start

**Prerequisites**: Docker and Docker Compose

```bash
# Clone the repo
git clone git@github.com:degree-analytics/claude-code-monitoring-guide.git
cd claude-code-monitoring-guide

# Run complete setup (replaces team-deploy.sh)
just setup

# Deploy hooks for all team members
just deploy hooks
```

The setup:
- ✅ Starts Docker monitoring stack on organized 7100+ ports
- ✅ Validates entire system with health checks  
- ✅ Installs Claude Code hooks for automatic metric capture
- ✅ Provides service management commands for easy operations
- ✅ Sets up the working dashboard
- ✅ Adds telemetry exports to your shell profile

## 📊 The ONE Working Dashboard

**Claude Code Working Dashboard**: http://localhost:7102/d/claude-code-working/claude-code-working-dashboard

Shows:
- Total cost (real $$$)
- Cost by model (Haiku/Sonnet/Opus)
- Token usage over time
- Lines of code generated
- Session activity

## 🔧 How It REALLY Works

```
Claude Code → Hook System → Pushgateway → Prometheus → Grafana
                              (Port 7101)   (Port 7100)  (Port 7102)
```

Claude Code emits these REAL metrics:
- `claude_code_cost_usage_USD_total` - Actual costs
- `claude_code_token_usage_tokens_total` - Token counts
- `claude_code_lines_of_code_count_total` - LOC generated
- `claude_code_session_count_total` - Session counts

## 📝 Daily Usage

### Just Use Claude Normally
```bash
claude
```

That's it! Metrics flow automatically if telemetry is enabled.

### Check Your Costs
```bash
# Open dashboards
just service console grafana

# Or visit directly:
# Stock Dashboard: http://localhost:7102/d/claude-code-working
# Tool Usage Dashboard: http://localhost:7102/d/tool-usage
```

### Verify Metrics Are Flowing
```bash
# Run comprehensive tests
just test all

# Check hook system
just monitor validate

# View current metrics
curl -s http://localhost:7101/metrics | grep claude

# Check Prometheus has data
curl -s "http://localhost:7100/api/v1/query?query=sum(claude_code_cost_usage_USD_total)"
```

## 🛠️ Team Management Commands

```bash  
# Service Management
just status                  # Check all service health
just service restart grafana # Restart specific service
just service logs prometheus # View service logs

# Hook Deployment  
just deploy hooks            # Install hooks for current user
just deploy validate         # Verify hook installation

# Testing & Validation
just test all               # Run all tests
just monitor validate       # Check entire stack
just monitor status         # Health check services

# Dashboard Management
just dashboard list         # List available dashboards
just dashboard backup       # Export all dashboards
just dashboard publish <name> # Deploy specific dashboard
```

## 🛠️ Troubleshooting

### No Data in Dashboard
1. **Quick diagnosis**:
   ```bash
   # Check system health  
   just status
   
   # Validate entire stack
   just monitor validate
   
   # Test hooks
   just test hooks
   ```

2. **Check hooks are installed**:
   ```bash
   # Verify deployment
   just deploy validate
   ```

2. Check OTEL endpoint:
   ```bash
   env | grep OTEL_EXPORTER_OTLP_ENDPOINT
   # Should show: http://localhost:7110
   ```

3. Restart terminal after setup:
   ```bash
   source ~/.zshrc  # or ~/.bashrc
   ```

### Port Conflicts
The setup script handles this automatically, but if needed:
```bash
./change-ports.sh  # Changes to 3030, 9091, 7110, 7111
```

## 📂 What's Real vs What We Tried

### ✅ What Works (Keep Using)
- OpenTelemetry metrics from Claude Code
- OTEL Collector → Prometheus → Grafana pipeline
- The working dashboard
- Docker Compose setup

### ❌ What Doesn't Work (We Removed)
- SQLite extraction (Claude stopped using it)
- Developer comparison dashboards (no user labels in OTEL)
- Linear integration (not available in metrics)
- Made-up ROI calculations

## 🔐 Privacy & Security

- **All metrics stay local** - nothing leaves your machine
- **No code content** is sent - only metadata
- **User email** is included in metrics (for potential aggregation)
- **Session IDs** are unique per Claude session

## 💡 Key Insights

1. **Claude Code costs add up** - Track them!
2. **Haiku vs Sonnet vs Opus** - Big price differences
3. **Cache tokens are free** - Use them when possible
4. **Lines of code** - Rough estimate but useful

## 📚 Documentation

- **[METRICS-REFERENCE.md](METRICS-REFERENCE.md)** - Complete list of all available metrics
- **Dashboard**: Only use the "working" dashboard
- **Metrics**: Real OTEL metrics only (claude_code_*)

## 📞 Support

- **Issues**: Contact Chad Walters
- **Questions**: Check METRICS-REFERENCE.md first

## 🚦 Quick Status Check

```bash
# Is everything running?
docker-compose ps

# Are metrics flowing?
curl -s http://localhost:9091/api/v1/query?query=up | jq '.data.result'

# What's my total cost?
curl -s "http://localhost:9091/api/v1/query?query=sum(claude_code_cost_usage_USD_total)" | jq '.data.result[0].value[1]'
```

Remember: This tracks **REAL usage and costs**, not imaginary metrics. Use it to understand actual Claude Code spending.