# Claude Code Monitoring Documentation Hub

## Purpose
Central navigation hub for Claude Code monitoring system documentation, providing organized access to setup guides, justfile commands, troubleshooting procedures, and operational workflows.

## When to Use This
- Setting up Claude Code monitoring for the first time
- Finding specific operational commands quickly  
- Troubleshooting monitoring issues
- Understanding metrics and dashboards
- Onboarding new team members to monitoring

**Keywords:** claude code, monitoring, metrics, prometheus, grafana, justfile, hooks

Welcome to the comprehensive documentation hub for **Claude Code Monitoring Guide** - a production-grade monitoring system for Claude Code usage tracking built with Docker, Prometheus, Grafana, and Python helper scripts.

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

**⚠️ MUST KNOW COMMANDS for daily operations:**

```bash
# Essential Setup (run once)
just setup                    # Complete initial setup with validation
just deploy hooks            # Install Claude Code hooks for current user

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

Our documentation is organized into 8 specialized guides designed for efficient discovery and operational excellence:

```
claude-code-monitoring-guide/
├── 📋 README.md                    # Main overview with quick start
├── 🎯 README-TEAM.md               # Team deployment and management
├── 📖 JUSTFILE-GUIDE.md            # Complete service management guide  
├── 📊 METRICS-REFERENCE.md         # All available metrics and queries
├── 🔧 CUSTOM-METRICS-GUIDE.md      # Adding custom metrics and hooks
├── 🔧 troubleshooting.md           # Problem diagnosis and solutions
├── 🏗️ claude_code_roi_full.md      # Complete implementation details
└── 📝 sample-report-output.md      # Example reports and analyses
```

---

## 🎯 Quick Start

**Focus**: Get monitoring running in under 10 minutes

### Essential Setup
- **[Main Setup Guide](../README.md#quick-start)** - Complete setup from zero to working dashboards ⭐
- **[Service Management Commands](../README.md#service-management)** - Essential justfile commands for daily use ⭐

### Immediate Validation
- **[Testing Guide](../README.md#monitoring--testing)** - Verify your installation works correctly
- **[Dashboard Access](../README.md#port-configuration)** - URLs and credentials for all services

**💡 First Time?** Start with `just setup` - it handles everything automatically with validation.

---

## 🏢 Team Deployment  

**Focus**: Deploy monitoring for entire development teams

### Team Setup & Management
- **[Team Setup Guide](../README-TEAM.md)** - Complete team deployment with hook management ⭐
- **[Team Management Commands](../README-TEAM.md#team-management-commands)** - Service management for teams
- **[Team Troubleshooting](../README-TEAM.md#troubleshooting)** - Team-specific diagnostic procedures

### Hook Deployment
- **[Hook System Overview](../CUSTOM-METRICS-GUIDE.md#current-implementation)** - How automatic metric collection works
- **[Hook Installation](../README.md#deploy-claude-code-hooks)** - Installing hooks for team members

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

**💡 Emergency Commands**:
```bash
just status              # Quick health overview
just monitor validate    # Full system check
just test all           # Comprehensive testing
```

---

## 📖 System Overview

**Focus**: Understanding the monitoring system architecture and capabilities  

### Architecture
The Claude Code monitoring system uses a modern observability stack:

```
Claude Code → production-tool-hook.sh → Pushgateway (7101)
                                            ↓
                                       Prometheus (7100)  
                                            ↓
                                        Grafana (7102)
```

### Key Components
- **Production Hook System**: Automatically captures every Claude Code tool use
- **Prometheus**: Time-series metrics storage and querying
- **Pushgateway**: Receives metrics from Claude Code hooks  
- **Grafana**: Visualization dashboards and alerting
- **Python Helper Scripts**: Service management and operations

### Capabilities
- ✅ **Real-time Monitoring**: Every tool use is captured automatically
- ✅ **Cost Estimation**: Track estimated Claude Code costs over time
- ✅ **Usage Analytics**: Understand tool usage patterns and productivity
- ✅ **Team Insights**: Monitor usage across team members and sessions
- ✅ **Production Ready**: Health checking, data persistence, error recovery

**💡 Full Details**: [Complete ROI Implementation Guide](../claude_code_roi_full.md)

---

## 🎓 Learning Path Recommendations

### For Beginners
1. Start with [Quick Start](../README.md#quick-start) - get basic monitoring running
2. Deploy hooks with [Hook Installation](../README.md#deploy-claude-code-hooks) 
3. Explore dashboards and understand [Basic Metrics](../METRICS-REFERENCE.md)

### For Teams  
1. Review [Team Setup Guide](../README-TEAM.md)
2. Master [Team Management Commands](../README-TEAM.md#team-management-commands)
3. Understand [Troubleshooting Procedures](../README-TEAM.md#troubleshooting)

### For Power Users
1. Study the [Complete Justfile System](../JUSTFILE-GUIDE.md)
2. Learn [Advanced Service Management](../JUSTFILE-GUIDE.md#advanced-service-operations)  
3. Create [Custom Metrics](../CUSTOM-METRICS-GUIDE.md) for your specific needs

### For Data Analysis
1. Master [Metrics Reference](../METRICS-REFERENCE.md) with query examples
2. Understand [Hook-Based vs Official Metrics](../METRICS-REFERENCE.md#available-metrics)
3. Build custom dashboards with [Dashboard Management](../JUSTFILE-GUIDE.md#dashboard-management)

---

## 📋 Document Status Legend

- ⭐ **Essential Reading** - Core documents for successful operation
- 🆕 **Recently Updated** - Contains latest improvements and fixes  
- 🏗️ **In Progress** - Documents being actively improved
- 📚 **Reference** - Detailed technical specifications

---

## 🆘 Need Help?

**Stuck on setup?** → [Quick Start Path](#quick-start) → `just setup`  
**Services not working?** → [Emergency Commands](#critical-essential-commands) → `just monitor validate`  
**Hook issues?** → [Troubleshooting](#troubleshooting) → `just test hooks`  
**Team deployment?** → [Team Path](#team-deployment) → [Team Guide](../README-TEAM.md)  
**Advanced operations?** → [Service Management](#service-management) → [Justfile Guide](../JUSTFILE-GUIDE.md)

**💡 Remember**: This monitoring system is designed to be **simple to use** but **powerful in capabilities**. The justfile commands hide complexity while providing production-grade monitoring for your Claude Code usage.