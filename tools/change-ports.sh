#!/bin/bash

# Port Configuration Script for Claude Code Monitoring
# Easily change all ports to avoid conflicts

set -e

# Default ports (change these to your preferred ports)
OLD_GRAFANA_PORT=3000
OLD_PROMETHEUS_PORT=9090
OLD_OTEL_GRPC_PORT=4317
OLD_OTEL_HTTP_PORT=4318

# New ports (customize these!)
NEW_GRAFANA_PORT=${1:-3030}      # Default to 3030 if not provided
NEW_PROMETHEUS_PORT=${2:-9091}   # Default to 9091
NEW_OTEL_GRPC_PORT=${3:-4327}    # Default to 4327
NEW_OTEL_HTTP_PORT=${4:-4328}    # Default to 4328

echo "🔄 Port Configuration Update"
echo "=============================="
echo "Current → New Port Mappings:"
echo "  Grafana:     $OLD_GRAFANA_PORT → $NEW_GRAFANA_PORT"
echo "  Prometheus:  $OLD_PROMETHEUS_PORT → $NEW_PROMETHEUS_PORT"
echo "  OTEL gRPC:   $OLD_OTEL_GRPC_PORT → $NEW_OTEL_GRPC_PORT"
echo "  OTEL HTTP:   $OLD_OTEL_HTTP_PORT → $NEW_OTEL_HTTP_PORT"
echo ""

# Function to update port in file
update_port() {
    local file=$1
    local old_port=$2
    local new_port=$3
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/:$old_port/:$new_port/g" "$file"
        sed -i '' "s/localhost:$old_port/localhost:$new_port/g" "$file"
        sed -i '' "s/0\.0\.0\.0:$old_port/0.0.0.0:$new_port/g" "$file"
    else
        # Linux
        sed -i "s/:$old_port/:$new_port/g" "$file"
        sed -i "s/localhost:$old_port/localhost:$new_port/g" "$file"
        sed -i "s/0\.0\.0\.0:$old_port/0.0.0.0:$new_port/g" "$file"
    fi
}

# Stop services if running
echo "🛑 Stopping any running services..."
docker-compose down 2>/dev/null || true

# Update docker-compose.yml
echo "📝 Updating docker-compose.yml..."
update_port "docker-compose.yml" $OLD_GRAFANA_PORT $NEW_GRAFANA_PORT
update_port "docker-compose.yml" $OLD_PROMETHEUS_PORT $NEW_PROMETHEUS_PORT
update_port "docker-compose.yml" $OLD_OTEL_GRPC_PORT $NEW_OTEL_GRPC_PORT
update_port "docker-compose.yml" $OLD_OTEL_HTTP_PORT $NEW_OTEL_HTTP_PORT

# Update setup-monitoring.sh
echo "📝 Updating setup-monitoring.sh..."
update_port "setup-monitoring.sh" $OLD_GRAFANA_PORT $NEW_GRAFANA_PORT
update_port "setup-monitoring.sh" $OLD_PROMETHEUS_PORT $NEW_PROMETHEUS_PORT
update_port "setup-monitoring.sh" $OLD_OTEL_GRPC_PORT $NEW_OTEL_GRPC_PORT

# Update otel-collector-config.yaml
echo "📝 Updating otel-collector-config.yaml..."
update_port "otel-collector-config.yaml" $OLD_OTEL_GRPC_PORT $NEW_OTEL_GRPC_PORT
update_port "otel-collector-config.yaml" $OLD_OTEL_HTTP_PORT $NEW_OTEL_HTTP_PORT

# Update documentation files
echo "📝 Updating documentation..."
for file in LOCAL-CUSTOMIZATIONS.md troubleshooting.md claude_code_roi_full.md; do
    if [ -f "$file" ]; then
        update_port "$file" $OLD_GRAFANA_PORT $NEW_GRAFANA_PORT
        update_port "$file" $OLD_PROMETHEUS_PORT $NEW_PROMETHEUS_PORT
        update_port "$file" $OLD_OTEL_GRPC_PORT $NEW_OTEL_GRPC_PORT
        update_port "$file" $OLD_OTEL_HTTP_PORT $NEW_OTEL_HTTP_PORT
    fi
done

# Update telemetry environment if it exists
if [ -f "$HOME/.claude/telemetry-env.sh" ]; then
    echo "📝 Updating telemetry environment..."
    update_port "$HOME/.claude/telemetry-env.sh" $OLD_OTEL_GRPC_PORT $NEW_OTEL_GRPC_PORT
fi

echo ""
echo "✅ Port configuration updated!"
echo ""
echo "📊 New service URLs:"
echo "   Grafana:    http://localhost:$NEW_GRAFANA_PORT (admin/admin)"
echo "   Prometheus: http://localhost:$NEW_PROMETHEUS_PORT"
echo "   OTEL gRPC:  localhost:$NEW_OTEL_GRPC_PORT"
echo "   OTEL HTTP:  localhost:$NEW_OTEL_HTTP_PORT"
echo ""
echo "🚀 To start services with new ports:"
echo "   ./setup-monitoring.sh start"
echo ""
echo "📡 Remember to update your telemetry config:"
echo "   ./setup-monitoring.sh enable"
echo "   source ~/.claude/telemetry-env.sh"