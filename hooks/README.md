# Hooks Directory

Contains Claude Code hook scripts for monitoring and metric collection.

## Main Hook (at root level)
- **[`../production-tool-hook.sh`](../production-tool-hook.sh)** - Primary hook for automatic tool usage tracking

## Development & Debug Hooks
- **[`debug-pretool-hook.sh`](debug-pretool-hook.sh)** - Debug PreToolUse events
- **[`debug-stdin-hook.sh`](debug-stdin-hook.sh)** - Debug JSON stdin parsing  
- **[`debug-tool-hook.sh`](debug-tool-hook.sh)** - General hook debugging
- **[`minimal-tool-hook.sh`](minimal-tool-hook.sh)** - Minimal hook example

## Specialized Hooks
- **[`tool-usage-hook.sh`](tool-usage-hook.sh)** - Specialized tool usage tracking
- **[`send-custom-metric.sh`](send-custom-metric.sh)** - Custom metric sender

## Usage

The main production hook is installed automatically via:
```bash
just deploy hooks
```

Development hooks can be tested manually:
```bash
./hooks/debug-tool-hook.sh
./hooks/minimal-tool-hook.sh
```