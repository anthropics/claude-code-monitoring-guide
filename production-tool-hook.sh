#!/bin/bash

# Production tool usage hook using real Claude JSON stdin data
# Sends metrics to Prometheus pushgateway

PUSHGATEWAY_URL="http://localhost:7101"

# Read JSON from stdin
JSON_DATA=$(cat)

# Extract session_id from JSON for user_id lookup
SESSION_ID=$(echo "$JSON_DATA" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('session_id', 'unknown'))")

# Get user_id using session correlation, but prefer readable user info
HASHED_USER_ID=$("$(dirname "$0")/scripts/get_claude_user_id_simple.sh" "$SESSION_ID")

# Try to get more readable user identification
GIT_EMAIL=$(git config user.email 2>/dev/null)
GIT_NAME=$(git config user.name 2>/dev/null)
SYSTEM_USER=$(whoami 2>/dev/null)

# Use the most informative identifier available
if [[ -n "$GIT_EMAIL" ]]; then
    USER_ID="$GIT_EMAIL"
elif [[ -n "$GIT_NAME" ]]; then
    USER_ID="$GIT_NAME"
elif [[ -n "$SYSTEM_USER" ]]; then
    USER_ID="$SYSTEM_USER"
else
    USER_ID="$HASHED_USER_ID"
fi

# Parse JSON with Python and send metrics
export JSON_DATA
export USER_ID
export SESSION_ID
export PUSHGATEWAY_URL

python3 << 'EOF'
import json
import sys
import subprocess
import os
from pathlib import Path

# Parse the JSON data from environment
json_data = os.environ.get('JSON_DATA', '{}')
try:
    data = json.loads(json_data)
except json.JSONDecodeError as e:
    print(f'Error parsing JSON: {e}', file=sys.stderr)
    sys.exit(1)

# Extract core fields  
session_id = os.environ.get('SESSION_ID', 'unknown')
tool_name = data.get('tool_name', 'unknown')
tool_input = data.get('tool_input', {})
tool_result = data.get('tool_result', {})
cwd = data.get('cwd', 'unknown')

# Use the same user identifier that AI agents use (standard USER env var)
user_id = os.environ.get('USER', os.environ.get('USER_ID', 'unknown'))
pushgateway_url = os.environ.get('PUSHGATEWAY_URL', 'http://localhost:9092')

# Check if this is PreToolUse or PostToolUse
hook_type = data.get('hook_type', 'unknown')
is_pre_tool = hook_type == 'PreToolUse' or 'tool_result' not in data
is_post_tool = hook_type == 'PostToolUse' or 'tool_result' in data

# Get timestamp (current time if not provided)
import time
timestamp = data.get('timestamp', time.time())

# Extract file information
file_path = tool_input.get('file_path', '')
file_extension = 'unknown'
if file_path:
    try:
        file_extension = Path(file_path).suffix.lstrip('.') or 'no_extension'
    except:
        file_extension = 'unknown'

# Extract agent information for Task tool
agent_type = 'unknown'
task_description = ''
prompt_length = 0
if tool_name == 'Task':
    agent_type = tool_input.get('subagent_type', 'unknown')
    task_description = tool_input.get('description', '')
    prompt_length = len(tool_input.get('prompt', ''))

# Categorize task by description keywords
task_category = 'other'
if tool_name == 'Task' and task_description:
    desc_lower = task_description.lower()
    if any(word in desc_lower for word in ['search', 'find', 'grep', 'look']):
        task_category = 'search'
    elif any(word in desc_lower for word in ['setup', 'config', 'install', 'deploy']):
        task_category = 'setup'
    elif any(word in desc_lower for word in ['write', 'code', 'implement', 'create']):
        task_category = 'coding'
    elif any(word in desc_lower for word in ['fix', 'debug', 'error', 'troubleshoot']):
        task_category = 'debugging'
    elif any(word in desc_lower for word in ['read', 'analyze', 'understand', 'check']):
        task_category = 'analysis'

# Extract bash commands - raw first command for general tracking
command = tool_input.get('command', '')
bash_command = 'other'
just_subcommand = ''
git_subcommand = ''
gt_subcommand = ''

if command and tool_name == 'Bash':
    # Clean up command and get the actual executable
    cleaned_cmd = command.strip()
    
    # Get first word as the raw command
    parts = cleaned_cmd.split()
    if parts:
        bash_command = parts[0]
        # Remove common shell operators and get clean command
        bash_command = bash_command.split('|')[0].split('&&')[0].split('||')[0].split(';')[0]
        
        # Special handling for just - capture the subcommand
        if bash_command == 'just' and len(parts) > 1:
            just_subcommand = parts[1]
        
        # Special handling for git - capture the subcommand  
        elif bash_command == 'git' and len(parts) > 1:
            git_subcommand = parts[1]
        
        # Special handling for gt - capture the subcommand
        elif bash_command == 'gt' and len(parts) > 1:
            gt_subcommand = parts[1]

# Determine operation type for tools
operation_type = 'other'
if tool_name == 'Read':
    operation_type = 'read'
elif tool_name == 'Write':
    operation_type = 'write'
elif tool_name == 'Edit' or tool_name == 'MultiEdit':
    operation_type = 'edit'
elif tool_name == 'Bash':
    operation_type = 'bash'
elif tool_name in ['Glob', 'Grep']:
    operation_type = 'search'
elif tool_name == 'TodoWrite':
    operation_type = 'todo'
elif tool_name in ['WebFetch', 'WebSearch']:
    operation_type = 'web'
elif tool_name == 'Task':
    operation_type = 'agent'
elif tool_name in ['LS', 'NotebookEdit']:
    operation_type = 'file_ops'

# Build metrics payload - compatible with stock dashboard
metrics_lines = []

# Estimate cost (rough approximation - $0.001 per tool use)
estimated_cost_usd = 0.001
model = "sonnet"  # Default model assumption

# Estimate tokens (rough approximation based on tool and content)
estimated_tokens = 100  # Base tokens per tool use
if tool_name == 'Read':
    estimated_tokens = 500
elif tool_name == 'Write':
    estimated_tokens = 800
elif tool_name == 'Edit':
    estimated_tokens = 300
elif tool_name == 'Bash':
    estimated_tokens = 200
elif tool_name in ['Grep', 'Glob']:
    estimated_tokens = 150

# Estimate lines of code (for file operations)
estimated_loc = 0
if tool_name in ['Write', 'Edit', 'MultiEdit'] and file_path:
    # Rough estimate based on tool type
    if tool_name == 'Write':
        estimated_loc = 50  # New file
    elif tool_name in ['Edit', 'MultiEdit']:
        estimated_loc = 10  # Modified lines

# Generate stock dashboard compatible metrics
# 1. Cost usage metric
metrics_lines.append('# TYPE claude_code_cost_usage_USD_total counter')
metrics_lines.append(f'claude_code_cost_usage_USD_total{{session_id="{session_id}",user_id="{user_id}",model="{model}",tool="{tool_name}"}} {estimated_cost_usd}')

# 2. Token usage metric  
metrics_lines.append('# TYPE claude_code_token_usage_tokens_total counter')
metrics_lines.append(f'claude_code_token_usage_tokens_total{{session_id="{session_id}",user_id="{user_id}",model="{model}",type="input"}} {estimated_tokens}')

# 3. Lines of code metric (only for file operations)
if estimated_loc > 0:
    metrics_lines.append('# TYPE claude_code_lines_of_code_count_total counter')
    metrics_lines.append(f'claude_code_lines_of_code_count_total{{session_id="{session_id}",user_id="{user_id}",type="{operation_type}",file_extension="{file_extension}"}} {estimated_loc}')

# Keep some custom metrics for detailed tracking
metrics_lines.append('# TYPE claude_custom_tool_usage_total counter') 
metrics_lines.append(f'claude_custom_tool_usage_total{{session_id="{session_id}",user="{user_id}",tool="{tool_name}",operation_type="{operation_type}",file_extension="{file_extension}"}} 1')

# Bash command metric (detailed tracking)
if command and tool_name == 'Bash':
    metrics_lines.append('# TYPE claude_custom_bash_commands_total counter')
    metrics_lines.append(f'claude_custom_bash_commands_total{{session_id="{session_id}",user="{user_id}",bash_command="{bash_command}"}} 1')
    
    # Special just subcommand tracking
    if just_subcommand:
        metrics_lines.append('# TYPE claude_custom_just_subcommands_total counter')
        metrics_lines.append(f'claude_custom_just_subcommands_total{{session_id="{session_id}",user="{user_id}",just_subcommand="{just_subcommand}"}} 1')
    
    # Special git subcommand tracking
    if git_subcommand:
        metrics_lines.append('# TYPE claude_custom_git_subcommands_total counter')
        metrics_lines.append(f'claude_custom_git_subcommands_total{{session_id="{session_id}",user="{user_id}",git_subcommand="{git_subcommand}"}} 1')
    
    # Special gt subcommand tracking
    if gt_subcommand:
        metrics_lines.append('# TYPE claude_custom_gt_subcommands_total counter')
        metrics_lines.append(f'claude_custom_gt_subcommands_total{{session_id="{session_id}",user="{user_id}",gt_subcommand="{gt_subcommand}"}} 1')

# Duration tracking and sub-tool counting for Task tools
task_duration = 0
sub_tool_count = 0
task_success = 'unknown'

if tool_name == 'Task':
    # Create a unique task ID for tracking
    task_id = f"{session_id}_{tool_name}_{agent_type}"
    temp_dir = "/tmp/claude_task_tracking"
    
    # Ensure temp directory exists
    import os
    os.makedirs(temp_dir, exist_ok=True)
    
    if is_pre_tool:
        # Store start time for duration calculation
        start_file = f"{temp_dir}/{task_id}_start"
        with open(start_file, 'w') as f:
            f.write(str(timestamp))
    
    elif is_post_tool:
        # Calculate duration if we have start time
        start_file = f"{temp_dir}/{task_id}_start"
        try:
            if os.path.exists(start_file):
                with open(start_file, 'r') as f:
                    start_time = float(f.read().strip())
                task_duration = timestamp - start_time
                os.remove(start_file)  # Clean up
        except:
            task_duration = 0
        
        # Count sub-tools by analyzing result content
        result_text = str(tool_result)
        # Look for tool usage indicators in the result
        tool_indicators = ['Read:', 'Write:', 'Edit:', 'Bash:', 'Grep:', 'Glob:', 'LS:', 'Task:', 'WebFetch:']
        sub_tool_count = sum(1 for indicator in tool_indicators if indicator.lower() in result_text.lower())
        
        # Determine success (rough heuristic)
        error_indicators = ['error', 'failed', 'exception', 'traceback']
        has_errors = any(indicator in result_text.lower() for indicator in error_indicators)
        task_success = 'failure' if has_errors else 'success'

# Agent metrics (detailed Task tool tracking)
if tool_name == 'Task':
    # Always send basic usage metrics on PreToolUse
    if is_pre_tool:
        metrics_lines.append('# TYPE claude_custom_agent_usage_total counter')
        metrics_lines.append(f'claude_custom_agent_usage_total{{session_id="{session_id}",user="{user_id}",agent_type="{agent_type}",task_category="{task_category}"}} 1')
        
        # Agent prompt complexity metric
        metrics_lines.append('# TYPE claude_custom_agent_prompt_length_total counter') 
        metrics_lines.append(f'claude_custom_agent_prompt_length_total{{session_id="{session_id}",user="{user_id}",agent_type="{agent_type}"}} {prompt_length}')
        
        # Agent task count by type
        metrics_lines.append('# TYPE claude_custom_agent_tasks_by_type_total counter')
        metrics_lines.append(f'claude_custom_agent_tasks_by_type_total{{session_id="{session_id}",user="{user_id}",agent_type="{agent_type}",task_category="{task_category}"}} 1')
    
    # Send enhanced metrics on PostToolUse
    elif is_post_tool and task_duration > 0:
        # Task duration metric
        metrics_lines.append('# TYPE claude_custom_agent_duration_seconds_total counter')
        metrics_lines.append(f'claude_custom_agent_duration_seconds_total{{session_id="{session_id}",user="{user_id}",agent_type="{agent_type}",task_category="{task_category}"}} {task_duration}')
        
        # Sub-tool usage metric
        metrics_lines.append('# TYPE claude_custom_agent_subtools_total counter')
        metrics_lines.append(f'claude_custom_agent_subtools_total{{session_id="{session_id}",user="{user_id}",agent_type="{agent_type}",task_category="{task_category}"}} {sub_tool_count}')
        
        # Task success metric
        metrics_lines.append('# TYPE claude_custom_agent_success_total counter')
        metrics_lines.append(f'claude_custom_agent_success_total{{session_id="{session_id}",user="{user_id}",agent_type="{agent_type}",task_success="{task_success}"}} 1')

# Join all metrics with newlines and add final newline
metrics_payload = '\n'.join(metrics_lines) + '\n'

# Send to pushgateway using curl with timestamp to ensure uniqueness
# This prevents overwriting the same metric and ensures proper counter accumulation
import time
timestamp_id = int(time.time() * 1000)  # millisecond timestamp for uniqueness
url = f'{pushgateway_url}/metrics/job/claude_code_tools/instance/{user_id}/session/{session_id}/tool/{tool_name}/ts/{timestamp_id}'
try:
    result = subprocess.run(
        ['curl', '-X', 'POST', '--data-binary', metrics_payload, url],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    if result.returncode == 0:
        print(f'✅ Tool metric sent: {tool_name} ({operation_type})', file=sys.stderr)
    else:
        print(f'❌ Failed to send metric: {result.stderr}', file=sys.stderr)
except Exception as e:
    print(f'❌ Error sending metric: {e}', file=sys.stderr)

EOF

exit 0