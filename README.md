# Claude Code ROI Measurement Guide

A comprehensive guide to measuring the return on investment for Claude Code implementation in your development organization.

**🗺️ DOCUMENTATION HUB**: **[`docs/INDEX.md`](docs/INDEX.md)** - Role-based navigation for all documentation  
**⚡ CORE WORKFLOWS**: **[`CLAUDE.md`](CLAUDE.md)** - Essential commands and critical references  
**🟢 CURRENT STATUS**: **[`CURRENT-STATUS.md`](CURRENT-STATUS.md)** - System operational status and working dashboard ✅

## Overview

This repository contains a complete walkthrough for setting up telemetry, measuring costs, tracking productivity, and calculating ROI for Claude Code usage. Whether you're an individual developer or managing a large engineering team, this guide provides the tools and metrics needed to make data-driven decisions about AI coding assistance.

## What's Actually Built & Working

- **4 Production Dashboards**: Tools, Bash Commands, Agents, and MCP usage tracking
- **Hook-Based Metrics Collection**: Automatic capture of every Claude Code tool use via production-tool-hook.sh
- **Real-Time Monitoring**: Live dashboards showing actual usage patterns and adoption
- **Timestamp-Based Counter System**: Breakthrough metrics accumulation that enables time-series analysis
- **Complete Service Stack**: Docker, Prometheus, Pushgateway, Grafana with 7100+ port organization

## Key Metrics Actually Captured

- **Tool Usage**: Every Read, Write, Edit, Bash, Task, MCP tool use with file types and operations
- **Bash Command Tracking**: Raw commands (git, curl, just) with categories and just subcommands  
- **Agent Usage**: Task tool usage by agent type and task categories
- **MCP Integration**: Server usage (context7, linear) with tool breakdown and categories
- **Session Analytics**: Usage by user, session, and time periods

## 🔑 HOW The Metrics System Works

**The Key Breakthrough**: Timestamp-based counter accumulation that enables proper time-series data.

### Core Architecture
```
Claude Code Tool Use → production-tool-hook.sh → Pushgateway (7101)
                                                      ↓
                                                Prometheus (7100)
                                                      ↓  
                                                 Grafana (7102)
```

### Critical Innovation: Timestamp Uniqueness
- **Problem**: Standard counters overwrite each other, causing flat time-series data
- **Solution**: Each metric includes a millisecond timestamp in the pushgateway URL
- **Result**: Counters accumulate properly (33→37→42) instead of staying static (1→1→1)

```bash
# This enables proper counter accumulation:
url = f'{pushgateway_url}/metrics/job/claude_code_tools/instance/{user_id}/session/{session_id}/tool/{tool_name}/ts/{timestamp_id}'
```

### Automatic Capture System
- **Installation**: `just deploy hooks` installs production-tool-hook.sh to ~/.claude/settings.json
- **Triggers**: Every Claude Code tool use (PreToolUse/PostToolUse events)  
- **Processing**: JSON stdin → Python parsing → HTTP POST to Pushgateway
- **Data Flow**: Real-time metrics visible in dashboards within seconds

### Dashboard Queries
- **Counter Aggregation**: `sum(claude_custom_tool_usage_total)` 
- **Time-Series**: Built-in Grafana time picker controls all dashboards
- **Labels**: session_id, user, tool, operation_type, file_extension, bash_command, agent_type

## 🔗 Linear Integration Status

**Current Status**: Pipeline established, not actively used

- ✅ **MCP Connection**: Linear MCP server configured and working
- ✅ **Tool Capture**: `mcp__linear__create_comment` appears in metrics (1 use captured)
- ✅ **Dashboard Integration**: Linear usage shows up in MCP dashboard
- ⏸️ **Not Actively Pulling**: Linear data import/analysis pipeline not implemented yet
- 🔧 **Future Work**: Data ingestion from Linear requires additional workflow design

**What Works Now**: Linear MCP tool usage is tracked in the MCP dashboard when used
**What's Next**: Decide how to pull Linear data into analysis workflows (separate from metrics collection)

## 📚 Documentation Hub

**🗺️ NAVIGATION CENTER**: **[`docs/INDEX.md`](docs/INDEX.md) - Complete documentation map with role-based navigation**

### Essential Guides
- **[`JUSTFILE-GUIDE.md`](JUSTFILE-GUIDE.md) - Complete service management system** ⭐
- **[`CLAUDE.md`](CLAUDE.md) - Core workflows and critical references** ⭐  
- [`METRICS-REFERENCE.md`](METRICS-REFERENCE.md) - All metrics with query examples
- [`troubleshooting.md`](troubleshooting.md) - Diagnostic procedures and solutions

### Specialized Guides  
- [`README-TEAM.md`](README-TEAM.md) - Team deployment and management
- [`CUSTOM-METRICS-GUIDE.md`](CUSTOM-METRICS-GUIDE.md) - Adding custom metrics and hooks
- [`DASHBOARD-AUDIT-RESULTS.md`](DASHBOARD-AUDIT-RESULTS.md) - Dashboard resolution: data corruption fix and current status ✅
- [`claude_code_roi_full.md`](claude_code_roi_full.md) - Complete implementation details
- [`sample-report-output.md`](sample-report-output.md) - Example reports and analyses

### Historical/Reference Docs
- [`LINEAR-INTEGRATION-STATUS.md`](LINEAR-INTEGRATION-STATUS.md) - Linear integration debugging (historical)
- [`AGENT-METRICS-ISSUE.md`](AGENT-METRICS-ISSUE.md) - Agent monitoring analysis (historical)

### Configuration Files
- [`docker-compose.yml`](docker-compose.yml) - Infrastructure orchestration
- [`prometheus.yml`](prometheus.yml) - Metrics collection configuration  
- [`production-tool-hook.sh`](production-tool-hook.sh) - Claude Code hook system

**💡 New to the system?** Start with **[`docs/INDEX.md`](docs/INDEX.md)** for role-based navigation to exactly what you need.

## Quick Start

**Prerequisites:** Docker and Docker Compose installed

**1. Setup & Start**
```bash
# Clone the repository
git clone <this-repo>
cd claude-code-monitoring-guide

# Run complete setup (checks prerequisites, starts services, validates)
just setup
```

**2. Access Dashboards**
- **Grafana:** http://localhost:7102 (admin/admin)
- **Prometheus:** http://localhost:7100  
- **Pushgateway:** http://localhost:7101

**3. Deploy Claude Code Hooks**
```bash
# Install monitoring hooks for current user
just deploy hooks

# Test that everything is working
just test all
```

**4. View Your 4 Production Dashboards**
```bash
# Check service health
just status

# Access Grafana to view dashboards
just service console grafana
```

**Available Dashboards:**
- **🔧 Tool Usage**: http://localhost:7102/d/claude-tool-usage-simple
- **💻 Bash Commands**: http://localhost:7102/d/claude-bash-commands  
- **🤖 Agents**: http://localhost:7102/d/claude-agents
- **🔌 MCP**: http://localhost:7102/d/claude-mcp

## Service Management

The repository includes a comprehensive `justfile` for easy management:

```bash
# Service Operations
just up                    # Start all services
just down                  # Stop all services  
just restart              # Restart services
just status               # Show service status & URLs

# Monitoring & Testing
just monitor status       # Health check all services
just monitor validate     # Validate entire stack
just test hooks          # Test Claude Code hooks
just test all            # Run all tests

# Dashboard Management  
just dashboard list      # List available dashboards
just dashboard publish   # Deploy dashboards to Grafana
just dashboard backup    # Export all dashboards

# Get Help
just help               # Show all available commands
just help-services      # Service management help
just help-monitoring    # Monitoring operations help
```

## Port Configuration

All services use organized 7100+ port range:
- **Prometheus:** 7100
- **Pushgateway:** 7101  
- **Grafana:** 7102
- **OTEL Collector:** 7110-7112

## Getting Started (Detailed)

Read the complete guide in [`claude_code_roi_full.md`](claude_code_roi_full.md) for detailed setup instructions, real-world examples, and actionable insights for your organization.

## Contributing

This guide is based on real-world implementation experience. If you have additional insights or improvements, please feel free to create an issue / PR.

This guide was written by [Kashyap Coimbatore Murali](https://www.linkedin.com/in/kashyap-murali/)
