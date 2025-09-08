#!/bin/bash

# Claude Code Monitoring Setup Script

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function start_monitoring() {
    echo "🚀 Starting monitoring stack..."
    cd "$SCRIPT_DIR"
    docker-compose up -d
    
    echo "⏳ Waiting for services to be ready..."
    sleep 5
    
    echo "✅ Monitoring stack started!"
    echo "   📊 Grafana: http://localhost:3030 (admin/admin)"
    echo "   📈 Prometheus: http://localhost:9091"
}

function stop_monitoring() {
    echo "🛑 Stopping monitoring stack..."
    cd "$SCRIPT_DIR"
    docker-compose down
    echo "✅ Monitoring stack stopped"
}

function enable_telemetry() {
    echo "📡 Enabling Claude Code telemetry..."
    
    # Create a shell config file for Claude Code telemetry
    cat > "$HOME/.claude/telemetry-env.sh" << 'EOF'
# Claude Code Telemetry Configuration
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:7110
export OTEL_METRIC_EXPORT_INTERVAL=30000  # 30 seconds
EOF
    
    echo "✅ Telemetry configuration saved to ~/.claude/telemetry-env.sh"
    echo ""
    echo "To use telemetry with Claude Code, run:"
    echo "   source ~/.claude/telemetry-env.sh && claude"
    echo ""
    echo "Or add this to your shell profile for permanent setup:"
    echo "   echo 'source ~/.claude/telemetry-env.sh' >> ~/.zshrc"
}

function disable_telemetry() {
    echo "📡 Disabling Claude Code telemetry..."
    
    cat > "$HOME/.claude/telemetry-env.sh" << 'EOF'
# Claude Code Telemetry Configuration (DISABLED)
unset CLAUDE_CODE_ENABLE_TELEMETRY
unset OTEL_METRICS_EXPORTER
unset OTEL_EXPORTER_OTLP_PROTOCOL
unset OTEL_EXPORTER_OTLP_ENDPOINT
unset OTEL_METRIC_EXPORT_INTERVAL
EOF
    
    echo "✅ Telemetry disabled"
}

function test_telemetry() {
    echo "🧪 Testing telemetry..."
    
    # Test with console output first
    export CLAUDE_CODE_ENABLE_TELEMETRY=1
    export OTEL_METRICS_EXPORTER=console
    export OTEL_METRIC_EXPORT_INTERVAL=1000
    
    echo "Running test command..."
    claude -p "say hello" 2>&1 | head -20
    
    echo ""
    echo "If you see metrics output above, telemetry is working!"
}

function show_status() {
    echo "📊 Current Status:"
    echo ""
    
    # Check if monitoring stack is running
    if docker-compose ps 2>/dev/null | grep -q "Up"; then
        echo "✅ Monitoring stack: RUNNING"
        docker-compose ps
    else
        echo "❌ Monitoring stack: STOPPED"
    fi
    
    echo ""
    
    # Check telemetry env vars
    if [ -n "$CLAUDE_CODE_ENABLE_TELEMETRY" ]; then
        echo "✅ Telemetry: ENABLED"
        echo "   Exporter: $OTEL_METRICS_EXPORTER"
        echo "   Endpoint: $OTEL_EXPORTER_OTLP_ENDPOINT"
    else
        echo "❌ Telemetry: DISABLED"
    fi
}

function usage() {
    cat << EOF
Claude Code Monitoring Setup

Usage: $0 [command]

Commands:
    start       Start the monitoring stack (Prometheus + Grafana)
    stop        Stop the monitoring stack
    enable      Enable Claude Code telemetry
    disable     Disable Claude Code telemetry
    test        Test telemetry output
    status      Show current status
    help        Show this help message

Quick Start:
    $0 start     # Start monitoring stack
    $0 enable    # Enable telemetry
    source ~/.claude/telemetry-env.sh && claude  # Run Claude with telemetry

EOF
}

# Main script
case "${1:-}" in
    start)
        start_monitoring
        ;;
    stop)
        stop_monitoring
        ;;
    enable)
        enable_telemetry
        ;;
    disable)
        disable_telemetry
        ;;
    test)
        test_telemetry
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        usage
        exit 1
        ;;
esac