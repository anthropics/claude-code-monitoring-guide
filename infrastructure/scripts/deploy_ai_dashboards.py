#!/usr/bin/env python3
"""
Deploy AI Agent Dashboards to Grafana

Deploys the 3 new AI agent monitoring dashboards:
1. AI Agents - Usage & Performance  
2. Session Correlation - Claude Code & AI Agents
3. Unified Development Tools - Claude Code & AI Agents
"""

import requests
import json
import sys
import time
from pathlib import Path

def deploy_dashboard(dashboard_path, grafana_url="http://localhost:7102", username="admin", password="admin"):
    """Deploy a dashboard JSON file to Grafana"""
    
    # Read dashboard JSON
    with open(dashboard_path, 'r') as f:
        dashboard_data = json.load(f)
    
    # Prepare payload for Grafana API
    payload = {
        "dashboard": dashboard_data,
        "overwrite": True,
        "message": f"Deployed AI agent dashboard: {dashboard_data.get('title', 'Unknown')}"
    }
    
    try:
        response = requests.post(
            f"{grafana_url}/api/dashboards/db",
            auth=(username, password),
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            dashboard_title = dashboard_data.get('title', 'Unknown')
            dashboard_uid = result.get('uid', 'unknown')
            dashboard_url = f"{grafana_url}/d/{dashboard_uid}"
            
            print(f"✅ {dashboard_title}")
            print(f"   URL: {dashboard_url}")
            return True
        else:
            print(f"❌ Failed to deploy {dashboard_path}: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to Grafana: {e}")
        return False

def main():
    print("🚀 Deploying Claude Code Dashboards to Grafana\n")
    
    # Dashboard paths
    dashboard_dir = Path(__file__).parent.parent / "grafana" / "provisioning" / "dashboards"
    dashboards = [
        ("ai-agents-simple.json", "Claude Code - AI Tool Agents")
    ]
    
    # Check Grafana availability
    try:
        response = requests.get("http://localhost:7102/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ Grafana not available at http://localhost:7102")
            print("   Run: just up")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to Grafana at http://localhost:7102")
        print("   Run: just up")
        sys.exit(1)
    
    print("✅ Grafana is running\n")
    
    # Deploy each dashboard
    deployed = 0
    for filename, description in dashboards:
        dashboard_path = dashboard_dir / filename
        
        if not dashboard_path.exists():
            print(f"❌ Dashboard file not found: {dashboard_path}")
            continue
            
        print(f"📊 Deploying: {description}")
        if deploy_dashboard(dashboard_path):
            deployed += 1
        print()
        
        # Small delay between deployments
        time.sleep(1)
    
    print(f"🎉 Deployment Complete: {deployed}/{len(dashboards)} dashboards deployed")
    print("\n📋 Access Dashboards:")
    print("   • Grafana: http://localhost:7102 (admin/admin)")
    print("   • Use Grafana UI to browse deployed dashboards")
    
    print("\n💡 Dashboard Features:")
    print("   • Total usage and cost tracking")
    print("   • Agent and model breakdown")
    print("   • Clean token charts (total + input/output breakdown)")
    print("   • Real-time data from doc-finder, git-info, ai-analyzer")

if __name__ == "__main__":
    main()