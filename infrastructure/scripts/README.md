# Scripts Directory

Python and shell scripts for managing the Claude Code monitoring system.

## Core Scripts

### Service Management
- **[`service_manager.py`](service_manager.py)** - Docker service orchestration and health checking
- **[`monitor_manager.py`](monitor_manager.py)** - Monitoring validation and status reporting
- **[`dashboard_manager.py`](dashboard_manager.py)** - Dashboard CRUD operations
- **[`test_manager.py`](test_manager.py)** - Comprehensive testing utilities
- **[`deploy_manager.py`](deploy_manager.py)** - Hook deployment and configuration

### User ID Management
- **[`get_claude_user_id_simple.sh`](get_claude_user_id_simple.sh)** - Session-based correlation to get real Claude Code user_id

## User ID Synchronization

The `get_claude_user_id_simple.sh` script ensures hook metrics use the same `user_id` as real Claude Code telemetry through session correlation:

**How it works:**
1. Takes `session_id` from Claude Code hook JSON data as parameter
2. Queries metrics endpoint for existing telemetry with matching `session_id` 
3. Extracts the `user_id` from real telemetry (e.g., `4650d18b4a405a18e1be90ef7164b4e66e77a083239706a49a1f438580f1d7d9`)
4. Falls back to system username only if no telemetry data exists

**Usage:**
```bash
# Get user_id for a specific session_id
./scripts/get_claude_user_id_simple.sh "bb6e40fd-c85d-414c-a26f-6c97e36bb384"

# Used automatically by production-tool-hook.sh
SESSION_ID=$(echo "$JSON_DATA" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('session_id', 'unknown'))")
USER_ID=$("$(dirname "$0")/scripts/get_claude_user_id_simple.sh" "$SESSION_ID")
```

**Benefits:**
- ✅ **Session correlation** - Uses session_id to match hook data with real telemetry
- ✅ **No hardcoding** - No personal data embedded in scripts
- ✅ **Team compatible** - Works automatically on any team member's machine  
- ✅ **Simple logic** - No complex Prometheus queries or fallback chains
- ✅ **Generic deployment** - Same script works for entire team

This ensures accurate user counts and unified metrics across the monitoring stack through session-based correlation.