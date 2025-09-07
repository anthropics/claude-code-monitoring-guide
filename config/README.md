# Config Directory

Contains configuration files for Claude Code hooks and monitoring setup.

## Configuration Files
- **[`hooks-config.json`](hooks-config.json)** - Claude Code hooks configuration
- **[`example-claude-hooks.json`](example-claude-hooks.json)** - Example hooks configuration

## Usage

These configurations are used by the deployment system:
```bash
just deploy hooks       # Uses these configs automatically
```

The hook configurations define:
- Event types (PreToolUse, PostToolUse, Compact, ToolUse)
- Hook scripts to execute
- Matching patterns for tools
- Command execution parameters