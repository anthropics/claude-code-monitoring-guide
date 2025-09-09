<!-- Auto attached rules -->

@docs/INDEX.md
@JUSTFILE-GUIDE.md
@METRICS-REFERENCE.md
@troubleshooting.md
@README.md

## 🎯 MUNINN CLAUDE CODE ADAPTER CORE RULES

### 🚀 CORE MONITORING WORKFLOW

**For monitoring setup**: Always start with validation workflow below (all commands from `infrastructure/` directory)
**For operational issues**: Use diagnostic commands first before manual interventions

**Essential Commands:**
```bash
# Navigate to infrastructure directory first
cd infrastructure

# FIRST-TIME SETUP (complete workflow)
just setup                    # Prerequisite check + service start + validation
just deploy hooks            # Install Claude Code adapter hooks for current user  
just test all               # Comprehensive system validation

# DAILY OPERATIONS
just status                  # Quick health overview + service URLs
just up                     # Start all monitoring services  
just monitor validate       # Full stack health check

# TROUBLESHOOTING WORKFLOW
just monitor status         # Service health diagnostics
just test hooks            # Validate Claude Code adapter hook system
just service logs <service> # Debug specific service issues
just service restart <service> # Fix problematic services
```

### 📍 CRITICAL RESOURCE REFERENCES
```
┌─────────────────────────────────────────────────────┐
│ 📍 CRITICAL RESOURCE REFERENCES (Muninn Structure)   │
├─────────────────────────────────────────────────────┤
│ • docs/INDEX.md - Complete documentation map        │
│ • JUSTFILE-GUIDE.md - Production service management │
│ • METRICS-REFERENCE.md - All metrics + queries     │
│ • troubleshooting.md - Diagnostic procedures        │
│ • adapters/claude/README.md - Claude adapter guide │
│ • README-TEAM.md - Team deployment guide           │
└─────────────────────────────────────────────────────┘
```

---

## 🤖 MONITORING SYSTEM CRITICAL THINKING

**Be systematic about monitoring issues and don't immediately jump to complex solutions.** Follow the diagnostic hierarchy: service health → hook validation → metric flow → dashboard refresh. Most issues are resolved at the service level.

**Examples of When to Use Systematic Diagnosis:**
- Dashboard showing no data → Check service health first, not dashboard queries
- Hooks not working → Validate hook installation before debugging scripts  
- Metrics missing → Test metric flow end-to-end before investigating Prometheus queries
- Performance issues → Check service resource usage before scaling solutions

**Recommended Diagnostic Pattern:**
1. Navigate to `infrastructure/` directory for all operations
2. Run `just status` to check overall system health
3. Run `just monitor validate` for comprehensive validation  
4. Run `just test <specific>` to isolate the problematic component
5. Use `just service logs <service>` to debug specific issues
6. Only after system-level diagnosis, investigate application-level problems

---

## 📊 MONITORING STACK ARCHITECTURE (CRITICAL)

**FUNDAMENTAL DISTINCTION - Service Management vs Metrics vs Dashboards:**

### 🏗️ Service Management: `just up/down/restart` (for infrastructure)
- **Docker Compose orchestration** - manages container lifecycle
- Components: prometheus, pushgateway, grafana, otel-collector
- Creates/manages: containers, networks, volumes, health checks
- **Examples**: `just up`, `just service restart grafana`, `just down`

### 📈 Metrics Collection: `production-tool-hook.sh` (for data capture)
- **Claude Code hooks** - captures tool usage automatically with timestamp-based counter accumulation
- Components: production-tool-hook.sh with breakthrough timestamp uniqueness fix
- Generates: claude_custom_* metrics series for Tools, Bash, Agents, MCP
- **Examples**: Every Read, Write, Edit, Bash, Task, MCP command generates metrics

### 📋 4 Production Dashboards (WORKING NOW)
- **🔧 Tool Usage**: http://localhost:7102/d/claude-tool-usage-simple
  - Total/unique tools, tool breakdown, file types, operations
- **💻 Bash Commands**: http://localhost:7102/d/claude-bash-commands  
  - Raw commands, categories, just subcommands
- **🤖 Agents**: http://localhost:7102/d/claude-agents
  - Agent types, task categories, usage counts, prompt lengths
- **🔌 MCP**: http://localhost:7102/d/claude-mcp
  - Server usage (context7, linear), categories, individual tools

---

## 🔧 PORT ORGANIZATION (MANDATORY KNOWLEDGE)

**All services use organized 7100+ port range for conflict avoidance:**

```bash
# Production Port Configuration (7100+ range)
Prometheus:    7100  # Metrics storage and querying
Pushgateway:   7101  # Receives metrics from hooks  
Grafana:       7102  # Dashboard visualization
OTEL Collector: 7110-7112  # Advanced telemetry (optional)

# Quick Access URLs
http://localhost:7100  # Prometheus (metrics/targets)
http://localhost:7101  # Pushgateway (raw metrics)  
http://localhost:7102  # Grafana (admin/admin)
```

**WHY 7100+ range?** Avoids conflicts with common development ports (3000s, 8000s, 9000s) and provides organized, memorable port assignments.

---

## 🚨 CLAUDE CODE ADAPTER HOOK SYSTEM ARCHITECTURE (CRITICAL)

**FUNDAMENTAL UNDERSTANDING - How the Muninn Claude Code adapter actually works:**

### 🎣 Hook Installation: `just deploy hooks` (from infrastructure/)
- **Target**: `~/.claude/settings.json` configuration  
- **Process**: Installs `adapters/claude/hooks/production-tool-hook.sh` with PreToolUse/PostToolUse events
- **Scope**: Per-user installation, captures ALL Claude Code tool usage for Muninn
- **Validation**: Use `just deploy validate` to verify installation

### 📊 Metric Generation: `adapters/claude/hooks/production-tool-hook.sh`
- **Trigger**: Every Claude Code tool use (Read, Write, Edit, Bash, etc.)
- **Process**: JSON stdin → Python parsing → HTTP POST to Pushgateway
- **Output**: claude_code_* metrics (cost, tokens, LOC) + claude_custom_* metrics (detailed tracking)
- **Endpoint**: http://localhost:7101/metrics/job/claude_code_tools/...

### 🔄 Data Flow: Hook → Pushgateway → Prometheus → Grafana
```
Claude Code Tool Use → production-tool-hook.sh → Pushgateway (7101)
                                                        ↓
                                                  Prometheus (7100)
                                                        ↓  
                                                   Grafana (7102)
```

---

## 🧪 TESTING METHODOLOGY (MANDATORY)

**All monitoring changes must be validated with comprehensive testing**

### Testing Hierarchy (Bottom-Up Validation)
```bash
# 1. Service Health (Infrastructure Layer)
just status                    # Are all containers running?
just monitor status           # Are all services responding?

# 2. Hook Validation (Data Collection Layer)  
just test hooks              # Is hook script working?
just deploy validate         # Are hooks properly installed?

# 3. Metric Flow (Data Pipeline Layer)
just test metrics           # Is metric collection working?
just test flow             # Is end-to-end data flow working?

# 4. Dashboard Validation (Visualization Layer)  
just dashboard list         # Are dashboards available?
# Manual: Check http://localhost:7102 for data visualization
```

### Test-Driven Monitoring Approach
- **Red**: Service down, hooks not working, no metrics flowing
- **Green**: All tests pass, metrics flowing, dashboards showing data
- **Refactor**: Optimize queries, improve dashboards, tune service performance

---

## 📋 OPERATIONAL WORKFLOWS (ESSENTIAL)

### Daily Startup Workflow
```bash
just status                  # Check current service state
just up                     # Start services if needed  
just monitor validate       # Validate entire stack
# Claude Code usage automatically generates metrics
```

### New Team Member Onboarding
```bash
just setup                  # Complete stack setup
just deploy hooks          # Install hooks for new user
just test all             # Validate everything works
# Share dashboard URLs: http://localhost:7102
```

### Troubleshooting Workflow  
```bash
just status                 # Quick health check
just monitor validate      # Comprehensive validation
just test <specific>       # Isolate problematic component
just service logs <service> # Debug specific service
just service restart <service> # Fix problematic service
```

### Dashboard Management Workflow
```bash
just dashboard list        # See available dashboards
just dashboard backup      # Backup before changes
just dashboard publish <name> # Deploy updated dashboard
# Test changes in http://localhost:7102
```

---

## 🎯 MONITORING SUCCESS CRITERIA

**A successful Claude Code monitoring deployment should demonstrate:**

✅ **Service Health**: `just status` shows all services healthy  
✅ **Hook Integration**: `just test hooks` passes validation  
✅ **Metric Flow**: `just test flow` shows end-to-end data movement  
✅ **Dashboard Functionality**: Grafana dashboards show real usage data  
✅ **Team Adoption**: Multiple users generating metrics via installed hooks  
✅ **Operational Excellence**: Issues resolved via justfile commands, not manual Docker manipulation

**Failure Modes to Avoid:**
❌ Manual Docker commands instead of justfile service management  
❌ Port conflicts due to ignoring 7100+ range organization
❌ Hook installation failures due to skipping validation steps
❌ Dashboard data issues due to skipping metric flow testing  
❌ Service instability due to skipping health checks

---

## 🔍 MONITORING OBSERVABILITY META-PRINCIPLE

**Monitor your monitoring system**: Use the justfile commands to validate that the monitoring system itself is healthy. A monitoring system that can't self-diagnose its health is unreliable for monitoring anything else.

**Evidence of Health:**
- `just status` consistently shows green/healthy services
- `just test all` passes all validation checks  
- Dashboard refresh shows recent metric updates (< 5 minutes old)
- Hook installation validation passes for all team members
- Service restart/recovery works reliably via justfile commands