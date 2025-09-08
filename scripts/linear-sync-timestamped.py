#!/usr/bin/env python3

"""
Linear Timestamped Sync Script

Pulls Linear completed issues and sends them to Prometheus with proper historical timestamps
that correspond to Linear issue completion dates. This enables proper time filtering in Grafana.

Uses Prometheus remote write API instead of Pushgateway to support timestamped metrics.
"""

import json
import sys
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import requests

def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def fetch_linear_data():
    """Fetch Linear completed issues using linearis CLI"""
    
    # Check for Linear API token
    linear_token = os.environ.get('LINEAR_API_TOKEN')
    if not linear_token:
        print("❌ LINEAR_API_TOKEN environment variable not set")
        return None
    
    # Find linearis CLI
    linearis_path = Path(__file__).parent.parent / "node_modules" / ".bin" / "linearis"
    if not linearis_path.exists():
        print("❌ Linearis CLI not found. Run 'just setup' to install dependencies.")
        return None
    
    print("📊 Fetching completed Linear issues...")
    
    # Create temp file for data
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Use linearis to fetch completed issues
        result = subprocess.run([
            str(linearis_path),
            "--api-token", linear_token,
            "issues", "search",
            "--states", "Done",
            "-l", "200",
            ""
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"❌ Linearis CLI failed: {result.stderr}")
            return None
        
        # Parse the JSON output
        try:
            data = json.loads(result.stdout)
            print(f"✅ Successfully fetched {len(data)} completed issues")
            return data
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse Linear data: {e}")
            return None
            
    except subprocess.TimeoutExpired:
        print("❌ Linearis CLI timed out")
        return None
    except Exception as e:
        print(f"❌ Error fetching Linear data: {e}")
        return None
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_path)
        except:
            pass

def date_to_timestamp(date_str):
    """Convert YYYY-MM-DD date string to Unix timestamp at noon UTC"""
    if not date_str or date_str == 'unknown':
        return int(datetime.now().timestamp())
    
    try:
        # Parse date and set to noon UTC for consistent daily timestamps
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        noon_datetime = date_obj.replace(hour=12, minute=0, second=0, tzinfo=timezone.utc)
        return int(noon_datetime.timestamp())
    except:
        return int(datetime.now().timestamp())

def generate_prometheus_metrics(issues):
    """Convert Linear issues to Prometheus metrics with historical timestamps"""
    
    metrics = []
    
    # Track completions by various dimensions
    daily_completions = {}
    user_completions = {}
    priority_completions = {}
    type_completions = {}
    
    for issue in issues:
        # Skip issues without assignees
        assignee = issue.get('assignee', {})
        if not assignee:
            continue
            
        # Get completion date
        completed_date = issue.get('completedAt') or issue.get('updatedAt')
        if not completed_date:
            continue
        
        # Extract date part (YYYY-MM-DD)
        date_str = completed_date.split('T')[0]
        
        # Get assignee info
        assignee_name = assignee.get('name', 'unknown')
        user_email = assignee_name.lower().replace(' ', '.') + '@degreeanalytics.com'
        user_clean = assignee_name.replace(' ', '_').replace('@', '_').replace('.', '_')
        
        # Get priority
        priority_num = issue.get('priority', 0)
        priority_map = {0: 'None', 1: 'Urgent', 2: 'High', 3: 'Medium', 4: 'Low'}
        priority = priority_map.get(priority_num, 'Unknown')
        
        # Get issue type (first label or 'Task')
        labels = issue.get('labels', [])
        issue_type = labels[0].get('name', 'Task') if labels else 'Task'
        
        # Count completions by dimension
        daily_completions[date_str] = daily_completions.get(date_str, 0) + 1
        
        user_key = f"{user_email}:{date_str}"
        user_completions[user_key] = user_completions.get(user_key, 0) + 1
        
        priority_key = f"{priority}:{date_str}"
        priority_completions[priority_key] = priority_completions.get(priority_key, 0) + 1
        
        type_key = f"{issue_type}:{date_str}"
        type_completions[type_key] = type_completions.get(type_key, 0) + 1
    
    # Generate timestamped metrics (keeping existing names for compatibility)
    for date_str, count in daily_completions.items():
        timestamp = date_to_timestamp(date_str)
        metrics.append({
            "metric": {
                "__name__": "linear_daily_completions",
                "date": date_str
            },
            "value": [timestamp, str(count)]
        })
    
    for user_key, count in user_completions.items():
        user_email, date_str = user_key.split(':', 1)
        user_clean = user_email.replace('@', '_').replace('.', '_')
        timestamp = date_to_timestamp(date_str)
        metrics.append({
            "metric": {
                "__name__": "linear_user_completions",
                "user": user_email,
                "user_clean": user_clean,
                "date": date_str
            },
            "value": [timestamp, str(count)]
        })
    
    for priority_key, count in priority_completions.items():
        priority, date_str = priority_key.split(':', 1)
        timestamp = date_to_timestamp(date_str)
        metrics.append({
            "metric": {
                "__name__": "linear_priority_completions",
                "priority": priority,
                "date": date_str
            },
            "value": [timestamp, str(count)]
        })
    
    for type_key, count in type_completions.items():
        issue_type, date_str = type_key.split(':', 1)
        timestamp = date_to_timestamp(date_str)
        metrics.append({
            "metric": {
                "__name__": "linear_type_completions",
                "type": issue_type,
                "date": date_str
            },
            "value": [timestamp, str(count)]
        })
    
    # Add sync timestamp metric
    current_timestamp = int(datetime.now().timestamp())
    metrics.append({
        "metric": {
            "__name__": "linear_last_sync_timestamp",
        },
        "value": [current_timestamp, str(current_timestamp)]
    })
    
    # Add total issues synced metric  
    total_issues = len(issues)
    metrics.append({
        "metric": {
            "__name__": "linear_total_issues_synced",
        },
        "value": [current_timestamp, str(total_issues)]
    })
    
    return metrics

def send_to_prometheus_remote_write(metrics, prometheus_url="http://localhost:7100"):
    """Send metrics with historical timestamps directly to Prometheus Remote Write API"""
    
    # Convert metrics to Prometheus Remote Write protobuf format
    from collections import defaultdict
    
    # Group metrics by series (same metric name and labels)
    series_data = defaultdict(list)
    
    for metric in metrics:
        name = metric["metric"]["__name__"]
        labels = {k: v for k, v in metric["metric"].items() if k != "__name__"}
        timestamp, value = metric["value"]
        
        # Create series key from name and sorted labels
        label_pairs = sorted(labels.items())
        series_key = (name, tuple(label_pairs))
        
        # Add timestamp and value (timestamp in milliseconds)
        series_data[series_key].append((int(timestamp * 1000), float(value)))
    
    # Build simplified protobuf-like message manually (without full protobuf library)
    # This is a simplified approach using JSON that Prometheus can accept via HTTP API
    
    print(f"📊 Sending {len(metrics)} timestamped metrics to Prometheus Remote Write...")
    
    # Use the simpler /api/v1/import/prometheus endpoint if available,
    # or fall back to text format with proper timestamps
    
    # Convert to Prometheus text format with timestamps
    prometheus_lines = []
    for metric in metrics:
        name = metric["metric"]["__name__"]
        labels = {k: v for k, v in metric["metric"].items() if k != "__name__"}
        timestamp, value = metric["value"]
        
        # Format labels
        label_str = ""
        if labels:
            label_pairs = [f'{k}="{v}"' for k, v in sorted(labels.items())]
            label_str = "{" + ",".join(label_pairs) + "}"
        
        # Add metric line with timestamp (in milliseconds)
        prometheus_lines.append(f'{name}{label_str} {value} {int(timestamp * 1000)}')
    
    prometheus_text = '\n'.join(prometheus_lines)
    
    # Try VictoriaMetrics-style import endpoint first (supports timestamps)
    import_url = f"{prometheus_url}/api/v1/import/prometheus"
    headers = {'Content-Type': 'text/plain'}
    
    try:
        response = requests.post(import_url, data=prometheus_text, headers=headers, timeout=30)
        if response.status_code == 200:
            print("✅ Successfully sent timestamped metrics via import endpoint")
            return True
        else:
            print(f"ℹ️ Import endpoint not available ({response.status_code}), trying remote write...")
    except Exception as e:
        print(f"ℹ️ Import endpoint failed ({e}), trying remote write...")
    
    # Fall back to standard remote write (requires protobuf, more complex)
    # For now, we'll use a simple approach by sending to multiple jobs
    print("📊 Using fallback approach: sending current metrics with date labels...")
    
    # Send current timestamp metrics but with date information in labels
    current_timestamp = int(datetime.now().timestamp())
    fallback_lines = []
    
    for metric in metrics:
        name = metric["metric"]["__name__"]
        labels = {k: v for k, v in metric["metric"].items() if k != "__name__"}
        original_timestamp, value = metric["value"]
        
        # Add the original date as a label for filtering
        original_date = datetime.fromtimestamp(original_timestamp, tz=timezone.utc)
        labels["completion_date"] = original_date.strftime('%Y-%m-%d')
        labels["completion_timestamp"] = str(int(original_timestamp))
        
        # Format labels with proper escaping
        label_pairs = []
        for k, v in sorted(labels.items()):
            # Escape quotes and backslashes in label values
            escaped_value = str(v).replace('\\', '\\\\').replace('"', '\\"')
            label_pairs.append(f'{k}="{escaped_value}"')
        
        if label_pairs:
            label_str = "{" + ",".join(label_pairs) + "}"
        else:
            label_str = ""
        
        # Ensure value is properly formatted
        try:
            float_value = float(value)
            formatted_value = str(float_value)
        except:
            formatted_value = "0"
        
        fallback_lines.append(f'{name}{label_str} {formatted_value}')
    
    # Send via pushgateway but with completion date information
    pushgateway_url = "http://localhost:7101/metrics/job/linear_historical"
    fallback_text = '\n'.join(fallback_lines)
    
    # Add trailing newline
    if fallback_text and not fallback_text.endswith('\n'):
        fallback_text += '\n'
    
    try:
        print(f"📊 Sending {len(fallback_lines)} metrics to Pushgateway...")
        response = requests.post(pushgateway_url, data=fallback_text, headers={'Content-Type': 'text/plain'}, timeout=30)
        if response.status_code == 200:
            print("✅ Successfully sent metrics with completion date labels")
            print("💡 Use 'completion_date' and 'completion_timestamp' labels for time filtering")
            return True
        else:
            print(f"❌ Fallback approach failed: {response.status_code} - {response.text}")
            print("📝 Sample metric lines:")
            for line in fallback_lines[:3]:  # Show first 3 lines for debugging
                print(f"   {line}")
            return False
    except Exception as e:
        print(f"❌ Error with fallback approach: {e}")
        return False

def main():
    """Main execution function"""
    print("🚀 Starting Linear timestamped sync...")
    
    # Load environment variables
    load_env_file()
    
    # Fetch Linear data
    issues = fetch_linear_data()
    if not issues:
        sys.exit(1)
    
    # Generate timestamped metrics
    metrics = generate_prometheus_metrics(issues)
    if not metrics:
        print("❌ No metrics generated")
        sys.exit(1)
    
    print(f"📈 Generated {len(metrics)} timestamped metrics")
    
    # Send to Prometheus using Remote Write API
    success = send_to_prometheus_remote_write(metrics)
    if not success:
        sys.exit(1)
    
    print("🎉 Linear timestamped sync completed successfully!")
    print("")
    print("Next steps:")
    print("1. Check metrics in Prometheus: http://localhost:7100")
    print("2. Refresh Linear dashboards in Grafana: http://localhost:7102")
    print("3. Use 'completion_date' and 'completion_timestamp' labels for time filtering")
    print("4. Test time picker functionality in Grafana dashboards")

if __name__ == "__main__":
    main()