# Tools Directory

Contains utility scripts for setup, configuration, and maintenance.

## Setup & Deployment
- **[`setup-monitoring.sh`](setup-monitoring.sh)** - Legacy setup script (replaced by `just setup`)
- **[`team-deploy.sh`](team-deploy.sh)** - Legacy team deployment (replaced by `just deploy hooks`)

## Utility Scripts
- **[`change-ports.sh`](change-ports.sh)** - Port configuration utility
- **[`parse-session.sh`](parse-session.sh)** - Session data parsing utility
- **[`custom-metrics-sender.py`](custom-metrics-sender.py)** - Python-based custom metric sender

## Usage

**Recommended**: Use justfile commands instead of these tools directly:
```bash
just setup              # Instead of setup-monitoring.sh
just deploy hooks       # Instead of team-deploy.sh  
just service status     # Instead of manual utilities
```

**Direct usage** (if needed):
```bash
./tools/change-ports.sh
./tools/parse-session.sh
python3 ./tools/custom-metrics-sender.py
```