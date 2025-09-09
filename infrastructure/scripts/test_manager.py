#!/usr/bin/env python3
"""
Test Manager - Testing utilities for Claude Code Monitoring System

Provides comprehensive testing for hooks, metrics, and end-to-end data flow
to ensure the Claude Code monitoring stack is working correctly.
"""

import argparse
import json
import logging
import os
import requests
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import uuid
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestManagerError(Exception):
    """Custom exception for test manager errors."""
    pass

class TestManager:
    """Manages testing for Claude Code monitoring stack."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.hook_script = self.project_root / "../adapters/claude/hooks/muninn-claude-adapter-hook.sh"
        
        # Service endpoints
        self.endpoints = {
            'pushgateway': 'http://localhost:7101',
            'prometheus': 'http://localhost:7100',
            'grafana': 'http://localhost:7102'
        }
        
        self.test_results = []
        
    def run_command(self, cmd: List[str], capture_output: bool = True,
                   timeout: int = 30, input_data: str = None) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            logger.debug(f"Running command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                input=input_data,
                cwd=self.project_root
            )
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
            return 1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            logger.error(f"Command failed: {' '.join(cmd)} - {str(e)}")
            return 1, "", str(e)
    
    def make_request(self, url: str, method: str = 'GET', 
                    timeout: int = 10) -> Tuple[bool, Optional[requests.Response]]:
        """Make HTTP request and return success status and response."""
        try:
            response = requests.request(method, url, timeout=timeout)
            return True, response
        except requests.exceptions.ConnectionError:
            return False, None
        except Exception as e:
            logger.debug(f"Request failed: {str(e)}")
            return False, None
    
    def check_service_availability(self) -> Dict[str, bool]:
        """Check if all required services are available."""
        service_status = {}
        
        for service, url in self.endpoints.items():
            if service == 'pushgateway':
                success, response = self.make_request(f"{url}/metrics")
            elif service == 'prometheus':
                success, response = self.make_request(f"{url}/api/v1/query?query=up")
            elif service == 'grafana':
                success, response = self.make_request(f"{url}/api/health")
            else:
                success = False
            
            service_status[service] = success and (response.status_code == 200 if response else False)
        
        return service_status
    
    def generate_test_hook_data(self, tool_name: str = "Read", 
                              file_path: str = "/tmp/test.txt") -> str:
        """Generate test JSON data for hook testing."""
        test_data = {
            "event": "PostToolUse",
            "timestamp": datetime.now().isoformat(),
            "session_id": f"test-session-{uuid.uuid4().hex[:8]}",
            "user_id": f"test-user-{os.getlogin() if hasattr(os, 'getlogin') else 'testuser'}",
            "tool_name": tool_name,
            "tool_input": {
                "file_path": file_path
            },
            "tool_output": "Test output",
            "working_directory": str(self.project_root)
        }
        return json.dumps(test_data, indent=2)
    
    def test_hook_execution(self) -> bool:
        """Test that hook script executes correctly with mock data."""
        print("🔍 Testing hook script execution...")
        
        if not self.hook_script.exists():
            print(f"   ❌ Hook script not found: {self.hook_script}")
            return False
        
        if not os.access(self.hook_script, os.X_OK):
            print(f"   ❌ Hook script not executable: {self.hook_script}")
            return False
        
        # Generate test data
        test_json = self.generate_test_hook_data()
        print(f"   📊 Sending test data to hook...")
        
        # Run hook with test data
        exit_code, stdout, stderr = self.run_command(
            [str(self.hook_script)],
            input_data=test_json,
            timeout=15
        )
        
        if exit_code == 0:
            print(f"   ✅ Hook executed successfully")
            if stdout.strip():
                print(f"   📝 Hook output: {stdout.strip()}")
            return True
        else:
            print(f"   ❌ Hook execution failed (exit code: {exit_code})")
            if stderr:
                print(f"   🐛 Error: {stderr.strip()}")
            return False
    
    def test_pushgateway_connectivity(self) -> bool:
        """Test that we can connect to pushgateway and read metrics."""
        print("🔍 Testing Pushgateway connectivity...")
        
        success, response = self.make_request(f"{self.endpoints['pushgateway']}/metrics")
        
        if not success:
            print(f"   ❌ Cannot connect to Pushgateway at {self.endpoints['pushgateway']}")
            return False
        
        if response.status_code != 200:
            print(f"   ❌ Pushgateway returned HTTP {response.status_code}")
            return False
        
        print(f"   ✅ Pushgateway connected successfully")
        
        # Check for existing Claude metrics
        metrics_text = response.text
        claude_metrics = [line for line in metrics_text.split('\n') 
                         if line.startswith('claude_custom')]
        
        if claude_metrics:
            print(f"   📊 Found {len(claude_metrics)} existing Claude metrics")
        else:
            print(f"   ℹ️  No existing Claude metrics (expected for fresh install)")
        
        return True
    
    def test_metric_injection(self) -> bool:
        """Test injecting a custom metric directly to pushgateway."""
        print("🔍 Testing direct metric injection...")
        
        test_metric = f"""claude_custom_test_metric{{session_id="test-session",tool="TestTool",user="testuser"}} 1\n"""
        
        try:
            response = requests.post(
                f"{self.endpoints['pushgateway']}/metrics/job/claude_code_test",
                data=test_metric,
                headers={'Content-Type': 'text/plain'},
                timeout=10
            )
            
            if response.status_code in [200, 202]:
                print(f"   ✅ Test metric injected successfully")
                
                # Wait a moment then verify it exists
                time.sleep(2)
                success, metrics_response = self.make_request(f"{self.endpoints['pushgateway']}/metrics")
                
                if success and 'claude_custom_test_metric' in metrics_response.text:
                    print(f"   ✅ Test metric confirmed in pushgateway")
                    return True
                else:
                    print(f"   ⚠️  Test metric injected but not found in metrics endpoint")
                    return False
            else:
                print(f"   ❌ Failed to inject metric: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error injecting metric: {str(e)}")
            return False
    
    def test_prometheus_scraping(self) -> bool:
        """Test that Prometheus can scrape pushgateway metrics."""
        print("🔍 Testing Prometheus scraping...")
        
        # Check if we can query Prometheus
        success, response = self.make_request(
            f"{self.endpoints['prometheus']}/api/v1/query?query=up"
        )
        
        if not success:
            print(f"   ❌ Cannot connect to Prometheus at {self.endpoints['prometheus']}")
            return False
        
        if response.status_code != 200:
            print(f"   ❌ Prometheus returned HTTP {response.status_code}")
            return False
        
        print(f"   ✅ Prometheus connected successfully")
        
        # Query for Claude metrics
        success, response = self.make_request(
            f"{self.endpoints['prometheus']}/api/v1/query?query=claude_custom_tool_usage_total"
        )
        
        if success and response.status_code == 200:
            data = response.json()
            if data.get('data', {}).get('result'):
                metric_count = len(data['data']['result'])
                print(f"   ✅ Found {metric_count} Claude tool usage metrics")
            else:
                print(f"   ℹ️  No Claude tool usage metrics found (expected for fresh install)")
        
        return True
    
    def generate_test_agent_data(self, agent_type: str = "search", task_description: str = "Test agent task") -> str:
        """Generate test JSON data for agent/Task tool testing."""
        test_data = {
            "event": "PreToolUse",
            "timestamp": datetime.now().isoformat(),
            "session_id": f"agent-test-{uuid.uuid4().hex[:8]}",
            "user_id": f"test-user-{os.getlogin() if hasattr(os, 'getlogin') else 'testuser'}",
            "tool_name": "Task",
            "tool_input": {
                "subagent_type": agent_type,
                "description": task_description,
                "prompt": f"Test prompt for {task_description} using {agent_type} agent"
            },
            "working_directory": str(self.project_root)
        }
        return json.dumps(test_data, indent=2)
    
    def test_agent_metrics_collection(self) -> bool:
        """Test that agent metrics are collected correctly."""
        print("🔍 Testing agent metrics collection...")
        
        # Generate unique test data for agent
        test_session_id = f"agent-test-{uuid.uuid4().hex[:8]}"
        agent_type = "search"
        task_description = "Search for test files to validate agent metrics"
        
        test_json = self.generate_test_agent_data(agent_type, task_description)
        
        # Parse to set our specific session ID
        test_data = json.loads(test_json)
        test_data['session_id'] = test_session_id
        test_json = json.dumps(test_data, indent=2)
        
        print(f"   📊 Testing agent: {agent_type} with session ID: {test_session_id}")
        
        # Execute hook with agent data
        exit_code, stdout, stderr = self.run_command(
            [str(self.hook_script)],
            input_data=test_json,
            timeout=15
        )
        
        if exit_code != 0:
            print(f"   ❌ Agent hook execution failed: {stderr}")
            return False
        
        print(f"   ✅ Agent hook executed successfully")
        
        # Wait for metrics to be processed
        time.sleep(3)
        
        # Check if agent-specific metrics appear in pushgateway
        success, response = self.make_request(f"{self.endpoints['pushgateway']}/metrics")
        if not success:
            print(f"   ❌ Cannot connect to Pushgateway for agent metric verification")
            return False
        
        metrics_text = response.text
        agent_metrics_found = []
        
        # Check for specific agent metrics
        agent_metric_types = [
            'claude_custom_agent_usage_total',
            'claude_custom_agent_prompt_length_total', 
            'claude_custom_agent_tasks_by_type_total'
        ]
        
        for metric_type in agent_metric_types:
            if test_session_id in metrics_text and metric_type in metrics_text:
                agent_metrics_found.append(metric_type)
        
        if agent_metrics_found:
            print(f"   ✅ Found {len(agent_metrics_found)} agent metrics in Pushgateway")
            for metric in agent_metrics_found:
                print(f"       • {metric}")
        else:
            print(f"   ⚠️  Agent metrics not found in Pushgateway (may take time to appear)")
            return False
        
        # Verify agent metrics in Prometheus
        query_url = f"{self.endpoints['prometheus']}/api/v1/query?query=claude_custom_agent_usage_total{{session_id=\"{test_session_id}\"}}"
        success, response = self.make_request(query_url)
        
        if success and response.status_code == 200:
            data = response.json()
            if data.get('data', {}).get('result'):
                print(f"   ✅ Agent metrics found in Prometheus")
                return True
            else:
                print(f"   ℹ️  Agent metrics not yet in Prometheus (scraping takes time)")
        
        return len(agent_metrics_found) > 0

    def test_end_to_end_flow(self) -> bool:
        """Test complete flow from hook execution to metric visibility."""
        print("🔍 Testing end-to-end metric flow...")
        
        # Generate unique test data
        test_session_id = f"e2e-test-{uuid.uuid4().hex[:8]}"
        test_tool = "EndToEndTest"
        test_json = self.generate_test_hook_data(test_tool, "/tmp/e2e-test.txt")
        
        # Parse to get session ID for verification
        test_data = json.loads(test_json)
        test_data['session_id'] = test_session_id
        test_json = json.dumps(test_data, indent=2)
        
        print(f"   📊 Running hook with session ID: {test_session_id}")
        
        # Execute hook
        exit_code, stdout, stderr = self.run_command(
            [str(self.hook_script)],
            input_data=test_json,
            timeout=15
        )
        
        if exit_code != 0:
            print(f"   ❌ Hook execution failed: {stderr}")
            return False
        
        print(f"   ✅ Hook executed successfully")
        
        # Check if metric appears in pushgateway first (should be immediate)
        print(f"   ⏳ Waiting for metric to reach Pushgateway...")
        time.sleep(2)
        
        success, response = self.make_request(f"{self.endpoints['pushgateway']}/metrics")
        if not (success and test_session_id in response.text):
            print(f"   ❌ Metric not found in Pushgateway")
            return False
        
        print(f"   ✅ Metric found in Pushgateway")
        
        # Poll Prometheus for up to 60 seconds (2 full scrape cycles)
        print(f"   ⏳ Polling Prometheus for metric (up to 60s, checking every 10s)...")
        query_url = f"{self.endpoints['prometheus']}/api/v1/query?query=claude_custom_tool_usage_total{{session_id=\"{test_session_id}\"}}"
        
        for attempt in range(6):  # 6 attempts * 10 seconds = 60 seconds total
            time.sleep(10)
            
            success, response = self.make_request(query_url)
            if success and response.status_code == 200:
                data = response.json()
                if data.get('data', {}).get('result'):
                    elapsed = (attempt + 1) * 10
                    print(f"   ✅ Metric found in Prometheus after {elapsed}s")
                    return True
            
            print(f"   ⏳ Attempt {attempt + 1}/6: Not yet scraped by Prometheus...")
        
        print(f"   ❌ Metric not found in Prometheus after 60s (scraping issue)")
        return False
    
    def test_hooks(self) -> int:
        """Run all hook-related tests."""
        print("🧪 Testing Claude Code Hooks")
        print("═" * 50)
        
        tests = [
            ("Hook Script Execution", self.test_hook_execution),
            ("Pushgateway Connectivity", self.test_pushgateway_connectivity),
            ("Direct Metric Injection", self.test_metric_injection)
        ]
        
        passed = 0
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                print()  # Blank line between tests
            except Exception as e:
                print(f"   ❌ Test failed with exception: {str(e)}")
                print()
        
        print(f"📊 Hook Tests: {passed}/{len(tests)} passed")
        return 0 if passed == len(tests) else 1
    
    def test_agents(self) -> int:
        """Run all agent-related tests."""
        print("🧪 Testing Agent Metrics Collection")
        print("═" * 50)
        
        tests = [
            ("Agent Metrics Collection", self.test_agent_metrics_collection),
        ]
        
        passed = 0
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                print()  # Blank line between tests
            except Exception as e:
                print(f"   ❌ Test failed with exception: {str(e)}")
                print()
        
        print(f"📊 Agent Tests: {passed}/{len(tests)} passed")
        return 0 if passed == len(tests) else 1
    
    def test_metrics(self) -> int:
        """Run all metrics-related tests."""
        print("🧪 Testing Metrics Collection")
        print("═" * 50)
        
        tests = [
            ("Pushgateway Connectivity", self.test_pushgateway_connectivity),
            ("Prometheus Connectivity", self.test_prometheus_scraping),
            ("Direct Metric Injection", self.test_metric_injection)
        ]
        
        passed = 0
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                print()  # Blank line between tests
            except Exception as e:
                print(f"   ❌ Test failed with exception: {str(e)}")
                print()
        
        print(f"📊 Metrics Tests: {passed}/{len(tests)} passed")
        return 0 if passed == len(tests) else 1
    
    def test_flow(self) -> int:
        """Run end-to-end flow tests."""
        print("🧪 Testing End-to-End Data Flow")
        print("═" * 50)
        
        # Check service availability first
        service_status = self.check_service_availability()
        missing_services = [svc for svc, status in service_status.items() if not status]
        
        if missing_services:
            print(f"❌ Required services not available: {', '.join(missing_services)}")
            print(f"   Run 'just up' to start all services")
            return 1
        
        print(f"✅ All required services available")
        print()
        
        try:
            success = self.test_end_to_end_flow()
            return 0 if success else 1
        except Exception as e:
            print(f"❌ End-to-end test failed: {str(e)}")
            return 1
    
    def test_all(self) -> int:
        """Run all tests."""
        print("🧪 Running All Claude Code Monitoring Tests")
        print("═" * 60)
        
        # Check service availability first
        print("🔍 Checking service availability...")
        service_status = self.check_service_availability()
        
        for service, status in service_status.items():
            icon = "✅" if status else "❌"
            print(f"   {icon} {service}: {'Available' if status else 'Not available'}")
        
        missing_services = [svc for svc, status in service_status.items() if not status]
        if missing_services:
            print(f"\n⚠️  Some services unavailable. Run 'just up' first.")
            print()
        
        # Run all test categories
        hook_result = self.test_hooks()
        print()
        
        agent_result = self.test_agents()
        print()
        
        metrics_result = self.test_metrics()
        print()
        
        flow_result = self.test_flow()
        print()
        
        # Summary
        total_tests = 4
        passed_tests = sum([1 for result in [hook_result, agent_result, metrics_result, flow_result] if result == 0])
        
        print("🏁 Final Test Summary")
        print("═" * 30)
        print(f"   Hook Tests: {'✅ PASS' if hook_result == 0 else '❌ FAIL'}")
        print(f"   Agent Tests: {'✅ PASS' if agent_result == 0 else '❌ FAIL'}")
        print(f"   Metrics Tests: {'✅ PASS' if metrics_result == 0 else '❌ FAIL'}")
        print(f"   Flow Tests: {'✅ PASS' if flow_result == 0 else '❌ FAIL'}")
        print(f"\n   Overall: {passed_tests}/{total_tests} test categories passed")
        
        return 0 if passed_tests == total_tests else 1

def main():
    parser = argparse.ArgumentParser(description='Claude Code Monitoring Test Manager')
    parser.add_argument('--type', required=True,
                       choices=['hooks', 'agents', 'metrics', 'flow', 'all'],
                       help='Type of test to run')
    
    args = parser.parse_args()
    
    try:
        manager = TestManager()
        
        if args.type == 'hooks':
            return manager.test_hooks()
        elif args.type == 'agents':
            return manager.test_agents()
        elif args.type == 'metrics':
            return manager.test_metrics()
        elif args.type == 'flow':
            return manager.test_flow()
        elif args.type == 'all':
            return manager.test_all()
        else:
            print(f"❌ Unknown test type: {args.type}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Tests cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Test manager failed: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())