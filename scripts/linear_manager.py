#!/usr/bin/env python3
"""
Linear Manager - Linear CLI integration for Claude Code Monitoring

This script provides a unified interface for managing Linear integration,
including authentication, data syncing, and metrics generation.

Actions: auth, status, test, sync, help
"""

import argparse
import subprocess
import sys
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LinearManagerError(Exception):
    """Custom exception for linear manager errors."""
    pass

class LinearManager:
    """Manages Linear CLI integration for monitoring stack."""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.sync_script = self.repo_root / "scripts" / "linear-sync.sh"
        self.env_file = self.repo_root / ".env"
        self.linearis_cli = self.repo_root / "node_modules" / ".bin" / "linearis"
        
    def _run_command(self, cmd: List[str], capture_output=True, timeout=30) -> Tuple[int, str, str]:
        """Run a command and return (returncode, stdout, stderr)."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=self.repo_root
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return 1, "", str(e)
    
    def _check_prerequisites(self) -> bool:
        """Check if required tools are available."""
        # Check for linearis CLI
        if not self.linearis_cli.exists():
            print("❌ Linearis CLI not found. Run 'just setup' to install dependencies.")
            return False
        
        # Check for jq (still needed for JSON processing in metrics)
        returncode, _, _ = self._run_command(["which", "jq"])
        if returncode != 0:
            print("❌ jq not found. Please install jq for JSON processing.")
            return False
            
        return True
    
    def _get_api_token(self) -> str:
        """Get API token from environment or .env file."""
        api_token = os.getenv('LINEAR_API_TOKEN')
        
        if not api_token and self.env_file.exists():
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        if line.startswith('LINEAR_API_TOKEN='):
                            api_token = line.split('=', 1)[1].strip()
                            break
            except Exception:
                pass
        
        return api_token
    
    def _get_user_info(self, api_token: str) -> dict:
        """Get user info from Linear API."""
        try:
            # Use linearis to get user info with --api-token flag
            result = subprocess.run([
                str(self.linearis_cli), "--api-token", api_token, "issues", "list", "-l", "1"
            ], capture_output=True, text=True, cwd=self.repo_root)
            
            if result.returncode == 0 and result.stdout.strip():
                import json
                issues_data = json.loads(result.stdout)
                # Extract user info from first issue's assignee if available
                if issues_data and len(issues_data) > 0:
                    first_issue = issues_data[0]
                    assignee = first_issue.get('assignee', {})
                    if assignee:
                        return {
                            'name': assignee.get('name', 'Unknown'),
                            'email': assignee.get('email', 'Unknown'),
                            'organization': {'name': 'Linear Organization'}
                        }
        except:
            pass
        
        return {}
    
    def _save_token_to_env(self, token: str):
        """Save token to .env file."""
        env_content = f"LINEAR_API_TOKEN={token}\n"
        
        # Read existing .env if it exists
        existing_content = ""
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                existing_content = f.read()
        
        # Update or append token
        if 'LINEAR_API_TOKEN=' in existing_content:
            # Replace existing token
            lines = existing_content.split('\n')
            updated_lines = []
            for line in lines:
                if line.startswith('LINEAR_API_TOKEN='):
                    updated_lines.append(f"LINEAR_API_TOKEN={token}")
                else:
                    updated_lines.append(line)
            env_content = '\n'.join(updated_lines)
        else:
            # Append new token
            env_content = existing_content + f"\nLINEAR_API_TOKEN={token}\n"
        
        with open(self.env_file, 'w') as f:
            f.write(env_content)
    
    def _check_authentication(self) -> bool:
        """Check if user is authenticated with Linear."""
        if not self._check_prerequisites():
            return False
        
        # Check for API token in environment or .env file
        api_token = self._get_api_token()
        
        if not api_token:
            return False
        
        # Test API token by making a simple request with linearis
        # Linearis uses --api-token flag, not environment variables
        returncode, stdout, stderr = self._run_command([
            str(self.linearis_cli), "--api-token", api_token, "issues", "list", "-l", "1"
        ])
        
        # If linearis succeeds, we're authenticated
        return returncode == 0
    
    def auth(self) -> bool:
        """Setup Linear API authentication."""
        print("🔐 Setting up Linear API authentication...")
        
        if not self._check_prerequisites():
            return False
        
        # Check if already authenticated
        if self._check_authentication():
            print("✅ Already authenticated with Linear!")
            
            # Show current user info
            try:
                api_token = self._get_api_token()
                if api_token:
                    user_info = self._get_user_info(api_token)
                    if user_info:
                        print(f"   👤 Logged in as: {user_info['name']} ({user_info['email']})")
                    
                response = input("\nWould you like to update your token? (y/N): ").lower().strip()
                if response not in ['y', 'yes']:
                    return True
            except:
                pass
        
        print("")
        print("🌐 Opening Linear API settings in your browser...")
        
        # Try to open browser to Linear API settings
        linear_api_url = "https://linear.app/settings/api"
        try:
            import webbrowser
            if webbrowser.open(linear_api_url):
                print("✅ Browser opened to Linear API settings")
            else:
                print(f"❌ Could not open browser. Please visit: {linear_api_url}")
        except:
            print(f"❌ Could not open browser. Please visit: {linear_api_url}")
        
        print("")
        print("📋 Quick Setup Steps:")
        print("1. ✅ Browser opened to Linear API settings")
        print("2. 🔑 Click 'Create new token'")
        print("3. 📝 Give it a name (e.g., 'Claude Code Monitoring')")
        print("4. 📋 Copy the generated token")
        print("5. 🔒 Paste it below (it will be saved securely)")
        print("")
        
        # Get token with validation
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    print(f"⏳ Attempt {attempt + 1} of {max_attempts}")
                
                token = input("📋 Paste your Linear API token: ").strip()
                
                if not token:
                    print("❌ No token provided")
                    if attempt < max_attempts - 1:
                        continue
                    else:
                        return False
                
                # Basic token validation (Linear tokens are typically long alphanumeric)
                if len(token) < 20 or not token.replace('_', '').replace('-', '').isalnum():
                    print("⚠️  Token format looks unusual. Are you sure this is correct?")
                    confirm = input("Continue anyway? (y/N): ").lower().strip()
                    if confirm not in ['y', 'yes']:
                        if attempt < max_attempts - 1:
                            continue
                        else:
                            return False
                
                print("🧪 Testing token...")
                
                # Test the token before saving
                os.environ['LINEAR_API_TOKEN'] = token
                if self._check_authentication():
                    # Get user info to show success
                    user_info = self._get_user_info(token)
                    
                    # Save to .env file
                    self._save_token_to_env(token)
                    
                    print("✅ Linear authentication successful!")
                    if user_info:
                        print(f"   👤 Logged in as: {user_info['name']} ({user_info['email']})")
                        print(f"   🏢 Organization: {user_info.get('organization', {}).get('name', 'Unknown')}")
                    print(f"   🔒 Token saved securely to {self.env_file}")
                    return True
                else:
                    print("❌ Token test failed. Please check your token and try again.")
                    if attempt < max_attempts - 1:
                        print("💡 Make sure you copied the entire token")
                        continue
                    else:
                        return False
                        
            except KeyboardInterrupt:
                print("\n❌ Setup cancelled")
                return False
            except Exception as e:
                print(f"❌ Error during setup: {e}")
                if attempt < max_attempts - 1:
                    continue
                else:
                    return False
        
        print("❌ Maximum attempts exceeded")
        return False
    
    def status(self) -> bool:
        """Check Linear authentication status."""
        print("🔍 Checking Linear authentication status...")
        
        if not self._check_prerequisites():
            return False
            
        if self._check_authentication():
            # Get user info from API
            api_token = self._get_api_token()
            
            if api_token:
                user_info = self._get_user_info(api_token)
                if user_info:
                    name = user_info.get('name', 'Unknown')
                    email = user_info.get('email', 'Unknown')
                    org_name = user_info.get('organization', {}).get('name', 'Unknown')
                    print(f"✅ Authenticated with Linear as {name} ({email})")
                    print(f"   🏢 Organization: {org_name}")
                else:
                    print("✅ Authenticated with Linear")
            else:
                print("✅ Authenticated with Linear")
            return True
        else:
            print("❌ Not authenticated with Linear - run 'just linear auth'")
            return False
    
    def test(self) -> bool:
        """Test Linear connectivity by fetching sample issues."""
        print("🧪 Testing Linear connectivity...")
        
        if not self._check_authentication():
            print("❌ Authentication required - run 'just linear auth'")
            return False
        
        # Get API token
        api_token = self._get_api_token()
        
        if not api_token:
            print("❌ API token not found")
            return False
            
        print("📊 Fetching sample issues...")
        
        # Use linearis to fetch sample issues with --api-token flag
        result = subprocess.run([
            str(self.linearis_cli), "--api-token", api_token, "issues", "list", "-l", "3"
        ], capture_output=True, text=True, cwd=self.repo_root)
        
        if result.returncode == 0:
            print("✅ Linear connectivity test complete!")
            if result.stdout.strip():
                try:
                    import json
                    issues = json.loads(result.stdout)
                    print(f"📋 Found {len(issues)} sample issues")
                    for issue in issues[:3]:
                        assignee = issue.get('assignee', {})
                        assignee_name = assignee.get('name', 'Unassigned') if assignee else 'Unassigned'
                        state = issue.get('state', {}).get('name', 'Unknown') if issue.get('state') else 'Unknown'
                        print(f"  - {issue.get('identifier', 'Unknown')}: {issue.get('title', 'No title')} ({state}, {assignee_name})")
                except json.JSONDecodeError:
                    print("📋 Issues found (non-JSON format)")
                except Exception as e:
                    print(f"❌ Error parsing response: {e}")
                    return False
            return True
        else:
            print(f"❌ Linear connectivity test failed: {result.stderr}")
            return False
    
    def sync(self) -> bool:
        """Sync Linear data to Prometheus metrics."""
        print("🔄 Running Linear data sync...")
        
        if not self.sync_script.exists():
            print(f"❌ Linear sync script not found: {self.sync_script}")
            return False
            
        if not self._check_authentication():
            print("❌ Authentication required - run 'just linear auth'")
            return False
            
        # Make sure script is executable
        os.chmod(self.sync_script, 0o755)
        
        # Run the sync script
        try:
            result = subprocess.run([str(self.sync_script)], cwd=self.repo_root)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running sync script: {e}")
            return False
    
    def help(self) -> bool:
        """Show Linear integration help."""
        print("📋 LINEAR INTEGRATION COMMANDS")
        print("════════════════════════════════════════════════════════════════════")
        print("")
        print("🔧 COMMANDS:")
        print("")
        print("  just linear auth")
        print("     Setup Linear API authentication (required first step)")
        print("     - Opens browser to Linear API settings automatically")
        print("     - Tests token before saving")
        print("     - Stores token securely in .env file")
        print("     - Shows your user info and organization")
        print("")
        print("  just linear status")
        print("     Check Linear authentication status")
        print("     - Shows if you're authenticated")
        print("     - Displays current user info")
        print("")
        print("  just linear test")
        print("     Test Linear connectivity")
        print("     - Uses Linearis CLI to fetch sample issues")
        print("     - Verifies API access and authentication")
        print("")
        print("  just linear sync")
        print("     Sync Linear data to Prometheus")
        print("     - Uses Linearis CLI to fetch completed issues (last 30 days)")
        print("     - Filters engineering team (@degreeanalytics.com)")
        print("     - Converts to Prometheus metrics")
        print("     - Sends to Pushgateway for dashboards")
        print("")
        print("  just linear cron")
        print("     Setup daily cron job for automatic sync")
        print("     - Shows cron job configuration")
        print("     - Provides manual installation instructions")
        print("     - Runs daily at 9:00 AM")
        print("")
        print("💡 WORKFLOW:")
        print("   1. just setup                    # Install dependencies")
        print("   2. just linear auth              # Authenticate with Linear")
        print("   3. just linear test              # Test connectivity")
        print("   4. just linear sync              # Sync data to metrics")
        print("   5. just linear cron              # Setup daily automation")
        print("   6. View dashboards: http://localhost:7102")
        print("")
        print("🔗 METRICS GENERATED:")
        print("   • linear_completion_by_user     - Issues completed by user")
        print("   • linear_daily_completions      - Daily completion counts")
        print("   • linear_completion_by_priority - Completions by priority")
        print("   • linear_completion_by_type     - Completions by issue type")
        return True
    
    def cron(self) -> bool:
        """Setup daily cron job for Linear data sync."""
        print("⏰ Setting up daily Linear data sync cron job...")
        
        if not self._check_authentication():
            print("❌ Authentication required - run 'just linear auth' first")
            return False
        
        # Get current script path
        script_path = self.sync_script.absolute()
        
        # Create cron entry (runs at 9 AM daily)
        cron_command = f"0 9 * * * {script_path}"
        cron_comment = "# Claude Code Linear daily sync"
        
        print("📋 Cron job details:")
        print(f"   Schedule: Daily at 9:00 AM")
        print(f"   Script: {script_path}")
        print(f"   Command: {cron_command}")
        print("")
        
        print("🔧 To install the cron job, run:")
        print("   crontab -e")
        print("")
        print("   Then add this line:")
        print(f"   {cron_comment}")
        print(f"   {cron_command}")
        print("")
        print("💡 Tips:")
        print("   • Make sure the script is executable: chmod +x script_path")
        print("   • Test the sync manually first: just linear sync")
        print("   • Check cron logs: grep CRON /var/log/syslog (Linux)")
        print("   • List current cron jobs: crontab -l")
        print("")
        print("🚨 Alternative - Manual scheduling:")
        print("   • Set a daily reminder to run: just linear sync")
        print("   • Use system task scheduler (Windows)")
        print("   • Use launchd (macOS) for more reliable scheduling")
        
        return True

def main():
    parser = argparse.ArgumentParser(
        description='Linear CLI integration manager for Claude Code Monitoring'
    )
    parser.add_argument(
        '--action',
        required=True,
        choices=['auth', 'status', 'test', 'sync', 'cron', 'help'],
        help='Action to perform'
    )
    
    args = parser.parse_args()
    
    manager = LinearManager()
    
    try:
        if args.action == 'auth':
            success = manager.auth()
        elif args.action == 'status':
            success = manager.status()
        elif args.action == 'test':
            success = manager.test()
        elif args.action == 'sync':
            success = manager.sync()
        elif args.action == 'cron':
            success = manager.cron()
        elif args.action == 'help':
            success = manager.help()
        else:
            print(f"❌ Unknown action: {args.action}")
            success = False
            
        sys.exit(0 if success else 1)
        
    except LinearManagerError as e:
        logger.error(f"Linear manager error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()