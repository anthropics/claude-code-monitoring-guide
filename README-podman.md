# Running with Podman on macOS

This guide covers running the Claude Code monitoring stack using Podman instead of Docker Desktop on macOS.

## Prerequisites

- macOS 12+ (Monterey or later)
- Homebrew installed

## Installation

```bash
# Install Podman and podman-compose
brew install podman podman-compose

# Initialize and start the Podman machine (Linux VM)
podman machine init
podman machine start

# Verify installation
podman --version        # Should be >= 4.0
podman-compose --version # Should be >= 1.0
```

## Quick Start

```bash
# Clone or navigate to the repo
cd claude-code-monitoring-guide

# (Optional) Copy and customize environment variables
cp .env.example .env
# Edit .env to change GF_ADMIN_PASSWORD if desired

# Start the stack
podman compose -f podman-compose.yaml up -d

# View logs
podman compose -f podman-compose.yaml logs -f
```

## Verify the Stack

### 1. Check containers are running

```bash
podman compose -f podman-compose.yaml ps
```

Expected output:
```
NAME                    STATUS
prometheus              Up
grafana                 Up
<project>-otel-collector-1   Up
```

### 2. Test service endpoints

```bash
# Prometheus UI
curl -s http://localhost:9090/-/ready && echo "Prometheus: OK"

# Grafana UI
curl -s http://localhost:3000/api/health && echo "Grafana: OK"

# OTel Collector metrics
curl -s http://localhost:8889/metrics | head -5 && echo "OTel Collector: OK"
```

### 3. Verify inter-container DNS resolution

```bash
# Exec into prometheus and verify it can resolve otel-collector
podman exec prometheus wget -qO- http://otel-collector:8889/metrics | head -3

# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | grep -o '"health":"[^"]*"' | head -5
```

If targets show `"health":"up"`, DNS resolution is working correctly.

## Access the UIs

| Service    | URL                      | Default Credentials |
|------------|--------------------------|---------------------|
| Grafana    | http://localhost:3000    | admin / admin       |
| Prometheus | http://localhost:9090    | (no auth)           |

## Stop the Stack

```bash
# Stop and remove containers (preserves volumes)
podman compose -f podman-compose.yaml down

# Stop and remove containers AND volumes (full cleanup)
podman compose -f podman-compose.yaml down -v
```

## Troubleshooting

### "Cannot connect to Podman" error

```bash
# Ensure the Podman machine is running
podman machine list
podman machine start
```

### Port already in use

```bash
# Check what's using the port
lsof -i :3000  # or :9090, :4317, etc.

# Kill the process or change the port in podman-compose.yaml
```

### Volume permission issues

If you see permission errors in container logs:

```bash
# Option 1: Use userns=keep-id (add to service in podman-compose.yaml)
# userns_mode: keep-id

# Option 2: Reset volumes
podman compose -f podman-compose.yaml down -v
podman compose -f podman-compose.yaml up -d
```

### Container DNS not resolving

If Prometheus can't reach `otel-collector:8889`:

```bash
# Check the network exists
podman network ls

# Inspect the network
podman network inspect claude-code-monitoring-guide_default

# Restart with explicit network recreation
podman compose -f podman-compose.yaml down
podman compose -f podman-compose.yaml up -d
```

### Slow startup on first run

First run pulls ~500MB of images. Subsequent starts are fast.

```bash
# Pre-pull images
podman pull docker.io/otel/opentelemetry-collector-contrib:latest
podman pull docker.io/prom/prometheus:latest
podman pull docker.io/grafana/grafana:latest
```

## Differences from Docker Compose

For this specific stack, there are **no functional differences**. The `podman-compose.yaml` is semantically identical to `docker-compose.yml`.

Key compatibility notes:
- Podman Compose uses the same Compose spec as Docker Compose
- Named volumes work identically
- Container name DNS resolution works in the default bridge network
- Port mappings are identical
- Bind mounts work (macOS home directory is auto-mounted in Podman machine)

### Minor syntax adjustments made

| Change | Reason |
|--------|--------|
| Added `docker.io/` prefix to images | Explicit registry (Podman default, but clearer) |
| Added `:ro` to config bind mounts | Best practice for read-only configs |
| Parameterized `GF_SECURITY_ADMIN_PASSWORD` | Avoid hardcoded secrets; uses `.env` |

## Using Both Docker and Podman

You can keep both files:
- `docker-compose.yml` - For Docker Desktop users
- `podman-compose.yaml` - For Podman users

They are functionally equivalent and can coexist.
