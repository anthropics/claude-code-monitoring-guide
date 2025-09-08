#!/usr/bin/env python3
"""
Simple MCP server management for individual server control.

This module provides functionality to manage Model Context Protocol (MCP) servers
individually through the Claude CLI, supporting both SSE and stdio server types.
Environment variables are expanded from .env file for flexible path configuration.
"""

import json
import subprocess
import sys
import argparse
import os
from pathlib import Path
from typing import Dict, Any, Union, Optional

class MCPManager:
    """
    Manages individual MCP (Model Context Protocol) server operations.

    Provides functionality to add, remove, and list MCP servers using Claude CLI.
    Supports both SSE (Server-Sent Events) and stdio server types with
    environment variable expansion from .env file.

    Attributes:
        registry_file (str): Path to the MCP servers JSON registry file.
    """

    def __init__(self) -> None:
        """
        Initialize the MCP Manager.

        Sets up the registry file path and loads environment variables
        from .env file for use in server configuration.
        """
        # Look for registry file in project root
        self.registry_file = os.path.join(os.path.dirname(__file__), "..", "mcp-servers.json")
        # Load environment variables from .env file
        self._load_env_file()

    def _load_env_file(self) -> None:
        """
        Load environment variables from .env file.

        Reads the .env file in the project root and sets environment variables
        that are not already defined in the current environment. This allows
        for environment variable expansion in the MCP server registry.
        """
        env_file = Path(self.registry_file).parent / ".env"
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Only set if not already in environment
                        if key not in os.environ:
                            os.environ[key] = value

    def _expand_env_vars(self, obj: Union[str, Dict[str, Any], list, Any]) -> Union[str, Dict[str, Any], list, Any]:
        """
        Recursively expand environment variables in strings within data structures.

        Args:
            obj: The object to process. Can be a string, dict, list, or other type.

        Returns:
            The processed object with environment variables expanded.
            For strings: ${VAR_NAME} patterns are expanded.
            For dicts/lists: recursively processes all contained values.
            For other types: returns the object unchanged.
        """
        if isinstance(obj, str):
            return os.path.expandvars(obj)
        elif isinstance(obj, dict):
            return {key: self._expand_env_vars(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        else:
            return obj

    def load_registry(self) -> Dict[str, Dict[str, Any]]:
        """
        Load server registry from JSON file and expand environment variables.

        Returns:
            A dictionary containing MCP server configurations with environment
            variables expanded. Returns empty dict if file not found or invalid JSON.

        Raises:
            Prints error messages for FileNotFoundError and JSONDecodeError but
            does not re-raise exceptions, returning empty dict instead.
        """
        try:
            with open(self.registry_file, 'r') as f:
                registry = json.load(f)
                # Expand environment variables in the registry
                return self._expand_env_vars(registry)
        except FileNotFoundError:
            print(f"❌ Registry file not found: {self.registry_file}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in registry file: {e}")
            return {}

    def add_server(self, server_name: str) -> int:
        """
        Add a server from the registry to Claude CLI configuration.

        Args:
            server_name: Name of the server to add from the registry.

        Returns:
            0 if successful, 1 if failed.

        Note:
            Supports both SSE (Server-Sent Events) and stdio server types.
            For SSE servers, uses 'claude mcp add' command.
            For stdio servers, uses 'claude mcp add-json' command.
        """
        registry = self.load_registry()
        if server_name not in registry:
            print(f"❌ Server '{server_name}' not found in registry")
            print("Available servers:")
            for name in registry.keys():
                print(f"  - {name}")
            return 1

        server_config = registry[server_name]
        print(f"📦 Adding {server_name}: {server_config['description']}")

        if server_config["type"] == "sse":
            cmd = ["claude", "mcp", "add", "--transport", "sse", server_name, server_config["url"]]
        else:  # stdio
            json_config = {
                "command": server_config["command"],
                "args": server_config["args"]
            }
            cmd = ["claude", "mcp", "add-json", server_name, json.dumps(json_config)]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✅ Successfully added {server_name}")
            return 0
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to add {server_name}: {e}")
            if e.stderr:
                print(f"   Error: {e.stderr.strip()}")
            return 1
        except FileNotFoundError:
            print("❌ Claude CLI not found. Please ensure Claude CLI is installed.")
            return 1

    def remove_server(self, server_name: str) -> int:
        """
        Remove a server from Claude CLI configuration.

        Args:
            server_name: Name of the server to remove.

        Returns:
            0 if successful, 1 if failed.
        """
        print(f"🗑️  Removing {server_name}")
        try:
            result = subprocess.run(["claude", "mcp", "remove", server_name],
                                  check=True, capture_output=True, text=True)
            print(f"✅ Successfully removed {server_name}")
            return 0
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to remove {server_name}: {e}")
            if e.stderr:
                print(f"   Error: {e.stderr.strip()}")
            return 1
        except FileNotFoundError:
            print("❌ Claude CLI not found. Please ensure Claude CLI is installed.")
            return 1

    def list_servers(self) -> int:
        """
        List currently configured MCP servers in Claude CLI.

        Returns:
            0 if successful, 1 if failed.
        """
        print("🔍 Configured MCP servers:")
        try:
            result = subprocess.run(["claude", "mcp", "list"], check=True, capture_output=True, text=True)
            if result.stdout:
                print(result.stdout.strip())
            return 0
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to list servers: {e}")
            if e.stderr:
                print(f"   Error: {e.stderr.strip()}")
            return 1
        except FileNotFoundError:
            print("❌ Claude CLI not found. Please ensure Claude CLI is installed.")
            return 1

    def list_available(self) -> int:
        """
        List all available servers in the registry.

        Returns:
            Always returns 0 (success).
        """
        registry = self.load_registry()
        print("📋 Available servers in registry:")
        for name, config in registry.items():
            print(f"  {name}: {config['description']}")
        return 0

    def help(self) -> int:
        """
        Display comprehensive help information about MCP server management.

        Returns:
            Always returns 0 (success).
        """
        print("""
MCP Server Management (Individual Server Control)
================================================

Individual server management for Claude Code MCP servers.

Commands:
  add <server>      Add server from registry
  remove <server>   Remove configured server
  list              List configured servers
  available         List available servers in registry
  help              Show this help

Examples:
  just mcp available        # Show available servers
  just mcp add linear       # Add Linear server
  just mcp add context7     # Add Context7 server for documentation
  just mcp add task-master  # Add Task Master server
  just mcp remove linear    # Remove Linear server
  just mcp list            # List configured servers

Registry:
  Server definitions are stored in mcp-servers.json
  Manually maintained for available server configurations

Environment Variables:
  Registry supports ${VAR_NAME} expansion from .env file
  Example: ZEN_MCP_SERVER_PATH=/path/to/zen-server
  Used for: "${ZEN_MCP_SERVER_PATH}/.zen_venv/bin/python"
""")
        return 0

def main() -> Optional[int]:
    """
    Main entry point for the MCP manager command-line interface.

    Parses command-line arguments and dispatches to appropriate MCPManager methods.

    Returns:
        Exit code: 0 for success, 1 for failure, None for help/invalid commands.
    """
    parser = argparse.ArgumentParser(description="MCP server management")
    parser.add_argument("action", choices=["add", "remove", "list", "available", "help"])
    parser.add_argument("server", nargs="?", help="Server name")
    args = parser.parse_args()

    manager = MCPManager()

    if args.action == "add":
        if not args.server:
            print("❌ Server name required for add action")
            return 1
        return manager.add_server(args.server)
    elif args.action == "remove":
        if not args.server:
            print("❌ Server name required for remove action")
            return 1
        return manager.remove_server(args.server)
    elif args.action == "list":
        return manager.list_servers()
    elif args.action == "available":
        return manager.list_available()
    elif args.action == "help":
        return manager.help()

if __name__ == "__main__":
    sys.exit(main())