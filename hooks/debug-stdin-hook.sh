#!/bin/bash
# Debug hook to capture JSON data from stdin

echo "[STDIN DEBUG] Hook fired at $(date)" >> ".claude/stdin-debug.log"

# Read JSON from stdin and save it
cat > /tmp/hook-input.json

# Log the raw JSON
echo "[STDIN DEBUG] Raw JSON input:" >> ".claude/stdin-debug.log"
cat /tmp/hook-input.json >> ".claude/stdin-debug.log"
echo "" >> ".claude/stdin-debug.log"

# Parse with Python
python3 -c "
import json, sys
try:
    with open('/tmp/hook-input.json', 'r') as f:
        data = json.load(f)
    
    with open('.claude/stdin-debug.log', 'a') as log:
        log.write('[STDIN DEBUG] Parsed JSON:\\n')
        log.write(f'  Keys: {list(data.keys())}\\n')
        
        if 'tool_input' in data:
            log.write(f'  tool_input keys: {list(data[\"tool_input\"].keys())}\\n')
            if 'file_path' in data['tool_input']:
                log.write(f'  file_path: {data[\"tool_input\"][\"file_path\"]}\\n')
            if 'command' in data['tool_input']:
                log.write(f'  command: {data[\"tool_input\"][\"command\"]}\\n')
        
        log.write('  Full data: ' + json.dumps(data, indent=2) + '\\n')
        log.write('[STDIN DEBUG] ---\\n\\n')

except Exception as e:
    with open('.claude/stdin-debug.log', 'a') as log:
        log.write(f'[STDIN DEBUG] Error parsing JSON: {e}\\n')
        log.write('[STDIN DEBUG] ---\\n\\n')
"

exit 0