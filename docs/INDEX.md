# Muninn Documentation Hub

## Purpose
Central navigation hub for Muninn AI tool observability platform documentation, providing organized access to setup guides, service management, troubleshooting procedures, and operational workflows for monitoring any AI development tool.

## When to Use This
- Setting up AI tool monitoring for the first time
- Finding specific operational commands quickly  
- Troubleshooting monitoring issues
- Understanding metrics and dashboards
- Onboarding new team members to AI tool observability
- Deploying monitoring for Claude Code, and preparing for future AI tool integrations

**Keywords:** muninn, ai tools, observability, claude code, monitoring, metrics, prometheus, grafana, justfile, hooks

Welcome to the comprehensive documentation hub for **Muninn** - a universal AI tool observability platform that provides comprehensive monitoring and analytics for AI development tools. Starting with Claude Code and designed to expand to any AI assistant or automation tool your team uses.

**🏗️ Current Status**: Production-ready monitoring stack with comprehensive service management
**📅 Last Updated**: 2025-09-07
**📋 Total Documents**: 8 comprehensive guides covering setup, operations, and troubleshooting

---

## 🚀 Quick Start Paths

Choose your path based on your role and immediate needs:

| Role | Primary Goal | Start Here | Time to Productive |
|------|-------------|------------|-------------------|
| **Individual Developer** | Monitor personal Claude Code usage | [Quick Start](#quick-start) → [Hook Deployment](../README.md#deploy-claude-code-hooks) | 10 minutes |
| **Team Lead** | Deploy monitoring for entire team | [Team Deployment](#team-deployment) → [Team Setup Guide](../README-TEAM.md) | 15 minutes |
| **DevOps Engineer** | Manage monitoring infrastructure | [Service Management](#service-management) → [Justfile Guide](../JUSTFILE-GUIDE.md) | 20 minutes |
| **Data Analyst** | Understand metrics and create reports | [Metrics & Dashboards](#metrics-dashboards) → [Metrics Reference](../METRICS-REFERENCE.md) | 15 minutes |
| **Troubleshooter** | Fix monitoring issues | [Troubleshooting](#troubleshooting) → [Troubleshooting Guide](../troubleshooting.md) | 5 minutes |
| **New Team Member** | Understand the monitoring system | [System Overview](#system-overview) → [Architecture Overview](#architecture) | 10 minutes |

---

## 🚨 CRITICAL: Essential Commands

**⚠️ MUST KNOW COMMANDS for daily operations (all from `infrastructure/` directory):**

```bash
# Navigate to infrastructure directory first
cd infrastructure

# Essential Setup (run once)  
just setup                    # Complete initial setup with validation
just deploy hooks            # Install Claude Code adapter hooks for current user

# Daily Operations  
just status                  # Check service health & URLs
just up                      # Start all monitoring services
just test all               # Comprehensive system validation

# Emergency Recovery
just service restart grafana    # Restart problematic service
just monitor validate          # Full stack health check
just clean containers          # Clean up containers if needed
```

---

## 📚 Documentation Structure

Muninn documentation is organized into universal platform guides and adapter-specific guides:

```
muninn/
├── 📋 README.md                    # Main Muninn platform overview
├── 🎯 CLAUDE.md                    # Core workflows and critical references  
├── 📖 JUSTFILE-GUIDE.md            # Complete service management guide
├── 📊 METRICS-REFERENCE.md         # All available metrics and queries
├── 🔧 CUSTOM-METRICS-GUIDE.md      # Adding custom metrics and hooks
├── 🔧 troubleshooting.md           # Problem diagnosis and solutions
├── 📝 README-TEAM.md               # Team deployment and management
├── 🏗️ claude_code_roi_full.md      # Complete implementation details
├── 📝 sample-report-output.md      # Example reports and analyses
├── infrastructure/                 # Universal monitoring stack
│   ├── justfile                    # Service management commands
│   ├── docker-compose.yml          # Service orchestration  
│   ├── prometheus.yml              # Metrics collection config
│   └── scripts/                    # Helper scripts
├── adapters/                       # AI tool adapters
│   └── claude/                     # Claude Code adapter
│       ├── 📋 README.md            # Claude adapter setup guide ⭐
│       ├── hooks/                  # Claude-specific hooks
│       ├── dashboards/             # Claude-specific dashboards
│       └── config/                 # Claude-specific configuration
└── docs/                           # Documentation hub
    └── INDEX.md                    # This navigation file
```

---

## 🎯 Quick Start

**Focus**: Get Claude Code monitoring running in under 10 minutes

### Essential Setup
- **[Main Setup Guide](../README.md#quick-start)** - Complete setup from zero to working dashboards ⭐
- **[Claude Adapter Guide](../adapters/claude/README.md)** - Claude Code adapter-specific setup ⭐
- **[Service Management Commands](../README.md#service-management)** - Essential justfile commands from infrastructure/ ⭐

### Immediate Validation  
- **[Testing Guide](../README.md#monitoring--testing)** - Verify your installation works correctly
- **[Dashboard Access](../README.md#port-configuration)** - URLs and credentials for all services

**💡 First Time?** Navigate to `infrastructure/` then run `just setup` - handles everything automatically with validation.

---

## 🏢 Team Deployment  

**Focus**: Deploy Muninn monitoring for entire development teams

### Team Setup & Management
- **[Team Setup Guide](../README-TEAM.md)** - Complete team deployment with Claude adapter hook management ⭐
- **[Team Management Commands](../README-TEAM.md#team-management-commands)** - Service management for teams
- **[Team Troubleshooting](../README-TEAM.md#troubleshooting)** - Team-specific diagnostic procedures

### Claude Adapter Deployment
- **[Claude Adapter Guide](../adapters/claude/README.md)** - Complete Claude Code adapter setup ⭐
- **[Hook System Overview](../adapters/claude/README.md#hook-system-details)** - How automatic Claude Code metric collection works
- **[Hook Installation](../README.md#deploy-claude-code-hooks)** - Installing Claude hooks for team members

**💡 Quick Access**: [Team README](../README-TEAM.md) - Everything teams need to know

---

## 🛠️ Service Management

**Focus**: Operating and maintaining the monitoring infrastructure

### Justfile System (Production-Grade)
- **[Complete Justfile Guide](../JUSTFILE-GUIDE.md)** - Comprehensive service management system ⭐
- **[Service Operations](../JUSTFILE-GUIDE.md#service-management)** - Start, stop, restart, status checking
- **[Health Monitoring](../JUSTFILE-GUIDE.md#monitoring--testing)** - Health checks and validation
- **[Dashboard Management](../JUSTFILE-GUIDE.md#dashboard-management)** - Dashboard CRUD operations

### Architecture & Ports
- **[Port Configuration](../README.md#port-configuration)** - Organized 7100+ port range for all services
- **[Service Stack](../JUSTFILE-GUIDE.md#architecture)** - How services connect and communicate

**💡 Power Users**: The justfile system hides all Docker complexity behind simple, memorable commands.

---

## 📊 Metrics & Dashboards

**Focus**: Understanding data, creating queries, and building insights

### Metrics Reference
- **[Complete Metrics Reference](../METRICS-REFERENCE.md)** - All available metrics with examples ⭐
- **[Hook-Based Metrics](../METRICS-REFERENCE.md#current-hook-based-metrics)** - Current implementation details
- **[Query Examples](../METRICS-REFERENCE.md#example-queries)** - Prometheus queries for common use cases

### Dashboard System
- **[Stock Dashboard](../README.md#access-dashboards)** - Cost, tokens, and LOC tracking
- **[Tool Usage Dashboard](../README.md#access-dashboards)** - Detailed tool usage analytics
- **[Dashboard Management](../JUSTFILE-GUIDE.md#dashboard-management)** - Backup, restore, publish dashboards

### Custom Metrics
- **[Custom Metrics Guide](../CUSTOM-METRICS-GUIDE.md)** - Adding your own metrics and tracking ⭐
- **[Hook System](../CUSTOM-METRICS-GUIDE.md#current-implementation)** - How automatic tracking works

**💡 Dashboard URLs**: 
- Grafana: http://localhost:7102 (admin/admin)
- Prometheus: http://localhost:7100  
- Pushgateway: http://localhost:7101

---

## 🔧 Troubleshooting

**Focus**: Diagnosing and fixing monitoring issues quickly

### Diagnostic System
- **[Quick Diagnostics](../troubleshooting.md#quick-diagnostics-recommended)** - Justfile-powered troubleshooting ⭐
- **[Service URLs](../troubleshooting.md#quick-diagnostics-recommended)** - Updated port configuration
- **[Common Issues](../troubleshooting.md)** - Legacy telemetry issues and solutions

### Testing & Validation
- **[Test Commands](../JUSTFILE-GUIDE.md#monitoring--testing)** - Comprehensive testing utilities
- **[Health Checking](../JUSTFILE-GUIDE.md#monitoring--testing)** - Service health validation
- **[Error Recovery](../JUSTFILE-GUIDE.md#error-handling)** - Common issues and fixes

**💡 Emergency Commands** (from `infrastructure/`):
```bash
just status              # Quick health overview
just monitor validate    # Full system check
just test all           # Comprehensive testing
```

---

## 📖 System Overview

**Focus**: Understanding Muninn's universal AI tool observability architecture and capabilities  

### Universal Platform Architecture
Muninn uses extensible adapter architecture with universal infrastructure:

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

### Current: Claude Code Adapter (Production Ready)
```
Claude Code → production-tool-hook.sh → Pushgateway (7101)
                                            ↓
                                       Prometheus (7100)  
                                            ↓
                                        Grafana (7102)
```

### Key Components
- **Universal Infrastructure**: Prometheus, Pushgateway, Grafana with organized 7100+ port range
- **Claude Adapter**: Automatically captures every Claude Code tool use via hook system
- **Extensible Architecture**: Clean separation between universal infrastructure and tool-specific adapters
- **Production Management**: Justfile-based service orchestration and health checking

### Current Capabilities (Claude Adapter)
- ✅ **Real-time Monitoring**: Every Claude Code tool use captured automatically
- ✅ **4 Production Dashboards**: Tools, Bash Commands, Agents, MCP usage analytics
- ✅ **Cost Estimation**: Track estimated Claude Code costs over time
- ✅ **Usage Analytics**: Understand tool usage patterns and productivity
- ✅ **Team Insights**: Monitor usage across team members and sessions
- ✅ **Production Ready**: Health checking, data persistence, error recovery

### Future Vision: Universal AI Tool Monitoring
- 🔧 **GitHub Copilot Adapter**: VS Code extension monitoring
- 🔧 **OpenAI API Adapter**: Direct API call capture and cost tracking  
- 🔧 **Cursor Adapter**: Application-level monitoring
- 🔧 **Custom LLM Adapters**: Extensible framework for any AI tool

**💡 Full Details**: [Complete ROI Implementation Guide](../claude_code_roi_full.md)

---

## 🎓 Learning Path Recommendations

### For Beginners (Claude Code Monitoring)
1. Start with [Quick Start](../README.md#quick-start) - get basic monitoring running
2. Read [Claude Adapter Guide](../adapters/claude/README.md) - understand the adapter
3. Deploy hooks with [Hook Installation](../README.md#deploy-claude-code-hooks) 
4. Explore dashboards and understand [Basic Metrics](../METRICS-REFERENCE.md)

### For Teams  
1. Review [Team Setup Guide](../README-TEAM.md)
2. Study [Claude Adapter Deployment](../adapters/claude/README.md#team-deployment)
3. Master [Team Management Commands](../README-TEAM.md#team-management-commands)
4. Understand [Troubleshooting Procedures](../README-TEAM.md#troubleshooting)

### For Power Users & Platform Administrators
1. Study the [Complete Justfile System](../JUSTFILE-GUIDE.md)
2. Learn [Advanced Service Management](../JUSTFILE-GUIDE.md#advanced-service-operations)  
3. Understand [Universal Infrastructure](../README.md#architecture) for future adapters
4. Create [Custom Metrics](../CUSTOM-METRICS-GUIDE.md) for your specific needs

### For Data Analysis & AI Tool Monitoring
1. Master [Metrics Reference](../METRICS-REFERENCE.md) with query examples
2. Understand [Hook-Based vs Official Metrics](../METRICS-REFERENCE.md#available-metrics)
3. Build custom dashboards with [Dashboard Management](../JUSTFILE-GUIDE.md#dashboard-management)
4. Explore [Claude Adapter Metrics](../adapters/claude/README.md#metrics-reference)

---

## 📋 Document Status Legend

- ⭐ **Essential Reading** - Core documents for successful operation
- 🆕 **Recently Updated** - Contains latest improvements and fixes  
- 🏗️ **In Progress** - Documents being actively improved
- 📚 **Reference** - Detailed technical specifications

---

## 🆘 Need Help?

**Stuck on setup?** → [Quick Start Path](#quick-start) → Navigate to `infrastructure/` → `just setup`  
**Services not working?** → [Emergency Commands](#critical-essential-commands) → `just monitor validate`  
**Hook issues?** → [Troubleshooting](#troubleshooting) → `just test hooks`  
**Claude adapter issues?** → [Claude Adapter Guide](../adapters/claude/README.md#troubleshooting)  
**Team deployment?** → [Team Path](#team-deployment) → [Team Guide](../README-TEAM.md)  
**Advanced operations?** → [Service Management](#service-management) → [Justfile Guide](../JUSTFILE-GUIDE.md)

**💡 Remember**: Muninn is designed to be **simple to use** but **powerful in capabilities**. The universal infrastructure with adapter-based architecture provides production-grade monitoring for any AI tool, starting with Claude Code and expanding to your entire AI development toolkit.