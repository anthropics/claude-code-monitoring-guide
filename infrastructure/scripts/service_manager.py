#!/usr/bin/env python3
"""
Service Manager - Unified docker service control for Claude Code Monitoring

This script provides a unified interface for managing docker services for
the Claude Code monitoring stack, hiding Docker complexity behind simple commands.

Supports: prometheus, grafana, pushgateway, otel-collector
"""

import argparse
import subprocess
import sys
import os
import json
import time
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceManagerError(Exception):
    """Custom exception for service manager errors."""
    pass

class ServiceManager:
    """Manages Docker services for Claude Code monitoring."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.compose_file = self.project_root / "docker-compose.yml"
        
        # Service definitions with clean 7100+ ports
        self.services = {
            'prometheus': {
                'container': 'prometheus',
                'port': 7100,
                'url': 'http://localhost:7100',
                'health_endpoint': '/api/v1/query?query=up',
                'description': 'Metrics collection and time-series database'
            },
            'pushgateway': {
                'container': 'pushgateway', 
                'port': 7101,
                'url': 'http://localhost:7101',
                'health_endpoint': '/metrics',
                'description': 'Push gateway for Claude Code hook metrics'
            },
            'grafana': {
                'container': 'grafana',
                'port': 7102,
                'url': 'http://localhost:7102',
                'credentials': 'admin/admin',
                'health_endpoint': '/api/health',
                'description': 'Monitoring dashboards and visualization'
            },
            'otel-collector': {
                'container': 'infrastructure-otel-collector-1',
                'ports': [7110, 7111, 7112],
                'url': 'http://localhost:7112',
                'health_endpoint': '/metrics',
                'description': 'OpenTelemetry metrics collection'
            }
        }
        
    def run_command(self, cmd: List[str], capture_output: bool = True, 
                   timeout: int = 30) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            logger.debug(f"Running command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=self.project_root
            )
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
            return 1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            logger.error(f"Command failed: {' '.join(cmd)} - {str(e)}")
            return 1, "", str(e)
    
    def get_service_names(self, services_arg: str) -> List[str]:
        """Parse services argument into list of service names."""
        if services_arg == 'all':
            return list(self.services.keys())
        return [s.strip() for s in services_arg.split(',') if s.strip()]
    
    def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check if a service is healthy."""
        if service_name not in self.services:
            return {'status': 'unknown', 'error': f'Unknown service: {service_name}'}
            
        service = self.services[service_name]
        
        # Check if container is running
        container_name = service['container']
        exit_code, stdout, stderr = self.run_command([
            'docker', 'ps', '--filter', f'name={container_name}', 
            '--filter', 'status=running', '--format', '{{.Names}}'
        ])
        
        if exit_code != 0 or container_name not in stdout:
            return {
                'status': 'stopped',
                'container': container_name,
                'error': 'Container not running'
            }
        
        # Check health endpoint if available
        if 'health_endpoint' in service:
            import requests
            try:
                url = service['url'] + service['health_endpoint']
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return {
                        'status': 'healthy',
                        'container': container_name,
                        'url': service['url']
                    }
                else:
                    return {
                        'status': 'unhealthy',
                        'container': container_name,
                        'error': f'Health check failed: HTTP {response.status_code}'
                    }
            except Exception as e:
                return {
                    'status': 'unhealthy', 
                    'container': container_name,
                    'error': f'Health check failed: {str(e)}'
                }
        
        return {
            'status': 'running',
            'container': container_name,
            'url': service.get('url', 'N/A')
        }
    
    def action_up(self, services: List[str]) -> int:
        """Start specified services."""
        print(f"🚀 Starting services: {', '.join(services)}")
        
        # Convert 'all' or validate service names
        if 'all' in services:
            service_args = []  # Start all services defined in docker-compose
        else:
            # Validate service names
            invalid_services = [s for s in services if s not in self.services]
            if invalid_services:
                print(f"❌ Invalid services: {', '.join(invalid_services)}")
                print(f"   Available: {', '.join(self.services.keys())}")
                return 1
            service_args = services
        
        # Use docker-compose to start services
        cmd = ['docker-compose', 'up', '-d'] + service_args
        exit_code, stdout, stderr = self.run_command(cmd, capture_output=False)
        
        if exit_code == 0:
            print("✅ Services started successfully")
            print("⏳ Waiting for services to be ready...")
            time.sleep(5)
            
            # Check health of started services
            services_to_check = services if 'all' not in services else list(self.services.keys())
            for service_name in services_to_check:
                if service_name in self.services:
                    health = self.check_service_health(service_name)
                    status_icon = "✅" if health['status'] in ['healthy', 'running'] else "⚠️"
                    print(f"   {status_icon} {service_name}: {health['status']}")
                    
                    # Show URL and credentials for Grafana
                    if service_name == 'grafana' and health['status'] in ['healthy', 'running']:
                        print(f"      🌐 URL: {health['url']}")
                        print(f"      🔑 Credentials: admin/admin")
        
        return exit_code
    
    def action_down(self, services: List[str]) -> int:
        """Stop specified services."""
        print(f"🛑 Stopping services: {', '.join(services)}")
        
        if 'all' in services:
            cmd = ['docker-compose', 'down']
        else:
            # Stop specific containers
            for service_name in services:
                if service_name in self.services:
                    container = self.services[service_name]['container']
                    exit_code, _, _ = self.run_command(['docker', 'stop', container])
                    status = "✅" if exit_code == 0 else "❌"
                    print(f"   {status} {service_name}")
            return 0
        
        exit_code, stdout, stderr = self.run_command(cmd, capture_output=False)
        
        if exit_code == 0:
            print("✅ Services stopped successfully")
        
        return exit_code
    
    def action_restart(self, services: List[str]) -> int:
        """Restart specified services."""
        print(f"🔄 Restarting services: {', '.join(services)}")
        
        # Stop services first
        stop_result = self.action_down(services)
        if stop_result != 0:
            return stop_result
            
        # Wait a moment
        time.sleep(2)
        
        # Start services
        return self.action_up(services)
    
    def action_status(self, services: List[str]) -> int:
        """Show status of specified services."""
        services_to_check = services if 'all' not in services else list(self.services.keys())
        
        print("🔍 Service Status")
        print("═" * 50)
        
        all_healthy = True
        for service_name in services_to_check:
            if service_name not in self.services:
                print(f"❓ {service_name}: Unknown service")
                all_healthy = False
                continue
                
            health = self.check_service_health(service_name)
            service_info = self.services[service_name]
            
            # Status icon
            if health['status'] == 'healthy':
                icon = "✅"
            elif health['status'] == 'running':
                icon = "🟡"
            elif health['status'] == 'stopped':
                icon = "🔴"
            else:
                icon = "❌"
                all_healthy = False
            
            print(f"{icon} {service_name:15} {health['status']:10} {health.get('url', 'N/A')}")
            
            if 'credentials' in service_info:
                print(f"   🔑 Credentials: {service_info['credentials']}")
                
            if 'error' in health:
                print(f"   ⚠️  Error: {health['error']}")
        
        return 0 if all_healthy else 1
    
    def action_console(self, services: List[str]) -> int:
        """Show console URLs and credentials for services."""
        if not services or 'all' in services:
            services = list(self.services.keys())
            
        print("🌐 Service Console Information")
        print("═" * 50)
        
        for service_name in services:
            if service_name not in self.services:
                continue
                
            service = self.services[service_name]
            health = self.check_service_health(service_name)
            
            if health['status'] in ['healthy', 'running']:
                print(f"✅ {service_name.upper()}")
                print(f"   🌐 URL: {service['url']}")
                if 'credentials' in service:
                    print(f"   🔑 Credentials: {service['credentials']}")
                print(f"   📝 {service['description']}")
                print()
            else:
                print(f"🔴 {service_name.upper()}: Not running")
                print(f"   Run: just service up {service_name}")
                print()
        
        return 0
    
    def action_logs(self, services: List[str]) -> int:
        """Show logs for specified services."""
        if not services or len(services) == 0:
            print("❌ Please specify a service for logs")
            return 1
            
        service_name = services[0]  # Take first service
        if service_name not in self.services:
            print(f"❌ Unknown service: {service_name}")
            return 1
            
        container = self.services[service_name]['container']
        print(f"📋 Logs for {service_name} ({container}):")
        print("═" * 50)
        
        # Use docker logs with follow
        exit_code = subprocess.call(['docker', 'logs', '-f', '--tail', '50', container])
        return exit_code
    
    def action_clean(self, level: str = 'containers') -> int:
        """Clean up Docker resources."""
        print(f"🧹 Cleaning up: {level}")
        
        if level == 'containers':
            # Remove stopped containers only
            exit_code, _, _ = self.run_command(['docker', 'container', 'prune', '-f'])
            if exit_code == 0:
                print("✅ Stopped containers removed")
        elif level == 'all':
            # Remove containers and networks (preserves data volumes)
            print("📦 Removing all containers and networks (data volumes preserved)")
            self.action_down(['all'])
            exit_code, _, _ = self.run_command(['docker-compose', 'down'])
            if exit_code == 0:
                print("✅ All containers and networks removed")
        elif level == 'data':
            # Remove data volumes (DATA LOSS!)
            print("⚠️  WARNING: This will permanently delete ALL monitoring data!")
            print("   📊 Prometheus metrics history")
            print("   📋 Grafana dashboards and settings")
            print("   🔄 Pushgateway pending metrics")
            print("")
            confirm = input("Type 'DELETE-DATA' to confirm: ")
            if confirm == 'DELETE-DATA':
                self.action_down(['all'])
                # Remove volumes with new project name
                exit_code, _, _ = self.run_command(['docker-compose', 'down', '-v'])
                # Also try to remove old project volumes (ignore errors if they don't exist)
                try:
                    self.run_command(['docker', 'volume', 'rm', 'claude-code-monitoring-guide_prometheus_data'])
                except:
                    pass
                try:
                    self.run_command(['docker', 'volume', 'rm', 'claude-code-monitoring-guide_grafana_data'])
                except:
                    pass  
                try:
                    self.run_command(['docker', 'volume', 'rm', 'claude-code-monitoring-guide_pushgateway_data'])
                except:
                    pass
                if exit_code == 0:
                    print("✅ All data volumes removed")
            else:
                print("❌ Cancelled")
                return 1
        
        return exit_code

def main():
    parser = argparse.ArgumentParser(description='Claude Code Monitoring Service Manager')
    parser.add_argument('--action', required=True,
                       choices=['up', 'down', 'restart', 'status', 'console', 'logs', 'clean'],
                       help='Action to perform')
    parser.add_argument('--services', default='all',
                       help='Comma-separated list of services or "all"')
    parser.add_argument('--level', default='containers',
                       choices=['containers', 'all', 'data'],
                       help='Clean level (for clean action)')
    
    args = parser.parse_args()
    
    try:
        manager = ServiceManager()
        services = manager.get_service_names(args.services)
        
        if args.action == 'up':
            return manager.action_up(services)
        elif args.action == 'down':
            return manager.action_down(services)
        elif args.action == 'restart':
            return manager.action_restart(services)
        elif args.action == 'status':
            return manager.action_status(services)
        elif args.action == 'console':
            return manager.action_console(services)
        elif args.action == 'logs':
            return manager.action_logs(services)
        elif args.action == 'clean':
            return manager.action_clean(args.level)
        else:
            print(f"❌ Unknown action: {args.action}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Service manager failed: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())