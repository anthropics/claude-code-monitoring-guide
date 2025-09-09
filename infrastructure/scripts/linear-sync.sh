#!/bin/bash

# Linear Daily Sync Script  
# Pulls last 200 completed Linear issues and converts to Prometheus metrics
# No duplication - overwrites metrics on each run
# Uses proper virtual environment and managed dependencies

set -e  # Exit on any error

PUSHGATEWAY_URL="http://localhost:7101/metrics"
JOB_NAME="linear_daily"
SCRIPT_DIR="$(dirname "$0")"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

# Change to repo directory
cd "$REPO_DIR"

# Activate Python virtual environment
if [[ -d "venv" ]]; then
    echo "🐍 Activating Python virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run 'just setup' first."
    exit 1
fi

# Check for linearis CLI
if [[ ! -f "node_modules/.bin/linearis" ]]; then
    echo "❌ Linearis CLI not found. Run 'just setup' to install dependencies."
    exit 1
fi

LINEARIS_CLI="./node_modules/.bin/linearis"

# Check for Linear API token
if [[ -z "${LINEAR_API_TOKEN:-}" ]] && [[ ! -f ".env" ]]; then
    echo "❌ Linear API token not found."
    echo "💡 Create a .env file with LINEAR_API_TOKEN=your_token"
    echo "   Or export LINEAR_API_TOKEN=your_token"
    echo "   Get your token from: https://linear.app/settings/api"
    exit 1
fi

# Load environment variables if .env exists
if [[ -f ".env" ]]; then
    echo "📄 Loading environment variables from .env file..."
    source .env
fi

# Create temp files for Linear data
TEMP_DIR="/tmp/linear_sync"
mkdir -p "$TEMP_DIR"

LINEAR_DATA_FILE="$TEMP_DIR/linear_completed_issues.json"
METRICS_FILE="$TEMP_DIR/linear_metrics.txt"

echo "🔄 Starting Linear data sync..."

# Use Linearis CLI to get completed issues from all teams
echo "📊 Fetching last 200 completed Linear issues from all teams..."

# Check if API token is available
if [[ -z "${LINEAR_API_TOKEN:-}" ]]; then
    echo "❌ LINEAR_API_TOKEN environment variable not set"
    exit 1
fi

echo "🔍 Using Linearis CLI to fetch completed issues..."

# Calculate date 30 days ago
THIRTY_DAYS_AGO=$(date -v-30d +%Y-%m-%d 2>/dev/null || date -d '30 days ago' +%Y-%m-%d)

# Use linearis to fetch completed issues from Linear
# Use search with Done state to get actually completed issues
if $LINEARIS_CLI \
    --api-token "$LINEAR_API_TOKEN" \
    issues search \
    --states "Done" \
    -l 200 "" > "$LINEAR_DATA_FILE" 2>/dev/null; then
    
    if [[ -s "$LINEAR_DATA_FILE" ]] && jq empty "$LINEAR_DATA_FILE" 2>/dev/null; then
        echo "✅ Successfully fetched Linear data"
        ISSUE_COUNT=$(jq '. | length' "$LINEAR_DATA_FILE" 2>/dev/null || echo "0")
        echo "📈 Found $ISSUE_COUNT completed issues"
        
        # Show the data for debugging
        echo "📋 Sample data:"
        jq -r '.[] | "  - \(.identifier): \(.title)"' "$LINEAR_DATA_FILE" 2>/dev/null | head -3
    else
        echo "❌ No valid Linear JSON data found"
        exit 1
    fi
else
    echo "❌ Failed to fetch Linear data from Linearis CLI"
    echo "💡 Make sure your LINEAR_API_TOKEN is valid and you have access to the organization"
    exit 1
fi

# Convert Linear data to Prometheus metrics
echo "🔄 Converting Linear data to Prometheus metrics..."

# Create empty metrics file for timestamped metrics
> "$METRICS_FILE"

# Process each completed issue with Python
python3 << 'PYTHON_EOF'
import json
import sys
from datetime import datetime, timedelta, timezone
import os

try:
    with open('/tmp/linear_sync/linear_completed_issues.json', 'r') as f:
        data = json.load(f)
    
    # Linearis CLI returns data as a simple array: [...]
    all_issues = data if isinstance(data, list) else []
    
    # Process all completed issues (already filtered to "Done" by linearis search)
    issues = []
    
    for issue in all_issues:
        # Skip issues without assignees
        assignee = issue.get('assignee', {})
        if not assignee:
            continue
            
        # Use updatedAt as fallback if completedAt is missing (Linear API quirk)
        completed_date = issue.get('completedAt') or issue.get('updatedAt')
        if not completed_date:
            continue
            
        issues.append(issue)
    
    print(f"Processed {len(issues)} completed issues from {len(all_issues)} total issues")
    
    metrics = []
    current_timestamp = int(datetime.now().timestamp())
    
    # Track completions by user, type, priority, and day
    user_completions = {}
    type_completions = {}
    priority_completions = {}
    daily_completions = {}
    
    for issue in issues:
        # Linearis CLI JSON format fields (email not available, using name)
        assignee_obj = issue.get('assignee', {})
        assignee_name = assignee_obj.get('name', 'unknown') if assignee_obj else 'unknown'
        # Create mock email for metrics (since actual email not available from linearis)
        assignee = assignee_name.lower().replace(' ', '.') + '@degreeanalytics.com' if assignee_name != 'unknown' else 'unknown'
        
        # Issue details
        issue_id = issue.get('identifier', 'unknown')  # ENG-123 format
        title = issue.get('title', '').replace('"', '\\"')[:50]  # Truncate and escape
        
        # Priority from Linearis (numeric value 0-4)
        priority_num = issue.get('priority', 0)
        priority_map = {0: 'None', 1: 'Urgent', 2: 'High', 3: 'Medium', 4: 'Low'}
        priority = priority_map.get(priority_num, 'Unknown')
        
        # Get completion date (use completedAt or updatedAt as fallback)
        date_field = issue.get('completedAt') or issue.get('updatedAt', '')
        completed_date = date_field.split('T')[0] if date_field else 'unknown'  # Extract date part
        
        # Issue type/label (Linear doesn't have explicit types, use first label or 'Task')
        labels = issue.get('labels', []) if issue.get('labels') else []
        issue_type = labels[0].get('name', 'Task') if labels else 'Task'
        
        # Count by user
        if assignee not in user_completions:
            user_completions[assignee] = 0
        user_completions[assignee] += 1
        
        # Count by type
        if issue_type not in type_completions:
            type_completions[issue_type] = 0
        type_completions[issue_type] += 1
        
        # Count by priority
        if priority not in priority_completions:
            priority_completions[priority] = 0
        priority_completions[priority] += 1
        
        # Count by day
        if completed_date not in daily_completions:
            daily_completions[completed_date] = 0
        daily_completions[completed_date] += 1
    
    # Generate timestamped metrics
    def date_to_timestamp(date_str):
        """Convert date string like '2025-09-05' to Unix timestamp at noon UTC"""
        if date_str == 'unknown':
            return current_timestamp
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            # Set to noon UTC for consistent daily timestamps
            noon_datetime = date_obj.replace(hour=12, minute=0, second=0, tzinfo=timezone.utc)
            return int(noon_datetime.timestamp())
        except:
            return current_timestamp
    
    with open('/tmp/linear_sync/linear_metrics.txt', 'a') as f:
        # Daily completions (no timestamps - Pushgateway doesn't accept them)
        for date, count in daily_completions.items():
            f.write(f'linear_daily_completions{{date="{date}"}} {count}\n')
        
        # Generate individual completion events for better time filtering
        daily_user_completions = {}
        daily_priority_completions = {}
        daily_type_completions = {}
        
        for issue in issues:
            # Get issue details
            assignee_obj = issue.get('assignee', {})
            assignee_name = assignee_obj.get('name', 'unknown') if assignee_obj else 'unknown'
            user = assignee_name.lower().replace(' ', '.') + '@degreeanalytics.com' if assignee_name != 'unknown' else 'unknown'
            
            # Priority
            priority_num = issue.get('priority', 0)
            priority_map = {0: 'None', 1: 'Urgent', 2: 'High', 3: 'Medium', 4: 'Low'}
            priority = priority_map.get(priority_num, 'Unknown')
            
            # Type
            labels = issue.get('labels', []) if issue.get('labels') else []
            issue_type = labels[0].get('name', 'Task') if labels else 'Task'
            
            # Completion date
            date_field = issue.get('completedAt') or issue.get('updatedAt', '')
            completed_date = date_field.split('T')[0] if date_field else 'unknown'
            
            # Count by user+day
            user_day_key = f"{user}:{completed_date}"
            if user_day_key not in daily_user_completions:
                daily_user_completions[user_day_key] = 0
            daily_user_completions[user_day_key] += 1
            
            # Count by priority+day
            priority_day_key = f"{priority}:{completed_date}"
            if priority_day_key not in daily_priority_completions:
                daily_priority_completions[priority_day_key] = 0
            daily_priority_completions[priority_day_key] += 1
            
            # Count by type+day
            type_day_key = f"{issue_type}:{completed_date}"
            if type_day_key not in daily_type_completions:
                daily_type_completions[type_day_key] = 0
            daily_type_completions[type_day_key] += 1
        
        # Write user completions by day (no timestamps)
        for user_day_key, count in daily_user_completions.items():
            user, date = user_day_key.split(':', 1)
            user_clean = user.replace('@', '_').replace('.', '_').replace('-', '_')
            f.write(f'linear_user_completions{{user="{user}",user_clean="{user_clean}",date="{date}"}} {count}\n')
        
        # Write priority completions by day (no timestamps)  
        for priority_day_key, count in daily_priority_completions.items():
            priority, date = priority_day_key.split(':', 1)
            f.write(f'linear_priority_completions{{priority="{priority}",date="{date}"}} {count}\n')
        
        # Write type completions by day (no timestamps)
        for type_day_key, count in daily_type_completions.items():
            issue_type, date = type_day_key.split(':', 1)
            f.write(f'linear_type_completions{{type="{issue_type}",date="{date}"}} {count}\n')
        
        # Sync metadata (no timestamps)
        f.write(f'linear_last_sync_timestamp {current_timestamp}\n')
        total_issues = len(issues)
        f.write(f'linear_total_issues_synced {total_issues}\n')
        
        print(f"✅ Generated metrics for {total_issues} completed issues")
        print(f"👥 Users: {list(user_completions.keys())}")
        print(f"📋 Types: {list(type_completions.keys())}")

except Exception as e:
    print(f"❌ Error processing Linear data: {e}")
    sys.exit(1)
    
PYTHON_EOF

if [[ $? -ne 0 ]]; then
    echo "❌ Failed to convert Linear data to metrics"
    exit 1
fi

# Send metrics to Pushgateway
echo "📊 Sending metrics to Pushgateway..."

if curl -s --data-binary @"$METRICS_FILE" "$PUSHGATEWAY_URL/job/$JOB_NAME" > /dev/null; then
    echo "✅ Successfully sent Linear metrics to Pushgateway"
    echo "🔗 View metrics: http://localhost:7101/metrics"
    echo "📊 View in Prometheus: http://localhost:7100/graph?g0.expr=linear_completion"
else
    echo "❌ Failed to send metrics to Pushgateway"
    exit 1
fi

# Keep temp files for debugging
echo "🐛 Debug: Temp files kept in $TEMP_DIR for inspection"

echo "🎉 Linear sync completed successfully!"
echo ""
echo "Next steps:"
echo "1. Check metrics in Prometheus: http://localhost:7100"
echo "2. View Linear dashboard in Grafana: http://localhost:7102"
echo "3. Set up daily cron job: just linear cron"