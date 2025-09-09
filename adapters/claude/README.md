# Claude Code Adapter for Muninn

**Muninn's first AI tool adapter** - Comprehensive monitoring and analytics for Claude Code usage patterns, costs, and productivity metrics.

## Overview

The Claude Code adapter captures every tool use (Read, Write, Edit, Bash, Task, MCP) automatically via hook system integration, providing real-time monitoring and analytics for Claude Code usage across your development workflow.

## What This Adapter Captures

### 🔧 Tool Usage Metrics
- **Every Tool Use**: Read, Write, Edit, Bash, Task, MCP with file types and operations
- **Operation Classification**: read, write, edit, bash, search, todo, web, agent, file_ops
- **File Extension Tracking**: .py, .js, .md, .json, etc.

### 💻 Bash Command Analytics
- **Raw Commands**: git, curl, just, npm, docker, etc.
- **Command Categories**: Development tools, infrastructure, package management
- **Just Subcommands**: status, up, deploy, test, etc.
- **Git Subcommands**: status, commit, push, pull, etc.

### 🤖 Agent Usage Tracking
- **Agent Types**: general-purpose, task-executor, git-expert, etc.
- **Task Categories**: search, setup, coding, debugging, analysis
- **Prompt Complexity**: Length tracking for performance analysis
- **Success/Failure Rates**: Task completion tracking

### 🔌 MCP Integration Monitoring
- **MCP Servers**: context7, linear, playwright, zen, notion
- **Tool Breakdown**: Individual MCP tool usage patterns
- **Server Categories**: Development tools, productivity, AI services

## Architecture

```
Claude Code Tool Use → production-tool-hook.sh → Pushgateway (7101)
                                                       ↓
                                                 Prometheus (7100)
                                                       ↓  
                                                  Grafana (7102)
                                                       ↓
                                              4 Production Dashboards
```

## Quick Setup

**Prerequisites**: Muninn infrastructure must be running (`just status` from `infrastructure/`)

**1. Deploy Claude Adapter Hooks**
```bash
# Navigate to infrastructure directory
cd infrastructure

# Install Claude Code monitoring hooks for current user
just deploy hooks

# Validate installation
just deploy validate
```

**2. Test Hook Integration**
```bash
# Test hook execution and JSON parsing
just test hooks

# Test end-to-end metrics flow
just test flow

# Run comprehensive tests
just test all
```

**3. Access Claude Dashboards**
- **🔧 Tool Usage**: http://localhost:7102/d/claude-tool-usage-simple
- **💻 Bash Commands**: http://localhost:7102/d/claude-bash-commands  
- **🤖 Agents**: http://localhost:7102/d/claude-agents
- **🔌 MCP**: http://localhost:7102/d/claude-mcp

## Hook System Details

### Installation Location
- **Hook Script**: `~/.claude/claude-code-monitoring/production-tool-hook.sh`
- **Configuration**: `~/.claude/settings.json` (PreToolUse/PostToolUse events)

### How It Works
1. **Trigger**: Every Claude Code tool use automatically triggers the hook
2. **Data Capture**: JSON stdin contains tool name, parameters, results, session info
3. **Processing**: Python script parses JSON and extracts relevant metrics
4. **Transmission**: HTTP POST to Pushgateway with timestamp-based uniqueness
5. **Storage**: Prometheus scrapes and stores time-series data
6. **Visualization**: Grafana dashboards display real-time usage analytics

### Breakthrough Innovation: Timestamp-Based Counter System
```python
timestamp_id = int(time.time() * 1000)  # millisecond timestamp for uniqueness
url = f'{pushgateway_url}/metrics/job/claude_code_tools/.../ts/{timestamp_id}'
```
**Result**: Proper counter accumulation (33→37→42) instead of flat data (1→1→1)

## Configuration Files

### Core Files
- **`hooks/production-tool-hook.sh`** - Main hook script with Python metrics processing
- **`dashboards/*.json`** - Grafana dashboard definitions for Claude usage
- **`config/`** - Claude adapter-specific configuration files

### Integration Points
- **Pushgateway URL**: http://localhost:7101 (configurable in hook script)
- **Metrics Endpoint**: `/metrics/job/claude_code_tools/instance/{user}/session/{session_id}/tool/{tool_name}/ts/{timestamp}`
- **Dashboard Provisioning**: Automatic loading via docker-compose volume mounts

## Team Deployment

### Individual Developer Setup
```bash
# Each developer runs this once
just deploy hooks
just deploy validate
```

### Team Management
```bash
# Deploy hooks for specific user
just deploy hooks username

# Validate all team members
just deploy validate

# Monitor team usage in dashboards
# -> Grafana: http://localhost:7102
# -> Users appear automatically in dashboard filters
```

## Troubleshooting

### Hook Not Working
```bash
# Check hook installation
just deploy validate

# Test hook execution
just test hooks

# Check hook script permissions
ls -la ~/.claude/claude-code-monitoring/production-tool-hook.sh
```

### No Metrics Appearing
```bash
# Check service health
just status

# Validate metric flow
just test flow

# Check pushgateway for raw metrics
curl http://localhost:7101/metrics | grep claude_custom
```

### Dashboard Issues
```bash
# Check dashboard availability
just dashboard list

# Re-deploy Claude dashboards
just dashboard publish claude-tool-usage-simple
just dashboard publish claude-bash-commands
just dashboard publish claude-agents  
just dashboard publish claude-mcp
```

## Metrics Reference

### Core Metrics Generated
- **`claude_custom_tool_usage_total`** - Every tool use with labels
- **`claude_custom_bash_commands_total`** - Bash command tracking
- **`claude_custom_agent_usage_total`** - Task/agent usage
- **`claude_code_cost_usage_USD_total`** - Estimated cost tracking
- **`claude_code_token_usage_tokens_total`** - Token usage estimation
- **`claude_code_lines_of_code_count_total`** - LOC modification tracking

### Useful Queries
```promql
# Total tool usage
sum(claude_custom_tool_usage_total)

# Most used bash commands
sum by (bash_command) (claude_custom_bash_commands_total)

# Agent usage by type
sum by (agent_type) (claude_custom_agent_usage_total)

# Tool usage by file type
sum by (file_extension) (claude_custom_tool_usage_total)
```

## Extending the Claude Adapter

### Adding Custom Metrics
1. **Modify Hook Script**: Edit `hooks/production-tool-hook.sh` Python section
2. **Add Metric Lines**: Append to `metrics_lines` list
3. **Test Changes**: Use `just test hooks` to validate
4. **Update Dashboards**: Add new metrics to dashboard queries

### Custom Dashboard Creation
1. **Export Existing**: `just dashboard export claude-tool-usage-simple`
2. **Modify JSON**: Edit dashboard definition file
3. **Import Updated**: `just dashboard import my-custom-dashboard`
4. **Publish**: `just dashboard publish my-custom-dashboard`

## Performance Impact

### Resource Usage
- **Hook Execution**: ~50ms per tool use
- **Network**: Single HTTP POST per tool use (~1KB)
- **Storage**: ~100 bytes per metric in Prometheus
- **Dashboard Updates**: Real-time (within seconds)

### Optimization Tips
- **Batching**: Hook processes metrics individually for real-time visibility
- **Filtering**: Use dashboard time ranges to limit query scope
- **Retention**: Configure Prometheus retention for long-term storage
- **Cleanup**: Pushgateway metrics auto-expire based on timestamp

## Integration with Other Muninn Adapters

The Claude adapter is designed to coexist with future Muninn adapters:

### Universal Infrastructure Sharing
- **Same Services**: Prometheus, Pushgateway, Grafana
- **Same Port Range**: 7100+ for all Muninn components
- **Same Management**: All adapters use justfile commands from `infrastructure/`

### Adapter Isolation
- **Separate Metrics**: claude_custom_* namespace prevents conflicts
- **Separate Dashboards**: Claude dashboards in `adapters/claude/dashboards/`
- **Separate Config**: Claude-specific configuration isolated in `adapters/claude/config/`

### Future Adapter Integration
```
Muninn Infrastructure (Universal)
├── adapters/
│   ├── claude/ (This adapter)
│   ├── copilot/ (Future)
│   ├── cursor/ (Future)  
│   └── openai-api/ (Future)
└── infrastructure/ (Shared by all)
```

## Support

### Documentation Links
- **[Main Muninn README](../../README.md)** - Overall system overview
- **[Metrics Reference](../../METRICS-REFERENCE.md)** - Complete metrics documentation
- **[Justfile Guide](../../JUSTFILE-GUIDE.md)** - Service management commands
- **[Troubleshooting](../../troubleshooting.md)** - Problem diagnosis procedures

### Quick Help Commands
```bash
# From infrastructure/ directory
just help               # Show all available commands
just help-monitoring    # Monitoring operations help
just help-dashboards    # Dashboard management help
just help-deployment    # Deployment and setup help
```

---

**💡 Remember**: The Claude adapter is Muninn's first implementation of AI tool monitoring. It demonstrates the pattern that future adapters (Copilot, Cursor, OpenAI API) will follow - universal infrastructure with tool-specific capture mechanisms.