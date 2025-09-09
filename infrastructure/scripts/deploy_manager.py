#!/usr/bin/env python3
"""
Deploy Manager - Deployment utilities for Claude Code Monitoring System

Handles deployment of hooks, configuration, and setup for new environments.
Provides utilities for installing Claude Code hooks and monitoring setup.
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import pwd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeployManagerError(Exception):
    """Custom exception for deploy manager errors."""
    pass

class DeployManager:
    """Manages deployment operations for Claude Code monitoring."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.hook_script = self.project_root / "production-tool-hook.sh"
        
        # Default Claude settings locations
        self.default_claude_dir = Path.home() / ".claude"
        self.default_settings_file = self.default_claude_dir / "settings.json"
        
    def get_user_info(self, username: str = None) -> Tuple[str, Path, Path]:
        """Get user information and paths."""
        if not username:
            # Use current user
            username = os.getlogin() if hasattr(os, 'getlogin') else pwd.getpwuid(os.getuid()).pw_name
            claude_dir = self.default_claude_dir
        else:
            # Get specified user's home directory
            try:
                user_info = pwd.getpwnam(username)
                claude_dir = Path(user_info.pw_dir) / ".claude"
            except KeyError:
                raise DeployManagerError(f"User '{username}' not found")
        
        settings_file = claude_dir / "settings.json"
        return username, claude_dir, settings_file
    
    def backup_settings(self, settings_file: Path) -> Path:
        """Create a backup of existing Claude settings."""
        if not settings_file.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = settings_file.parent / f"settings.json.backup.{timestamp}"
        
        shutil.copy2(settings_file, backup_path)
        return backup_path
    
    def load_settings(self, settings_file: Path) -> Dict[str, Any]:
        """Load existing Claude settings or return empty dict."""
        if not settings_file.exists():
            return {}
        
        try:
            with open(settings_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise DeployManagerError(f"Invalid JSON in settings file: {str(e)}")
    
    def save_settings(self, settings: Dict[str, Any], settings_file: Path):
        """Save Claude settings to file."""
        # Ensure directory exists
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
    
    def create_hook_configuration(self, hook_script_path: Path) -> Dict[str, Any]:
        """Create hook configuration for Claude settings."""
        hook_config = {
            "PreToolUse": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": str(hook_script_path)
                        }
                    ]
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "type": "command", 
                            "command": str(hook_script_path)
                        }
                    ]
                }
            ]
        }
        return hook_config
    
    def action_hooks(self, username: str = None) -> int:
        """Deploy Claude Code monitoring hooks to user's settings."""
        try:
            user, claude_dir, settings_file = self.get_user_info(username)
            
            print(f"🚀 Deploying Claude Code monitoring hooks for user: {user}")
            print("═" * 60)
            
            # Check if hook script exists and is executable
            if not self.hook_script.exists():
                print(f"❌ Hook script not found: {self.hook_script}")
                return 1
            
            if not os.access(self.hook_script, os.X_OK):
                print(f"❌ Hook script not executable: {self.hook_script}")
                print(f"   Run: chmod +x {self.hook_script}")
                return 1
            
            print(f"✅ Hook script found: {self.hook_script}")
            
            # Create target directory structure
            target_dir = claude_dir / "claude-code-monitoring"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy hook script to target location
            target_hook_script = target_dir / "production-tool-hook.sh"
            shutil.copy2(self.hook_script, target_hook_script)
            os.chmod(target_hook_script, 0o755)  # Ensure executable
            
            print(f"✅ Hook script copied to: {target_hook_script}")
            
            # Load existing settings
            print(f"📋 Loading Claude settings from: {settings_file}")
            settings = self.load_settings(settings_file)
            
            # Backup existing settings
            backup_path = self.backup_settings(settings_file)
            if backup_path:
                print(f"💾 Settings backed up to: {backup_path}")
            
            # Create hook configuration
            hook_config = self.create_hook_configuration(target_hook_script)
            
            # Check for existing hooks
            existing_hooks = settings.get("hooks", {})
            if existing_hooks:
                print(f"⚠️  Existing hooks found in settings")
                print(f"   PreToolUse: {len(existing_hooks.get('PreToolUse', []))} hooks")
                print(f"   PostToolUse: {len(existing_hooks.get('PostToolUse', []))} hooks")
                
                # Ask for confirmation
                response = input("   Merge with existing hooks? (y/N): ")
                if response.lower() != 'y':
                    print("❌ Deployment cancelled")
                    return 1
                
                # Merge hooks
                for event_type, hooks in hook_config.items():
                    if event_type in existing_hooks:
                        existing_hooks[event_type].extend(hooks)
                    else:
                        existing_hooks[event_type] = hooks
                
                settings["hooks"] = existing_hooks
            else:
                # No existing hooks, add ours
                settings["hooks"] = hook_config
            
            # Save updated settings
            self.save_settings(settings, settings_file)
            print(f"✅ Claude settings updated successfully")
            
            # Validate deployment
            print(f"\n🔍 Validating deployment...")
            
            if target_hook_script.exists() and os.access(target_hook_script, os.X_OK):
                print(f"   ✅ Hook script: Installed and executable")
            else:
                print(f"   ❌ Hook script: Installation failed")
                return 1
            
            updated_settings = self.load_settings(settings_file)
            if "hooks" in updated_settings:
                hook_count = (len(updated_settings["hooks"].get("PreToolUse", [])) + 
                             len(updated_settings["hooks"].get("PostToolUse", [])))
                print(f"   ✅ Hooks configuration: {hook_count} hooks installed")
            else:
                print(f"   ❌ Hooks configuration: Not found in settings")
                return 1
            
            print(f"\n🎉 Deployment successful!")
            print(f"📊 Next steps:")
            print(f"   • Start Claude Code to activate hooks")
            print(f"   • Run 'just test hooks' to verify hook functionality")
            print(f"   • Use Claude Code tools to generate metrics")
            print(f"   • Check metrics at: http://localhost:7101/metrics")
            
            return 0
            
        except Exception as e:
            print(f"❌ Deployment failed: {str(e)}")
            return 1
    
    def action_validate_deployment(self, username: str = None) -> int:
        """Validate Claude Code monitoring deployment."""
        try:
            user, claude_dir, settings_file = self.get_user_info(username)
            
            print(f"🔍 Validating Claude Code monitoring deployment for: {user}")
            print("═" * 60)
            
            validation_errors = []
            
            # Check Claude directory
            if claude_dir.exists():
                print(f"✅ Claude directory: {claude_dir}")
            else:
                print(f"❌ Claude directory not found: {claude_dir}")
                validation_errors.append("Claude directory missing")
            
            # Check settings file
            if settings_file.exists():
                print(f"✅ Settings file: {settings_file}")
                
                # Validate settings content
                try:
                    settings = self.load_settings(settings_file)
                    
                    if "hooks" in settings:
                        hooks = settings["hooks"]
                        pre_hooks = len(hooks.get("PreToolUse", []))
                        post_hooks = len(hooks.get("PostToolUse", []))
                        print(f"✅ Hooks configured: PreToolUse({pre_hooks}), PostToolUse({post_hooks})")
                        
                        # Check for monitoring hooks specifically
                        has_monitoring_hooks = False
                        for event_type, event_hooks in hooks.items():
                            for hook_group in event_hooks:
                                for hook in hook_group.get("hooks", []):
                                    if "claude-code-monitoring" in hook.get("command", ""):
                                        has_monitoring_hooks = True
                                        break
                        
                        if has_monitoring_hooks:
                            print(f"✅ Monitoring hooks: Found in configuration")
                        else:
                            print(f"⚠️  Monitoring hooks: Not found in configuration")
                            validation_errors.append("Monitoring hooks not configured")
                    else:
                        print(f"❌ Hooks: Not configured in settings")
                        validation_errors.append("No hooks configured")
                        
                except Exception as e:
                    print(f"❌ Settings validation failed: {str(e)}")
                    validation_errors.append("Invalid settings file")
            else:
                print(f"❌ Settings file not found: {settings_file}")
                validation_errors.append("Settings file missing")
            
            # Check hook script installation
            hook_install_path = claude_dir / "claude-code-monitoring" / "production-tool-hook.sh"
            if hook_install_path.exists():
                if os.access(hook_install_path, os.X_OK):
                    print(f"✅ Hook script: {hook_install_path} (executable)")
                else:
                    print(f"⚠️  Hook script: {hook_install_path} (not executable)")
                    validation_errors.append("Hook script not executable")
            else:
                print(f"❌ Hook script not installed: {hook_install_path}")
                validation_errors.append("Hook script not installed")
            
            # Check monitoring services
            print(f"\n🔍 Checking monitoring services...")
            try:
                import requests
                
                services = {
                    'Pushgateway': 'http://localhost:7101/metrics',
                    'Prometheus': 'http://localhost:7100/api/v1/query?query=up',
                    'Grafana': 'http://localhost:7102/api/health'
                }
                
                for service_name, url in services.items():
                    try:
                        response = requests.get(url, timeout=5)
                        if response.status_code == 200:
                            print(f"   ✅ {service_name}: Running")
                        else:
                            print(f"   ❌ {service_name}: HTTP {response.status_code}")
                            validation_errors.append(f"{service_name} not healthy")
                    except:
                        print(f"   ❌ {service_name}: Not reachable")
                        validation_errors.append(f"{service_name} not running")
                        
            except ImportError:
                print(f"   ⚠️  Cannot check services (requests module not available)")
            
            # Summary
            print(f"\n" + "═" * 60)
            if not validation_errors:
                print(f"🎉 Validation successful! Claude Code monitoring is properly deployed.")
                return 0
            else:
                print(f"❌ Found {len(validation_errors)} issues:")
                for i, error in enumerate(validation_errors, 1):
                    print(f"   {i}. {error}")
                
                print(f"\n💡 To fix issues:")
                print(f"   • Run 'just deploy hooks' to reinstall hooks")
                print(f"   • Run 'just up' to start monitoring services")
                return 1
                
        except Exception as e:
            print(f"❌ Validation failed: {str(e)}")
            return 1
    
    def action_uninstall(self, username: str = None) -> int:
        """Uninstall Claude Code monitoring hooks."""
        try:
            user, claude_dir, settings_file = self.get_user_info(username)
            
            print(f"🗑️  Uninstalling Claude Code monitoring hooks for: {user}")
            print("═" * 60)
            
            # Remove installed files
            hook_install_dir = claude_dir / "claude-code-monitoring"
            if hook_install_dir.exists():
                shutil.rmtree(hook_install_dir)
                print(f"✅ Removed hook installation directory: {hook_install_dir}")
            
            # Update settings
            if settings_file.exists():
                backup_path = self.backup_settings(settings_file)
                if backup_path:
                    print(f"💾 Settings backed up to: {backup_path}")
                
                settings = self.load_settings(settings_file)
                
                # Remove monitoring hooks
                if "hooks" in settings:
                    removed_count = 0
                    for event_type in ["PreToolUse", "PostToolUse"]:
                        if event_type in settings["hooks"]:
                            original_hooks = settings["hooks"][event_type]
                            filtered_hooks = []
                            
                            for hook_group in original_hooks:
                                filtered_group_hooks = []
                                for hook in hook_group.get("hooks", []):
                                    if "claude-code-monitoring" not in hook.get("command", ""):
                                        filtered_group_hooks.append(hook)
                                    else:
                                        removed_count += 1
                                
                                if filtered_group_hooks:
                                    hook_group["hooks"] = filtered_group_hooks
                                    filtered_hooks.append(hook_group)
                            
                            if filtered_hooks:
                                settings["hooks"][event_type] = filtered_hooks
                            else:
                                del settings["hooks"][event_type]
                    
                    # Remove hooks section if empty
                    if not settings["hooks"]:
                        del settings["hooks"]
                    
                    self.save_settings(settings, settings_file)
                    print(f"✅ Removed {removed_count} monitoring hooks from settings")
                else:
                    print(f"ℹ️  No hooks found in settings")
            
            print(f"🎉 Uninstallation complete!")
            return 0
            
        except Exception as e:
            print(f"❌ Uninstallation failed: {str(e)}")
            return 1

def main():
    parser = argparse.ArgumentParser(description='Claude Code Monitoring Deploy Manager')
    parser.add_argument('--action', required=True,
                       choices=['hooks', 'validate', 'uninstall'],
                       help='Deployment action to perform')
    parser.add_argument('--username', default='',
                       help='Target username (default: current user)')
    
    args = parser.parse_args()
    
    try:
        manager = DeployManager()
        
        username = args.username if args.username else None
        
        if args.action == 'hooks':
            return manager.action_hooks(username)
        elif args.action == 'validate':
            return manager.action_validate_deployment(username)
        elif args.action == 'uninstall':
            return manager.action_uninstall(username)
        else:
            print(f"❌ Unknown action: {args.action}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Deployment cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Deploy manager failed: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())