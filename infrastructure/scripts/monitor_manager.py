#!/usr/bin/env python3
"""
Monitor Manager - Monitoring operations for Claude Code Monitoring

Provides unified interface for monitoring-related operations like health checks,
log monitoring, metrics validation, and status reporting.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MonitorManager:
    """Manages monitoring operations for Claude Code monitoring stack."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        
        # Service endpoints with clean 7100+ ports
        self.endpoints = {
            'prometheus': {
                'url': 'http://localhost:7100',
                'health': '/api/v1/query?query=up',
                'metrics': '/api/v1/label/__name__/values'
            },
            'pushgateway': {
                'url': 'http://localhost:7101', 
                'health': '/metrics',
                'metrics': '/metrics'
            },
            'grafana': {
                'url': 'http://localhost:7102',
                'health': '/api/health',
                'login': '/api/user',
                'dashboards': '/api/search'
            },
            'otel-collector': {
                'url': 'http://localhost:7112',
                'health': '/metrics',
                'metrics': '/metrics'
            }
        }
        
        # Hook configuration
        self.hook_script = self.project_root / "../adapters/claude/hooks/muninn-claude-adapter-hook.sh"
        
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
    
    def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check if a service endpoint is healthy."""
        if service_name not in self.endpoints:
            return {'status': 'unknown', 'error': f'Unknown service: {service_name}'}
        
        endpoint = self.endpoints[service_name]
        
        try:
            # Check health endpoint
            health_url = endpoint['url'] + endpoint['health']
            response = requests.get(health_url, timeout=5)
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'url': endpoint['url'],
                    'response_time': response.elapsed.total_seconds(),
                    'response_size': len(response.content)
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': f'HTTP {response.status_code}',
                    'url': endpoint['url']
                }
        except requests.exceptions.ConnectionError:
            return {
                'status': 'down',
                'error': 'Connection refused - service not running',
                'url': endpoint['url']
            }
        except requests.exceptions.Timeout:
            return {
                'status': 'timeout',
                'error': 'Request timed out',
                'url': endpoint['url']
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'url': endpoint['url']
            }
    
    def get_metrics_count(self, service_name: str) -> Dict[str, Any]:
        """Get count of metrics from a service."""
        if service_name not in self.endpoints:
            return {'error': f'Unknown service: {service_name}'}
            
        endpoint = self.endpoints[service_name]
        
        try:
            if service_name == 'prometheus':
                # Query Prometheus for metric names
                url = f"{endpoint['url']}/api/v1/label/__name__/values"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    metric_names = data.get('data', [])
                    claude_metrics = [m for m in metric_names if m.startswith('claude_custom')]
                    
                    return {
                        'total_metrics': len(metric_names),
                        'claude_metrics': len(claude_metrics),
                        'claude_metric_names': claude_metrics
                    }
            
            elif service_name in ['pushgateway', 'otel-collector']:
                # Get raw metrics and count lines
                url = endpoint['url'] + endpoint['metrics']
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    lines = response.text.strip().split('\n')
                    metric_lines = [l for l in lines if l and not l.startswith('#')]
                    claude_lines = [l for l in metric_lines if 'claude_custom' in l]
                    
                    return {
                        'total_metric_lines': len(metric_lines),
                        'claude_metric_lines': len(claude_lines),
                        'sample_metrics': claude_lines[:5]  # First 5 for preview
                    }
            
        except Exception as e:
            return {'error': str(e)}
        
        return {'error': 'Unsupported service for metrics counting'}
    
    def action_status(self, service: str = 'all') -> int:
        """Show monitoring status of all services."""
        services_to_check = list(self.endpoints.keys()) if service == 'all' else [service]
        
        print("🔍 Monitoring Stack Health Status")
        print("═" * 60)
        print(f"{'Service':<15} {'Status':<12} {'Response':<10} {'URL'}")
        print("─" * 60)
        
        all_healthy = True
        
        for service_name in services_to_check:
            if service_name not in self.endpoints:
                print(f"❓ {service_name}: Unknown service")
                all_healthy = False
                continue
            
            health = self.check_service_health(service_name)
            
            # Status icon and formatting
            if health['status'] == 'healthy':
                icon = "✅"
                response_time = f"{health.get('response_time', 0):.2f}s"
            elif health['status'] == 'down':
                icon = "🔴"
                response_time = "N/A"
                all_healthy = False
            elif health['status'] == 'timeout':
                icon = "⏱️"
                response_time = ">5s"
                all_healthy = False
            else:
                icon = "❌"
                response_time = "ERROR"
                all_healthy = False
            
            print(f"{icon} {service_name:<14} {health['status']:<11} {response_time:<9} {health['url']}")
            
            if 'error' in health:
                print(f"   ⚠️  {health['error']}")
        
        # Show Claude metrics summary
        print("\n📊 Claude Code Metrics Summary")
        print("─" * 40)
        
        # Get metrics from Pushgateway (most relevant for Claude hooks)
        metrics_info = self.get_metrics_count('pushgateway')
        if 'error' not in metrics_info:
            print(f"   Claude Metrics: {metrics_info.get('claude_metric_lines', 0)}")
            print(f"   Total Metrics:  {metrics_info.get('total_metric_lines', 0)}")
            
            if metrics_info.get('sample_metrics'):
                print("   Recent Metrics:")
                for metric in metrics_info['sample_metrics'][:3]:
                    if len(metric) > 80:
                        metric = metric[:77] + "..."
                    print(f"     • {metric}")
        else:
            print(f"   ❌ Could not fetch metrics: {metrics_info['error']}")
        
        return 0 if all_healthy else 1
    
    def action_logs(self, service: str) -> int:
        """Show logs for a specific service."""
        if service == 'all':
            print("❌ Please specify a specific service for logs")
            print("   Available: prometheus, grafana, pushgateway, otel-collector")
            return 1
        
        # Map service names to container names
        container_map = {
            'prometheus': 'prometheus',
            'grafana': 'grafana', 
            'pushgateway': 'pushgateway',
            'otel-collector': 'infrastructure-otel-collector-1'
        }
        
        if service not in container_map:
            print(f"❌ Unknown service: {service}")
            print(f"   Available: {', '.join(container_map.keys())}")
            return 1
        
        container_name = container_map[service]
        
        print(f"📋 Following logs for {service} ({container_name})")
        print("   Press Ctrl+C to stop")
        print("═" * 60)
        
        try:
            # Use docker logs with follow
            exit_code = subprocess.call([
                'docker', 'logs', '-f', '--tail', '50', container_name
            ])
            return exit_code
        except KeyboardInterrupt:
            print("\n⚠️ Log following stopped")
            return 0
    
    def action_validate(self) -> int:
        """Validate the entire monitoring stack."""
        print("🔍 Validating Claude Code Monitoring Stack")
        print("═" * 60)
        
        validation_errors = []
        
        # 1. Check all services are healthy
        print("1. Checking service health...")
        for service_name in self.endpoints.keys():
            health = self.check_service_health(service_name)
            if health['status'] == 'healthy':
                print(f"   ✅ {service_name}: OK")
            else:
                print(f"   ❌ {service_name}: {health.get('error', 'Unknown error')}")
                validation_errors.append(f"{service_name} not healthy")
        
        # 2. Check Docker containers
        print("\n2. Checking Docker containers...")
        containers = ['prometheus', 'grafana', 'pushgateway', 
                     'infrastructure-otel-collector-1']
        
        for container in containers:
            exit_code, stdout, _ = self.run_command([
                'docker', 'ps', '--filter', f'name={container}',
                '--filter', 'status=running', '--format', '{{.Names}}'
            ])
            
            if exit_code == 0 and container in stdout:
                print(f"   ✅ {container}: Running")
            else:
                print(f"   ❌ {container}: Not running")
                validation_errors.append(f"{container} container not running")
        
        # 3. Check hook script exists and is executable
        print("\n3. Checking Claude Code hooks...")
        if self.hook_script.exists():
            if os.access(self.hook_script, os.X_OK):
                print(f"   ✅ Hook script: {self.hook_script} (executable)")
            else:
                print(f"   ⚠️  Hook script: {self.hook_script} (not executable)")
                validation_errors.append("Hook script not executable")
        else:
            print(f"   ❌ Hook script: {self.hook_script} (missing)")
            validation_errors.append("Hook script missing")
        
        # 4. Check metrics flow
        print("\n4. Checking metrics collection...")
        metrics_info = self.get_metrics_count('pushgateway')
        if 'error' not in metrics_info:
            claude_count = metrics_info.get('claude_metric_lines', 0)
            if claude_count > 0:
                print(f"   ✅ Claude metrics: {claude_count} metrics collected")
            else:
                print(f"   ⚠️  Claude metrics: No metrics found (hooks may not be firing)")
                validation_errors.append("No Claude metrics found")
        else:
            print(f"   ❌ Metrics check failed: {metrics_info['error']}")
            validation_errors.append("Cannot check metrics")
        
        # 5. Check Grafana dashboards
        print("\n5. Checking Grafana dashboards...")
        try:
            response = requests.get(
                f"{self.endpoints['grafana']['url']}/api/search",
                auth=('admin', 'admin'),
                timeout=10
            )
            
            if response.status_code == 200:
                dashboards = response.json()
                dashboard_count = len(dashboards)
                print(f"   ✅ Grafana dashboards: {dashboard_count} found")
                
                # Look for Claude-specific dashboards
                claude_dashboards = [d for d in dashboards if 'claude' in d.get('title', '').lower()]
                if claude_dashboards:
                    print(f"   ✅ Claude dashboards: {len(claude_dashboards)} found")
                    for dash in claude_dashboards:
                        print(f"      • {dash.get('title', 'Untitled')}")
                else:
                    print(f"   ⚠️  No Claude-specific dashboards found")
            else:
                print(f"   ❌ Cannot access Grafana API: HTTP {response.status_code}")
                validation_errors.append("Cannot access Grafana")
                
        except Exception as e:
            print(f"   ❌ Grafana check failed: {str(e)}")
            validation_errors.append("Grafana validation failed")
        
        # Summary
        print("\n" + "═" * 60)
        if not validation_errors:
            print("🎉 All validation checks passed!")
            print("\n💡 Your Claude Code monitoring stack is healthy and ready!")
            return 0
        else:
            print(f"❌ Found {len(validation_errors)} issues:")
            for i, error in enumerate(validation_errors, 1):
                print(f"   {i}. {error}")
            
            print(f"\n💡 Run 'just service status' and 'just up' to resolve issues")
            return 1
    
    def action_metrics_count(self, service: str = 'all') -> int:
        """Show detailed metrics count for services."""
        services_to_check = list(self.endpoints.keys()) if service == 'all' else [service]
        
        print("📊 Metrics Count Report")
        print("═" * 50)
        
        for service_name in services_to_check:
            if service_name not in self.endpoints:
                continue
                
            print(f"\n🔍 {service_name.upper()}")
            print("─" * 30)
            
            metrics_info = self.get_metrics_count(service_name)
            
            if 'error' in metrics_info:
                print(f"   ❌ Error: {metrics_info['error']}")
                continue
            
            # Display metrics based on service type
            if service_name == 'prometheus':
                print(f"   Total metrics: {metrics_info.get('total_metrics', 0)}")
                print(f"   Claude metrics: {metrics_info.get('claude_metrics', 0)}")
                
                claude_names = metrics_info.get('claude_metric_names', [])
                if claude_names:
                    print("   Claude metric types:")
                    for name in claude_names:
                        print(f"     • {name}")
            
            elif service_name in ['pushgateway', 'otel-collector']:
                print(f"   Total metric lines: {metrics_info.get('total_metric_lines', 0)}")
                print(f"   Claude metric lines: {metrics_info.get('claude_metric_lines', 0)}")
                
                samples = metrics_info.get('sample_metrics', [])
                if samples:
                    print("   Sample Claude metrics:")
                    for sample in samples:
                        if len(sample) > 70:
                            sample = sample[:67] + "..."
                        print(f"     • {sample}")
        
        return 0

def main():
    parser = argparse.ArgumentParser(description='Claude Code Monitor Manager')
    parser.add_argument('--action', required=True,
                       choices=['status', 'logs', 'validate', 'metrics-count'],
                       help='Action to perform')
    parser.add_argument('--service', default='all',
                       help='Service name or "all"')
    
    args = parser.parse_args()
    
    try:
        manager = MonitorManager()
        
        if args.action == 'status':
            return manager.action_status(args.service)
        elif args.action == 'logs':
            return manager.action_logs(args.service)
        elif args.action == 'validate':
            return manager.action_validate()
        elif args.action == 'metrics-count':
            return manager.action_metrics_count(args.service)
        else:
            print(f"❌ Unknown action: {args.action}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Monitor manager failed: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())