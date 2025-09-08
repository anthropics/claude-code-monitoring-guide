# Justfile System Guide

## 🚀 Overview

The Claude Code monitoring repository includes a comprehensive `justfile` that provides a production-grade service management system. This guide explains all available commands and their usage.

## 📋 Quick Reference

```bash
# Essential Commands
just setup                    # Complete initial setup
just up                       # Start all services
just status                   # Check service health & URLs
just deploy hooks             # Install Claude Code hooks

# Get Help
just help                     # Show all commands
just help-services            # Service management help
just help-monitoring          # Monitoring operations help
just help-dashboards          # Dashboard management help
just help-deployment          # Deployment and setup help
```

## 🏗️ Service Management

### Core Commands

**`just up [services]`**
- Starts monitoring services (default: all)
- Includes health checks and status reporting
- Shows service URLs and credentials

```bash
just up                        # Start all services
just up prometheus,grafana     # Start specific services
```

**`just down`**
- Stops all monitoring services
- Preserves data volumes

**`just restart [services]`**
- Restarts services (default: all)
- Equivalent to down + up with health checks

**`just status`**
- Shows comprehensive service status
- Lists all service URLs
- Quick health overview

### Advanced Service Operations

**`just service <action> [service]`**
- Unified service control with multiple actions:
  - `up` - Start services
  - `down` - Stop services  
  - `restart` - Restart services
  - `status` - Show service status
  - `console` - Show URLs and credentials
  - `logs` - Follow service logs
  - `clean` - Clean up containers

```bash
just service console grafana   # Show Grafana URL/credentials
just service logs prometheus   # Tail Prometheus logs
just service restart pushgateway # Restart pushgateway only
```

## 📊 Monitoring & Testing

### Health Checking

**`just monitor <action> [service]`**
- Comprehensive monitoring operations:
  - `status` - Service health status
  - `logs` - Tail service logs
  - `validate` - Validate entire stack
  - `metrics-count` - Show detailed metrics

```bash
just monitor status            # Check all services
just monitor validate          # Full stack validation
just monitor logs grafana      # Tail Grafana logs
```

### Testing System

**`just test <type>`**
- Test monitoring components:
  - `hooks` - Test hook execution and JSON parsing
  - `metrics` - Test metrics collection and pushgateway
  - `flow` - Test end-to-end metrics flow
  - `all` - Run all tests

```bash
just test hooks               # Test Claude Code hooks
just test all                 # Run comprehensive tests
```

## 📋 Dashboard Management

**`just dashboard <action> [name]`**
- Complete dashboard lifecycle management:
  - `list` - List all dashboards
  - `publish <name>` - Deploy dashboard to Grafana
  - `update <name>` - Update existing dashboard
  - `export <name>` - Export dashboard from Grafana to file
  - `backup` - Export all dashboards to backup directory
  - `import <name>` - Import dashboard from file

```bash
just dashboard list                    # List available dashboards
just dashboard publish tool-usage      # Deploy tool-usage dashboard  
just dashboard backup                  # Export all to backup files
```

**Dashboard Locations:**
- `grafana/dashboards/` - Dashboard JSON files
- `grafana/provisioning/dashboards/` - Provisioned dashboards

## 🚀 Deployment & Setup

### Initial Setup

**`just setup`**
- Complete initial setup for new environments
- Checks prerequisites (Docker, Docker Compose)
- Starts all monitoring services
- Validates the installation  
- Shows next steps

### Hook Deployment

**`just deploy <action> [username]`**
- Deploy Claude Code hooks to user settings:
  - `hooks [username]` - Install production-tool-hook.sh
  - `validate [username]` - Verify hook installation

```bash
just deploy hooks              # Deploy for current user
just deploy hooks john         # Deploy for specific user
just deploy validate          # Verify deployment
```

### Configuration Management

**`just export-config [path]`**
- Export complete monitoring configuration to archive
- Default: `./claude-monitoring-config.tar.gz`
- Includes all configuration files and scripts

**`just import-config <path>`**
- Import monitoring configuration from archive
- Overwrites existing configuration files
- Preserves data volumes

```bash
just export-config backup.tar.gz      # Export to backup
just import-config backup.tar.gz      # Import from backup
```

## 🧹 Maintenance

**`just clean [level]`**
- Clean up containers and volumes
- Levels: `containers`, `volumes`, `all`

**`just reset --confirm`**
- Reset entire stack (DESTRUCTIVE)
- Requires confirmation flag for safety

## 🏢 Architecture

### Port Configuration

All services use organized **7100+ port range**:

| Service | Port | Description |
|---------|------|-------------|
| Prometheus | 7100 | Metrics collection and time-series database |
| Pushgateway | 7101 | Push gateway for Claude Code hook metrics |
| Grafana | 7102 | Monitoring dashboards and visualization |
| OTEL Collector | 7110-7112 | OpenTelemetry metrics collection |

### Service Stack

```
Claude Code → production-tool-hook.sh → Pushgateway (7101)
                                            ↓
                                       Prometheus (7100)
                                            ↓
                                        Grafana (7102)
```

## 🛠️ Helper Scripts

The justfile system uses Python helper scripts for advanced operations:

- **`scripts/service_manager.py`** - Docker service orchestration and health checking
- **`scripts/monitor_manager.py`** - Monitoring validation and status reporting  
- **`scripts/dashboard_manager.py`** - Dashboard CRUD operations
- **`scripts/test_manager.py`** - Comprehensive testing utilities
- **`scripts/deploy_manager.py`** - Hook deployment and configuration

## 💡 Usage Patterns

### Daily Operations

```bash
# Start your day
just status                   # Check if services are running
just up                      # Start if needed

# Deploy to new team member
just deploy hooks john       # Install hooks for user 'john'

# Check system health
just test all               # Run comprehensive tests
just monitor validate      # Validate entire stack
```

### Troubleshooting Workflow

```bash
# Something's not working
just status                 # Quick health check
just monitor validate      # Full validation
just service logs grafana  # Check specific service logs
just service restart prometheus # Restart problematic service
```

### Dashboard Management

```bash
# Working with dashboards  
just dashboard list         # See what's available
just dashboard backup       # Create backup before changes
just dashboard publish tool-usage # Deploy updated dashboard
```

### Configuration Updates

```bash
# Before major changes
just export-config backup-$(date +%Y%m%d).tar.gz

# After testing
just dashboard backup       # Save dashboard state
```

## 🔍 Advanced Tips

### Parallel Operations

The justfile system supports parallel service operations:

```bash
# These run in parallel automatically
just up                     # Starts all services concurrently
just service logs           # Tails multiple service logs  
```

### Service Dependencies

Services start in correct dependency order:
1. Prometheus (metrics storage)
2. Pushgateway (metrics collection)
3. Grafana (visualization)
4. OTEL Collector (advanced telemetry)

### Health Checking

All commands include built-in health checking:
- Service startup waits for readiness
- Status commands verify actual service health
- Restart operations include health validation

## 🚨 Error Handling

### Common Issues

**Port Conflicts:**
```bash
just down                   # Stop all services
just clean containers       # Clean up containers
just up                     # Restart with fresh containers
```

**Dashboard Not Loading:**
```bash
just service restart grafana    # Restart Grafana
just dashboard publish <name>   # Re-deploy dashboard
```

**Hooks Not Working:**
```bash
just deploy validate        # Check hook installation
just test hooks            # Test hook execution
```

### Safety Features

- **Confirmation Required**: Destructive operations require `--confirm` flag
- **Backup Prompts**: Import operations warn about overwrites
- **Health Validation**: All operations include health checks
- **Rollback Support**: Configuration import/export for easy rollback

## 📚 Related Documentation

- **[README.md](README.md)** - Main repository overview with quick start
- **[troubleshooting.md](troubleshooting.md)** - Troubleshooting guide with justfile commands
- **[METRICS-REFERENCE.md](METRICS-REFERENCE.md)** - Complete metrics reference
- **[README-TEAM.md](README-TEAM.md)** - Team deployment guide

---

**💡 Pro Tip**: Use `just help-<category>` for detailed help on specific command categories. The justfile system is designed to hide Docker complexity while providing production-grade service management capabilities.