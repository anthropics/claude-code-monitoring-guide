# Muninn - AI Tool Observability Platform

**Remember everything about your AI tools.** Muninn provides comprehensive monitoring and analytics for AI development tools, starting with Claude Code and designed to expand to any AI assistant or automation tool your team uses.

**🗺️ DOCUMENTATION HUB**: **[`docs/INDEX.md`](docs/INDEX.md)** - Role-based navigation for all documentation  
**⚡ CORE WORKFLOWS**: **[`CLAUDE.md`](CLAUDE.md)** - Essential commands and critical references  
**🟢 CURRENT STATUS**: **[`CURRENT-STATUS.md`](CURRENT-STATUS.md)** - System operational status and working dashboard ✅

## Overview

Muninn is a production-ready observability platform that tracks usage, costs, and productivity across your AI tool ecosystem. Named after Odin's raven of memory, Muninn remembers and analyzes every interaction with your AI development tools to provide actionable insights for teams and organizations.

**Current Implementation**: Production-ready monitoring for Claude Code, with extensible architecture for any AI tool.
**Future Vision**: Universal AI tool observability - monitor Claude Code, GitHub Copilot, OpenAI API, Cursor, and custom AI tools from a single platform.

## What's Actually Built & Working

### 🏗️ Universal Infrastructure
- **Production Service Stack**: Docker, Prometheus, Pushgateway, Grafana with organized 7100+ port management
- **Justfile Operations**: Production-grade service management with health checking and validation
- **Extensible Architecture**: Clean separation between universal infrastructure and tool-specific adapters

### 🎯 Claude Code Adapter (Production Ready)
- **4 Live Dashboards**: Tools, Bash Commands, Agents, and MCP usage analytics  
- **Automatic Metrics Collection**: Hook-based capture of every Claude Code interaction
- **Real-Time Monitoring**: Live dashboards showing usage patterns, costs, and productivity metrics
- **Breakthrough Time-Series**: Timestamp-based counter system enabling proper historical analysis

## Key Metrics (Claude Code Adapter)

- **Tool Usage**: Every Read, Write, Edit, Bash, Task, MCP tool use with file types and operations
- **Bash Command Tracking**: Raw commands (git, curl, just) with categories and just subcommands  
- **Agent Usage**: Task tool usage by agent type and task categories
- **MCP Integration**: Server usage (context7, linear) with tool breakdown and categories
- **Session Analytics**: Usage by user, session, and time periods

## 🔑 HOW Muninn Works

**The Core Innovation**: Universal AI tool monitoring with timestamp-based counter accumulation enabling proper time-series data across any AI platform.

### Architecture Overview
```
AI Tool Use → Adapter Hook → Pushgateway (7101)
    │             │               ↓
Claude Code ──┐   │         Prometheus (7100)
GPT API ─────┼───┤               ↓
Copilot ─────┼───┤          Grafana (7102)  
Custom ──────┘   │               ↓
              Universal      Dashboards
             Infrastructure
```

### Current Implementation (Claude Code)
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

## 🔗 Expanding to Other AI Tools

**Vision**: Universal AI tool monitoring through Muninn's extensible adapter system

### Current: Claude Code (Production Ready)
- ✅ **Hook Integration**: Complete tool capture via production-tool-hook.sh
- ✅ **4 Live Dashboards**: Tools, Bash Commands, Agents, MCP
- ✅ **Real-Time Analytics**: Usage patterns, costs, productivity metrics

### Planned Adapters
- **GitHub Copilot**: VS Code extension monitoring
- **OpenAI API**: Direct API call capture and cost tracking  
- **Cursor**: Application-level monitoring
- **Custom LLMs**: Extensible framework for any AI tool

**Architecture**: Each adapter plugs into the universal Muninn infrastructure, providing consistent dashboards and analytics across all AI tools.

## 📚 Documentation Hub

**🗺️ NAVIGATION CENTER**: **[`docs/INDEX.md`](docs/INDEX.md) - Complete documentation map with role-based navigation**

### Essential Guides
- **[`infrastructure/JUSTFILE-GUIDE.md`](JUSTFILE-GUIDE.md) - Complete service management system** ⭐
- **[`MUNINN.md`](MUNINN.md) - Core Muninn workflows and critical references** ⭐  
- [`METRICS-REFERENCE.md`](METRICS-REFERENCE.md) - All metrics with query examples
- [`troubleshooting.md`](troubleshooting.md) - Diagnostic procedures and solutions

### Adapter Guides  
- **[`adapters/claude/README.md`](adapters/claude/README.md) - Claude Code adapter setup and operation** 
- [`README-TEAM.md`](README-TEAM.md) - Team deployment and management
- [`CUSTOM-METRICS-GUIDE.md`](CUSTOM-METRICS-GUIDE.md) - Adding custom metrics and adapters

### Architecture & Analysis
- [`DASHBOARD-AUDIT-RESULTS.md`](DASHBOARD-AUDIT-RESULTS.md) - Dashboard validation and current status ✅
- [`claude_code_roi_full.md`](claude_code_roi_full.md) - Complete Claude Code implementation details
- [`sample-report-output.md`](sample-report-output.md) - Example reports and analyses

### System Files
- [`infrastructure/docker-compose.yml`](infrastructure/docker-compose.yml) - Universal monitoring infrastructure
- [`infrastructure/prometheus.yml`](infrastructure/prometheus.yml) - Metrics collection configuration  
- [`adapters/claude/hooks/production-tool-hook.sh`](adapters/claude/hooks/production-tool-hook.sh) - Claude Code adapter hook

**💡 New to Muninn?** Start with **[`docs/INDEX.md`](docs/INDEX.md)** for role-based navigation to exactly what you need.

## Quick Start

**Prerequisites:** Docker and Docker Compose installed

**1. Setup & Start**
```bash
# Clone the repository
git clone <this-repo>
cd muninn

# Navigate to infrastructure directory for all operations
cd infrastructure

# Run complete setup (checks prerequisites, starts services, validates)
just setup
```

**2. Access Dashboards**
- **Grafana:** http://localhost:7102 (admin/admin)
- **Prometheus:** http://localhost:7100  
- **Pushgateway:** http://localhost:7101

**3. Deploy Claude Code Adapter**
```bash
# Install Claude Code monitoring hooks for current user (from infrastructure/)
just deploy hooks

# Test that everything is working
just test all
```

**4. View Your 4 Production Dashboards**
```bash
# Check service health (from infrastructure/)
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

The infrastructure includes a comprehensive `justfile` for easy management (all commands run from `infrastructure/` directory):

```bash
# Service Operations (from infrastructure/)
just up                    # Start all services
just down                  # Stop all services  
just restart              # Restart services
just status               # Show service status & URLs

# Monitoring & Testing
just monitor status       # Health check all services
just monitor validate     # Validate entire stack
just test hooks          # Test Claude Code adapter hooks
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

**New to Muninn?** Start with the [Documentation Hub](#-documentation-hub) for role-based navigation to exactly what you need.

**Looking for implementation details?** Read [`claude_code_roi_full.md`](claude_code_roi_full.md) for the complete Claude Code adapter development story.

## Contributing & License

Muninn is built for the community of AI-assisted developers. If you have insights, improvements, or want to contribute new AI tool adapters, please feel free to create an issue or PR.

## Credits

**Original Implementation**: [Kashyap Coimbatore Murali](https://www.linkedin.com/in/kashyap-murali/)
**Based on**: [Anthropic's Claude Code ROI Guide](https://github.com/anthropics/claude-code-monitoring-guide)  
**Evolved into**: Muninn - Universal AI Tool Observability Platform

---

**Muninn remembers everything about your AI tools.** Start monitoring your AI development workflow today.
