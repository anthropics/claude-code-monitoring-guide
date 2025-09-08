#!/bin/bash

# Claude Code Monitoring - Team Deployment Script
# Sets up REAL OpenTelemetry monitoring for Claude Code

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "===================================================="
echo "     Claude Code OTEL Monitoring - Team Setup      "
echo "===================================================="
echo ""

# 1. Check prerequisites
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Prerequisites met"
echo ""

# 2. Start monitoring stack
echo "Starting monitoring stack..."

cd "$SCRIPT_DIR"

# Check for port conflicts and use alternate ports if needed
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 3000 in use, using 3030 for Grafana"
    if [ -f change-ports.sh ]; then
        ./change-ports.sh
    fi
fi

# Start the stack
docker-compose up -d

echo "✅ Monitoring stack started"
echo ""

# 3. Wait for services
echo "Waiting for services to be ready..."
sleep 10

# 4. Configure Claude Code telemetry
echo "Configuring Claude Code telemetry..."

# Create telemetry config script
cat > "$HOME/.claude-telemetry.sh" << 'EOF'
#!/bin/bash
# Claude Code OpenTelemetry Configuration

# Enable telemetry
export CLAUDE_CODE_ENABLE_TELEMETRY=1

# Configure OTLP exporter to send to local OTEL collector
export OTEL_METRICS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:7110

# Set metric export interval (30 seconds)
export OTEL_METRIC_EXPORT_INTERVAL=30000
export OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=delta
EOF

chmod +x "$HOME/.claude-telemetry.sh"

echo "✅ Telemetry configuration created"
echo ""

# 5. Add to shell profile
echo "Adding telemetry to shell profile..."

SHELL_RC=""
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
else
    SHELL_RC="$HOME/.profile"
fi

# Add telemetry source if not present
if ! grep -q "claude-telemetry.sh" "$SHELL_RC" 2>/dev/null; then
    cat >> "$SHELL_RC" << 'EOF'

# Claude Code OpenTelemetry
if [ -f "$HOME/.claude-telemetry.sh" ]; then
    source "$HOME/.claude-telemetry.sh"
fi
EOF
    echo "✅ Added to $SHELL_RC"
else
    echo "✅ Already configured in $SHELL_RC"
fi

# 6. Test telemetry
echo ""
echo "Testing telemetry..."

# Source the config
source "$HOME/.claude-telemetry.sh"

# Quick test
export OTEL_METRICS_EXPORTER=console
export OTEL_METRIC_EXPORT_INTERVAL=1000

echo "Running test command..."
claude -p "test" 2>/dev/null | head -20

# Reset to OTLP
export OTEL_METRICS_EXPORTER=otlp
export OTEL_METRIC_EXPORT_INTERVAL=30000

echo ""
echo "===================================================="
echo "            Setup Complete! 🎉                     "
echo "===================================================="
echo ""
echo "📊 Dashboards available at:"
echo "   http://localhost:3030/d/claude-code-working/claude-code-working-dashboard"
echo ""
echo "   Username: admin"
echo "   Password: admin"
echo ""
echo "📈 What's being tracked (REAL metrics):"
echo "   • Cost per session by model (Haiku/Sonnet/Opus)"
echo "   • Token usage (input/output/cache)"
echo "   • Lines of code generated"
echo "   • Session duration and count"
echo ""
echo "🔄 Next steps:"
echo "   1. Restart your terminal (or run: source ~/.zshrc)"
echo "   2. Run Claude Code normally"
echo "   3. Metrics will appear in dashboard after ~1 minute"
echo ""
echo "🛠  Useful commands:"
echo "   docker-compose ps        # Check monitoring stack"
echo "   docker-compose logs -f   # View logs"
echo "   docker-compose down      # Stop monitoring"
echo ""
echo "===================================================="