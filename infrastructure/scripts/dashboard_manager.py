#!/usr/bin/env python3
"""
Dashboard Manager - Grafana dashboard management for Claude Code Monitoring

Provides unified interface for dashboard operations including publishing,
updating, backup, and import/export of Claude Code monitoring dashboards.
"""

import argparse
import json
import logging
import os
import requests
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DashboardManagerError(Exception):
    """Custom exception for dashboard manager errors."""
    pass

class DashboardManager:
    """Manages Grafana dashboards for Claude Code monitoring."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.dashboards_dir = self.project_root / "grafana" / "dashboards"
        self.provisioning_dir = self.project_root / "grafana" / "provisioning" / "dashboards"
        # Claude adapter dashboards location
        self.claude_dashboards_dir = self.project_root / ".." / "adapters" / "claude" / "dashboards"
        
        # Grafana API configuration
        self.grafana = {
            'url': 'http://localhost:7102',
            'auth': ('admin', 'admin'),
            'headers': {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        }
        
        # Ensure directories exist
        self.dashboards_dir.mkdir(parents=True, exist_ok=True)
        self.provisioning_dir.mkdir(parents=True, exist_ok=True)
        
    def make_grafana_request(self, method: str, endpoint: str, 
                           data: Optional[Dict] = None, timeout: int = 10) -> requests.Response:
        """Make a request to Grafana API."""
        url = f"{self.grafana['url']}/api{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self.grafana['auth'],
                headers=self.grafana['headers'],
                json=data,
                timeout=timeout
            )
            return response
        except requests.exceptions.ConnectionError:
            raise DashboardManagerError("Cannot connect to Grafana - is it running on port 7102?")
        except requests.exceptions.Timeout:
            raise DashboardManagerError(f"Grafana API request timed out after {timeout}s")
    
    def get_dashboard_files(self) -> Dict[str, Path]:
        """Get all dashboard files from local directories."""
        dashboard_files = {}
        
        # Check all directories for JSON files (Claude dashboards first, then others)
        for directory in [self.claude_dashboards_dir, self.dashboards_dir, self.provisioning_dir]:
            if directory.exists():
                for file_path in directory.glob("*.json"):
                    # Use filename without extension as key
                    name = file_path.stem
                    # Skip if already found (first directory takes precedence)
                    if name not in dashboard_files:
                        dashboard_files[name] = file_path
        
        return dashboard_files
    
    def action_list(self) -> int:
        """List all dashboards from Grafana."""
        try:
            response = self.make_grafana_request('GET', '/search?type=dash-db')
            
            if response.status_code != 200:
                print(f"❌ Failed to list dashboards: HTTP {response.status_code}")
                return 1
            
            dashboards = response.json()
            local_files = self.get_dashboard_files()
            
            print("📋 Grafana Dashboards")
            print("═" * 60)
            
            if not dashboards:
                print("   No dashboards found in Grafana")
            else:
                print(f"{'Name':<30} {'UID':<15} {'Local File'}")
                print("─" * 60)
                
                for dash in dashboards:
                    title = dash.get('title', 'Untitled')
                    uid = dash.get('uid', 'N/A')
                    
                    # Check if we have a local file for this dashboard
                    local_status = "❌"
                    for name, path in local_files.items():
                        # Multiple matching approaches for better compatibility
                        name_clean = name.lower().replace('-', '_').replace('dashboard', '').replace('simple', '').strip('_')
                        title_clean = title.lower().replace('-', '_').replace(' ', '').replace('(', '').replace(')', '').replace('claude', '').replace('code', '').replace('simple', '').strip('_')
                        uid_clean = uid.lower().replace('-', '_').replace('claude', '').replace('code', '').strip('_')
                        
                        # Special case mappings for tricky names
                        special_matches = {
                            'bash_commands': ['bashcommands', 'bash_commands'],
                            'tool_usage': ['toolusage', 'tool_usage'], 
                            'original_working': ['working', 'original_working']
                        }
                        
                        # Check various matching patterns
                        matched = False
                        
                        # Direct matches
                        if (name_clean in title_clean or title_clean in name_clean or
                            name_clean in uid_clean or uid_clean in name_clean):
                            matched = True
                        
                        # Special case matches
                        for key, variants in special_matches.items():
                            if key in name_clean:
                                for variant in variants:
                                    if variant in title_clean or variant in uid_clean:
                                        matched = True
                                        break
                        
                        if matched:
                            local_status = f"✅"
                            break
                    
                    print(f"{title:<30} {uid:<15} {local_status}")
            
            # Show local files not in Grafana
            print(f"\n📁 Local Dashboard Files")
            print("─" * 30)
            for name, path in local_files.items():
                print(f"   • {name} ({path.relative_to(self.project_root)})")
            
            return 0
            
        except DashboardManagerError as e:
            print(f"❌ {str(e)}")
            return 1
    
    def action_publish(self, dashboard_name: str) -> int:
        """Publish a dashboard from local file to Grafana."""
        if not dashboard_name:
            print("❌ Dashboard name required for publish action")
            print("   Usage: just dashboard publish <name>")
            return 1
        
        local_files = self.get_dashboard_files()
        
        # Find matching dashboard file
        dashboard_file = None
        for name, path in local_files.items():
            if name == dashboard_name or name.replace('-', '_') == dashboard_name.replace('-', '_'):
                dashboard_file = path
                break
        
        if not dashboard_file:
            print(f"❌ Dashboard file not found: {dashboard_name}")
            print("   Available dashboards:")
            for name in local_files.keys():
                print(f"     • {name}")
            return 1
        
        try:
            # Load dashboard JSON
            with open(dashboard_file, 'r') as f:
                dashboard_data = json.load(f)
            
            # Prepare dashboard for API
            if 'dashboard' in dashboard_data:
                # Already wrapped in API format
                api_data = dashboard_data
            else:
                # Wrap in API format
                api_data = {
                    'dashboard': dashboard_data,
                    'overwrite': True,
                    'message': f'Published by Claude Code Dashboard Manager at {datetime.now().isoformat()}'
                }
            
            # Ensure dashboard has required fields
            dashboard = api_data['dashboard']
            if 'id' in dashboard:
                del dashboard['id']  # Remove ID to avoid conflicts
            
            print(f"📤 Publishing dashboard: {dashboard_name}")
            print(f"   Source: {dashboard_file.relative_to(self.project_root)}")
            
            response = self.make_grafana_request('POST', '/dashboards/db', api_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Dashboard published successfully")
                print(f"   URL: {self.grafana['url']}/d/{result.get('uid', 'unknown')}")
                return 0
            else:
                print(f"❌ Failed to publish dashboard: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        print(f"   Error: {error_data['message']}")
                except:
                    print(f"   Response: {response.text}")
                return 1
                
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in dashboard file: {dashboard_file}")
            return 1
        except Exception as e:
            print(f"❌ Error publishing dashboard: {str(e)}")
            return 1
    
    def action_update(self, dashboard_name: str) -> int:
        """Update an existing dashboard (same as publish with overwrite)."""
        print(f"🔄 Updating dashboard: {dashboard_name}")
        return self.action_publish(dashboard_name)
    
    def action_export(self, dashboard_name: str) -> int:
        """Export a specific dashboard from Grafana to local file."""
        if not dashboard_name:
            print("❌ Dashboard name required for export action")
            print("   Usage: just dashboard export <name>")
            return 1
        
        try:
            # First, search for the dashboard
            response = self.make_grafana_request('GET', '/search?type=dash-db')
            if response.status_code != 200:
                print(f"❌ Failed to search dashboards: HTTP {response.status_code}")
                return 1
            
            dashboards = response.json()
            target_dashboard = None
            
            # Find matching dashboard
            for dash in dashboards:
                title = dash.get('title', '').lower()
                if (dashboard_name.lower() in title or 
                    title.replace('-', '_').replace(' ', '_') == dashboard_name.lower().replace('-', '_')):
                    target_dashboard = dash
                    break
            
            if not target_dashboard:
                print(f"❌ Dashboard not found in Grafana: {dashboard_name}")
                print("   Available dashboards:")
                for dash in dashboards:
                    print(f"     • {dash.get('title', 'Untitled')}")
                return 1
            
            # Get full dashboard data
            uid = target_dashboard['uid']
            response = self.make_grafana_request('GET', f'/dashboards/uid/{uid}')
            
            if response.status_code != 200:
                print(f"❌ Failed to export dashboard: HTTP {response.status_code}")
                return 1
            
            dashboard_data = response.json()
            
            # Clean up the data for export
            dashboard = dashboard_data.get('dashboard', {})
            if 'id' in dashboard:
                del dashboard['id']
            if 'version' in dashboard:
                del dashboard['version']
            
            # Save to file
            filename = dashboard_name.lower().replace(' ', '-').replace('_', '-') + '-dashboard.json'
            output_path = self.dashboards_dir / filename
            
            with open(output_path, 'w') as f:
                json.dump(dashboard, f, indent=2, sort_keys=True)
            
            print(f"✅ Dashboard exported successfully")
            print(f"   Source: {target_dashboard['title']}")
            print(f"   File: {output_path.relative_to(self.project_root)}")
            
            return 0
            
        except DashboardManagerError as e:
            print(f"❌ {str(e)}")
            return 1
        except Exception as e:
            print(f"❌ Error exporting dashboard: {str(e)}")
            return 1
    
    def action_backup(self) -> int:
        """Backup all dashboards from Grafana to local files."""
        try:
            response = self.make_grafana_request('GET', '/search?type=dash-db')
            
            if response.status_code != 200:
                print(f"❌ Failed to list dashboards: HTTP {response.status_code}")
                return 1
            
            dashboards = response.json()
            
            if not dashboards:
                print("   No dashboards found to backup")
                return 0
            
            print(f"💾 Backing up {len(dashboards)} dashboards...")
            print("═" * 50)
            
            backup_dir = self.dashboards_dir / "backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            success_count = 0
            
            for dash in dashboards:
                title = dash.get('title', 'Untitled')
                uid = dash.get('uid')
                
                if not uid:
                    print(f"⚠️  Skipping {title} (no UID)")
                    continue
                
                try:
                    # Get full dashboard data
                    response = self.make_grafana_request('GET', f'/dashboards/uid/{uid}')
                    
                    if response.status_code == 200:
                        dashboard_data = response.json()
                        
                        # Clean up the data
                        dashboard = dashboard_data.get('dashboard', {})
                        if 'id' in dashboard:
                            del dashboard['id']
                        if 'version' in dashboard:
                            del dashboard['version']
                        
                        # Save to backup directory
                        filename = title.lower().replace(' ', '-').replace('_', '-') + '-dashboard.json'
                        backup_path = backup_dir / filename
                        
                        with open(backup_path, 'w') as f:
                            json.dump(dashboard, f, indent=2, sort_keys=True)
                        
                        print(f"✅ {title}")
                        success_count += 1
                    else:
                        print(f"❌ {title} (HTTP {response.status_code})")
                        
                except Exception as e:
                    print(f"❌ {title} (Error: {str(e)})")
            
            print(f"\n💾 Backup completed: {success_count}/{len(dashboards)} dashboards")
            print(f"   Location: {backup_dir.relative_to(self.project_root)}")
            
            return 0 if success_count > 0 else 1
            
        except DashboardManagerError as e:
            print(f"❌ {str(e)}")
            return 1
        except Exception as e:
            print(f"❌ Error during backup: {str(e)}")
            return 1
    
    def action_import(self, dashboard_name: str) -> int:
        """Import a dashboard file (same as publish)."""
        print(f"📥 Importing dashboard: {dashboard_name}")
        return self.action_publish(dashboard_name)

def main():
    parser = argparse.ArgumentParser(description='Claude Code Dashboard Manager')
    parser.add_argument('--action', required=True,
                       choices=['list', 'publish', 'update', 'backup', 'export', 'import'],
                       help='Action to perform')
    parser.add_argument('--name', default=None,
                       help='Dashboard name (for publish, update, export, import)')
    
    args = parser.parse_args()
    
    try:
        manager = DashboardManager()
        
        # Handle empty string as None for optional name
        name = args.name if args.name and args.name.strip() else None
        
        if args.action == 'list':
            return manager.action_list()
        elif args.action == 'publish':
            if not name:
                print("❌ Dashboard name required for publish action")
                return 1
            return manager.action_publish(name)
        elif args.action == 'update':
            if not name:
                print("❌ Dashboard name required for update action")
                return 1
            return manager.action_update(name)
        elif args.action == 'export':
            if not name:
                print("❌ Dashboard name required for export action")
                return 1
            return manager.action_export(name)
        elif args.action == 'backup':
            return manager.action_backup()
        elif args.action == 'import':
            if not name:
                print("❌ Dashboard name required for import action")
                return 1
            return manager.action_import(name)
        else:
            print(f"❌ Unknown action: {args.action}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Dashboard manager failed: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())