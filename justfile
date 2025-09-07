# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    Claude Code Monitoring System                            ║
# ║                                                                              ║
# ║ 🚀 Production-grade monitoring for Claude Code tool usage                   ║
# ║ 📊 Real-time metrics, dashboards, and hook monitoring                       ║
# ║ 🐳 Full Docker orchestration with clean port management                     ║
# ║ 🧪 Complete testing pipeline for hooks and metrics                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
# 📋 Type 'just' or 'just help' to see all available commands organized by category

# Load .env file automatically
set dotenv-load

# Use bash for all recipes to support pipefail and other bash features
set shell := ["bash", "-c"]

# Default task - shows organized help instead of raw list
_default:
    @just help

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           SERVICE MANAGEMENT                                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Start all monitoring services (Prometheus, Grafana, Pushgateway, OTEL)
# Usage: just up [services]
# Examples:
#   just up                      # Start all services
#   just up prometheus,grafana   # Start specific services
up services='all':
    @python3 scripts/service_manager.py --action up --services {{services}}

# Stop all monitoring services
down:
    @python3 scripts/service_manager.py --action down --services all

# Restart monitoring services
# Usage: just restart [services]
restart services='all':
    @python3 scripts/service_manager.py --action restart --services {{services}}

# Unified service management command
# Usage: just service <action> [service] [options]
# Actions: up, down, restart, status, console, logs, clean
# Services: all, prometheus, grafana, pushgateway, otel-collector
# Examples:
#   just service up prometheus           # Start Prometheus
#   just service console grafana         # Show Grafana URL/credentials
#   just service logs pushgateway        # Show pushgateway logs
#   just service status all              # Check all service health
#   just service clean                   # Clean up stopped containers
service action service='all' *args='':
    @python3 scripts/service_manager.py --action {{action}} --services {{service}} {{args}}

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                         MONITORING OPERATIONS                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Monitoring operations - status, logs, validation
# Usage: just monitor <action> [service] [options]
# Actions: status, logs, validate, metrics-count
# Examples:
#   just monitor status             # Check all services health
#   just monitor logs grafana       # Tail Grafana logs
#   just monitor validate           # Validate monitoring stack
#   just monitor metrics-count      # Count current metrics
monitor action service='all' *args='':
    @python3 scripts/monitor_manager.py --action {{action}} --service {{service}} {{args}}

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                         DASHBOARD MANAGEMENT                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Dashboard management operations
# Usage: just dashboard <action> [name] [options]
# Actions: list, publish, update, backup, export, import
# Examples:
#   just dashboard list                    # List all dashboards
#   just dashboard publish tool-usage      # Deploy tool-usage dashboard
#   just dashboard update tool-usage       # Update existing dashboard
#   just dashboard backup                  # Export all dashboards to files
#   just dashboard export tool-usage       # Export specific dashboard
dashboard action name='' *args='':
    @python3 scripts/dashboard_manager.py --action {{action}} --name {{name}} {{args}}

# Deploy AI tool agent dashboard to Grafana  
# Creates 1 dashboard: Claude Code - AI Tool Agents (7 clean panels)
# Usage: just deploy-ai-dashboards
deploy-ai-dashboards:
    @python3 scripts/deploy_ai_dashboards.py

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                            TESTING UTILITIES                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Test Claude Code hooks and metrics collection
# Usage: just test <type> [options]
# Types: hooks, agents, metrics, flow, all
# Examples:
#   just test hooks          # Test hook execution and JSON parsing
#   just test agents         # Test agent metrics collection (Task tools)
#   just test metrics        # Test metrics collection and pushgateway
#   just test flow           # Test end-to-end metrics flow
#   just test all            # Run all tests
test type='all' *args='':
    @python3 scripts/test_manager.py --type {{type}} {{args}}

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                         MAINTENANCE & UTILITIES                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Clean up Docker containers, volumes, and networks
# Usage: just clean [level]
# Levels: containers (default), volumes, all
# Examples:
#   just clean            # Remove stopped containers
#   just clean volumes    # Remove containers AND volumes (data loss!)
#   just clean all        # Nuclear option - remove everything
clean level='containers':
    @python3 scripts/service_manager.py --action clean --level {{level}}

# Reset the entire monitoring stack (DESTRUCTIVE)
# Usage: just reset [--confirm]
reset *args='':
    @if echo "{{args}}" | grep -q "\--confirm"; then \
        echo "🚨 Resetting entire monitoring stack..."; \
        just clean all; \
        docker-compose up -d; \
        echo "✅ Monitoring stack reset complete"; \
    else \
        echo "⚠️  This will destroy ALL data and reset the monitoring stack"; \
        echo "   Run 'just reset --confirm' if you're sure"; \
    fi

# Wipe all monitoring data (metrics, dashboards, settings) but keep configuration  
# Deletes: prometheus_data, grafana_data, pushgateway_data volumes
# Preserves: All configuration files, dashboard definitions, hooks, scripts
# Usage: just wipe [--confirm]
wipe *args='':
    @if echo "{{args}}" | grep -q "\--confirm"; then \
        echo "🚨 Wiping all monitoring data..."; \
        echo "📊 Stopping services..."; \
        docker-compose down; \
        echo "🗑️  Deleting data volumes..."; \
        docker volume rm claude-code-monitoring-guide_prometheus_data || true; \
        docker volume rm claude-code-monitoring-guide_grafana_data || true; \
        docker volume rm claude-code-monitoring-guide_pushgateway_data || true; \
        echo "🚀 Starting fresh services..."; \
        docker-compose up -d; \
        echo "✅ All monitoring data wiped - starting fresh!"; \
        echo "💡 Your configuration files and scripts are preserved"; \
    else \
        echo "💥 DESTRUCTIVE ACTION: This will permanently delete ALL monitoring data"; \
        echo "   📊 Metrics history (costs, tokens, sessions)"; \
        echo "   📋 Grafana data (dashboard customizations, annotations)"; \
        echo "   🔄 Pushgateway data (pending metrics)"; \
        echo ""; \
        echo "✅ PRESERVED: Configuration files, dashboards, hooks, scripts"; \
        echo ""; \
        echo "🚨 Run 'just wipe --confirm' if you understand the consequences"; \
    fi

# Check monitoring stack health and show key URLs
status:
    @echo "🔍 Claude Code Monitoring Stack Status"
    @echo "════════════════════════════════════════"
    @just monitor status
    @echo ""
    @echo "📊 Key URLs:"
    @echo "   Grafana:     http://localhost:7102 (admin/admin)"  
    @echo "   Prometheus:  http://localhost:7100"
    @echo "   Pushgateway: http://localhost:7101"
    @echo "   OTEL:        http://localhost:7112"

# Show comprehensive help with categories
help:
    @echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    @echo "║                    Claude Code Monitoring System                            ║"
    @echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    @echo ""
    @echo "🚀 SERVICE MANAGEMENT"
    @echo "   up [services]              Start monitoring services"
    @echo "   down                       Stop all services"  
    @echo "   restart [services]         Restart services"
    @echo "   service <action> [service] Unified service control"
    @echo "   status                     Show stack status & URLs"
    @echo ""
    @echo "📊 MONITORING & METRICS"
    @echo "   monitor <action> [service] Monitoring operations"  
    @echo "   test <type>                Test hooks and metrics"
    @echo ""
    @echo "📋 DASHBOARD MANAGEMENT"
    @echo "   dashboard <action> [name]  Dashboard operations"
    @echo ""
    @echo "🚀 DEPLOYMENT & SETUP"
    @echo "   setup                      Initial setup for new environments"
    @echo "   deploy hooks [user]        Deploy hooks to user's Claude settings"
    @echo "   mcp <action> [server]      MCP server management"
    @echo "   export config [path]       Export monitoring configuration"
    @echo "   import config <path>       Import monitoring configuration"
    @echo ""
    @echo "🧹 MAINTENANCE"
    @echo "   clean [level]              Clean up containers/volumes"
    @echo "   reset --confirm            Reset entire stack (DESTRUCTIVE)"
    @echo "   wipe --confirm             Wipe all data, keep config (DESTRUCTIVE)"
    @echo ""
    @echo "💡 Examples:"
    @echo "   just up                    # Start all services"
    @echo "   just service console grafana # Show Grafana URL"
    @echo "   just monitor status        # Check health"
    @echo "   just test hooks           # Test Claude hooks"
    @echo "   just dashboard list       # List dashboards"
    @echo "   just deploy-ai-dashboards # Deploy AI tool agent dashboard"
    @echo "   just setup                 # Setup monitoring for first time"
    @echo ""
    @echo "📖 Detailed help:"
    @echo "   just help-services         # Service management help"
    @echo "   just help-monitoring       # Monitoring operations help" 
    @echo "   just help-dashboards       # Dashboard management help"
    @echo "   just help-deployment       # Deployment and setup help"

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                       DEPLOYMENT & SETUP COMMANDS                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Initial setup for new environments
setup:
    @echo "🚀 Setting up Claude Code Monitoring Stack"
    @echo "════════════════════════════════════════════"
    @echo "1. Checking prerequisites..."
    @which docker > /dev/null || (echo "❌ Docker not found. Please install Docker first." && exit 1)
    @which docker-compose > /dev/null || (echo "❌ Docker Compose not found. Please install Docker Compose first." && exit 1)
    @which python3 > /dev/null || (echo "❌ Python 3 not found. Please install Python 3 first." && exit 1)
    @which node > /dev/null || (echo "❌ Node.js not found. Please install Node.js first." && exit 1)
    @echo "✅ Prerequisites check passed"
    @echo ""
    @echo "2. Setting up Python virtual environment..."
    @if [ ! -d "venv" ]; then \
        echo "🐍 Creating Python virtual environment..."; \
        python3 -m venv venv; \
    else \
        echo "✅ Virtual environment already exists"; \
    fi
    @echo "📦 Installing Python dependencies..."
    @. venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
    @echo ""
    @echo "3. Installing Node.js dependencies..."
    @npm install
    @echo ""
    @echo "4. Making scripts executable..."
    @chmod +x scripts/*.sh hooks/*.sh tools/*.sh || true
    @echo ""
    @echo "5. Starting monitoring services..."
    @just up
    @echo ""
    @echo "3. Waiting for services to initialize..."
    @sleep 10
    @echo ""
    @echo "4. Validating setup..."
    @just monitor validate
    @echo ""
    @echo "🎉 Setup complete! Your Claude Code monitoring stack is ready."
    @echo ""
    @echo "📊 Access your dashboards:"
    @echo "   Grafana:     http://localhost:7102 (admin/admin)"
    @echo "   Prometheus:  http://localhost:7100"
    @echo "   Pushgateway: http://localhost:7101"
    @echo ""
    @echo "💡 Next steps:"
    @echo "   • Run 'just deploy hooks' to setup Claude Code hooks"
    @echo "   • Run 'just test all' to verify everything is working"
    @echo "   • Run 'just dashboard publish tool-usage' to deploy dashboards"

# Deploy hooks to user's Claude settings
# Usage: just deploy hooks [username]
deploy action username='' *args='':
    @python3 scripts/deploy_manager.py --action {{action}} --username {{username}} {{args}}

# MCP server management - individual server control
# Usage: just mcp <action> [server]
# Actions: add, remove, list, available, help
# Examples:
#   just mcp available        # Show available servers in registry
#   just mcp add linear       # Add Linear server from registry
#   just mcp add context7     # Add Context7 server for documentation
#   just mcp add task-master  # Add Task Master server
#   just mcp remove linear    # Remove Linear server
#   just mcp list            # List configured servers
mcp action='help' server='':
    @python3 scripts/mcp_manager.py {{action}} {{server}}

# Export monitoring configuration
export-config path='./claude-monitoring-config.tar.gz':
    @echo "📦 Exporting Claude Code monitoring configuration..."
    @tar -czf {{path}} \
        docker-compose.yml \
        prometheus.yml \
        grafana/ \
        production-tool-hook.sh \
        *.json \
        scripts/ \
        justfile
    @echo "✅ Configuration exported to: {{path}}"
    @echo "💡 To import: just import-config {{path}}"

# Import monitoring configuration
import-config path:
    @echo "📥 Importing Claude Code monitoring configuration..."
    @if [ ! -f "{{path}}" ]; then echo "❌ Configuration file not found: {{path}}" && exit 1; fi
    @echo "⚠️  This will overwrite existing configuration files."
    @echo "   Backup your current setup if needed."
    @echo -n "Continue? (y/N): " && read answer && [ "$answer" = "y" ] || (echo "Cancelled." && exit 1)
    @tar -xzf {{path}}
    @echo "✅ Configuration imported successfully"
    @echo "💡 Run 'just up' to start services with new configuration"

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        DETAILED HELP COMMANDS                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Service management detailed help
help-services:
    @echo "🚀 SERVICE MANAGEMENT COMMANDS"
    @echo "════════════════════════════════════════════════════════════════════"
    @echo ""
    @echo "📋 AVAILABLE SERVICES:"
    @echo "   • prometheus    - Metrics collection and time-series database"
    @echo "   • pushgateway   - Push gateway for Claude Code hook metrics"  
    @echo "   • grafana       - Monitoring dashboards and visualization"
    @echo "   • otel-collector - OpenTelemetry metrics collection"
    @echo ""
    @echo "🔧 COMMANDS:"
    @echo ""
    @echo "  just up [services]"
    @echo "     Start monitoring services (default: all)"
    @echo "     Examples:"
    @echo "       just up                      # Start all services"
    @echo "       just up prometheus,grafana   # Start specific services"
    @echo ""
    @echo "  just down"
    @echo "     Stop all monitoring services"
    @echo ""
    @echo "  just restart [services]" 
    @echo "     Restart services (default: all)"
    @echo ""
    @echo "  just service <action> [service]"
    @echo "     Unified service control with actions:"
    @echo "       • up      - Start services"
    @echo "       • down    - Stop services"
    @echo "       • restart - Restart services"
    @echo "       • status  - Show service status"
    @echo "       • console - Show URLs and credentials"
    @echo "       • logs    - Follow service logs"
    @echo "       • clean   - Clean up containers"
    @echo ""
    @echo "  just status"
    @echo "     Show monitoring stack status and key URLs"

# Monitoring operations detailed help  
help-monitoring:
    @echo "📊 MONITORING & METRICS COMMANDS"
    @echo "════════════════════════════════════════════════════════════════════"
    @echo ""
    @echo "🔧 COMMANDS:"
    @echo ""
    @echo "  just monitor <action> [service]"
    @echo "     Monitoring operations with actions:"
    @echo "       • status        - Show service health status"
    @echo "       • logs          - Tail service logs"  
    @echo "       • validate      - Validate entire monitoring stack"
    @echo "       • metrics-count - Show detailed metrics count"
    @echo ""
    @echo "  just test <type>"
    @echo "     Test monitoring components:"
    @echo "       • hooks   - Test hook execution and JSON parsing"
    @echo "       • agents  - Test agent metrics collection (Task tools)"
    @echo "       • metrics - Test metrics collection and pushgateway"
    @echo "       • flow    - Test end-to-end metrics flow"
    @echo "       • all     - Run all tests"
    @echo ""
    @echo "💡 EXAMPLES:"
    @echo "   just monitor status             # Check all services"
    @echo "   just monitor logs grafana       # Tail Grafana logs"
    @echo "   just monitor validate           # Full stack validation"
    @echo "   just test hooks                 # Test Claude hooks"
    @echo "   just test agents                # Test agent metrics"
    @echo "   just test all                   # Run all tests"

# Dashboard management detailed help
help-dashboards:
    @echo "📋 DASHBOARD MANAGEMENT COMMANDS"  
    @echo "════════════════════════════════════════════════════════════════════"
    @echo ""
    @echo "🔧 COMMANDS:"
    @echo ""
    @echo "  just dashboard <action> [name]"
    @echo "     Dashboard operations with actions:"
    @echo "       • list           - List all dashboards"
    @echo "       • publish <name> - Deploy dashboard from local file to Grafana"
    @echo "       • update <name>  - Update existing dashboard"
    @echo "       • export <name>  - Export dashboard from Grafana to file"
    @echo "       • backup         - Export all dashboards to backup directory"
    @echo "       • import <name>  - Import dashboard from file"
    @echo ""
    @echo "💡 EXAMPLES:"
    @echo "   just dashboard list                    # List all dashboards"
    @echo "   just dashboard publish tool-usage      # Deploy tool-usage dashboard"
    @echo "   just dashboard update tool-usage       # Update existing dashboard"
    @echo "   just dashboard export tool-usage       # Export specific dashboard"
    @echo "   just dashboard backup                  # Export all to backup files"
    @echo "   just deploy-ai-dashboards              # Deploy AI tool agent dashboard"
    @echo ""
    @echo "📁 DASHBOARD LOCATIONS:"
    @echo "   • grafana/dashboards/                  # Dashboard JSON files"
    @echo "   • grafana/provisioning/dashboards/     # Provisioned dashboards"

# Deployment and setup detailed help
help-deployment:
    @echo "🚀 DEPLOYMENT & SETUP COMMANDS"
    @echo "════════════════════════════════════════════════════════════════════"
    @echo ""
    @echo "🔧 COMMANDS:"
    @echo ""
    @echo "  just setup"
    @echo "     Complete initial setup for new environments"
    @echo "     - Checks prerequisites (Docker, Docker Compose)"
    @echo "     - Starts all monitoring services"
    @echo "     - Validates the installation"
    @echo "     - Shows next steps"
    @echo ""
    @echo "  just deploy hooks [username]"
    @echo "     Deploy Claude Code hooks to user's settings"
    @echo "     - Installs production-tool-hook.sh"
    @echo "     - Configures Claude Code settings.json"
    @echo "     - Sets up hook events (PreToolUse, PostToolUse)"
    @echo ""
    @echo "  just mcp <action> [server]"
    @echo "     MCP server management (individual server control)"
    @echo "     Actions: add, remove, list, available, help"
    @echo "     - Registry-based server configuration"
    @echo "     - Supports SSE and stdio server types"
    @echo "     - Environment variable expansion from .env file"
    @echo ""
    @echo "  just export-config [path]"
    @echo "     Export complete monitoring configuration to archive"
    @echo "     Default: ./claude-monitoring-config.tar.gz"
    @echo ""
    @echo "  just import-config <path>"
    @echo "     Import monitoring configuration from archive"
    @echo "     - Overwrites existing configuration files"
    @echo "     - Preserves data volumes"
    @echo ""
    @echo "💡 EXAMPLES:"
    @echo "   just setup                             # Initial setup"
    @echo "   just deploy hooks john                 # Deploy hooks for user 'john'"
    @echo "   just mcp available                     # Show available MCP servers"
    @echo "   just mcp add context7                  # Add Context7 documentation server"
    @echo "   just mcp add linear                    # Add Linear workspace integration"
    @echo "   just export-config backup.tar.gz      # Export to backup.tar.gz"
    @echo "   just import-config backup.tar.gz      # Import from backup"

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           LINEAR INTEGRATION                                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Linear management command (auth, status, test, sync)
# Usage: just linear <action> [args...]
# Actions: auth, status, test, sync, help
linear action *args='':
    @python3 scripts/linear_manager.py --action {{action}} {{args}}

# Variables for service ports (clean 7100+ range)
PROMETHEUS_PORT := "7100"
PUSHGATEWAY_PORT := "7101" 
GRAFANA_PORT := "7102"
OTEL_GRPC_PORT := "7110"
OTEL_HTTP_PORT := "7111"  
OTEL_METRICS_PORT := "7112"