#!/usr/bin/env python3
"""
Custom OTEL Metrics Sender for Claude Code
Sends custom metrics to the same OTEL collector that Claude uses
"""

import os
import time
import json
import sys
from datetime import datetime

# You can install this with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
try:
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.resources import Resource
except ImportError:
    print("Installing required packages...")
    os.system("pip install -q opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc")
    print("Please run the script again")
    sys.exit(0)

class CustomMetricsSender:
    def __init__(self):
        # Create resource with our custom service name
        resource = Resource.create({
            "service.name": "claude-custom-metrics",
            "service.version": "1.0.0",
            "user.email": os.environ.get("USER_EMAIL", "unknown"),
            "user.id": os.environ.get("USER", "unknown")
        })
        
        # Configure OTLP exporter to send to same collector as Claude
        otlp_exporter = OTLPMetricExporter(
            endpoint="localhost:7110",  # Same as Claude!
            insecure=True
        )
        
        # Set up metric reader
        metric_reader = PeriodicExportingMetricReader(
            exporter=otlp_exporter,
            export_interval_millis=30000  # 30 seconds like Claude
        )
        
        # Create meter provider
        provider = MeterProvider(
            resource=resource,
            metric_readers=[metric_reader]
        )
        
        # Set as global
        metrics.set_meter_provider(provider)
        
        # Create our meter
        self.meter = metrics.get_meter("claude_custom", "1.0.0")
        
        # Create metrics
        self.setup_metrics()
    
    def setup_metrics(self):
        """Define our custom metrics"""
        
        # Counter for compactions
        self.compact_counter = self.meter.create_counter(
            name="claude_custom_compact_count_total",
            description="Number of times session was compacted",
            unit="1"
        )
        
        # Counter for specific actions
        self.action_counter = self.meter.create_counter(
            name="claude_custom_action_count_total",
            description="Custom actions tracked",
            unit="1"
        )
        
        # Gauge for current state
        self.state_gauge = self.meter.create_up_down_counter(
            name="claude_custom_state",
            description="Current state value",
            unit="1"
        )
        
        # Histogram for timing
        self.timing_histogram = self.meter.create_histogram(
            name="claude_custom_operation_duration_seconds",
            description="Time taken for operations",
            unit="s"
        )
    
    def track_compact(self, session_id, user=None):
        """Track a session compaction"""
        labels = {
            "session_id": session_id,
            "user": user or os.environ.get("USER", "unknown"),
            "timestamp": str(int(time.time()))
        }
        self.compact_counter.add(1, labels)
        print(f"✅ Tracked compact for session {session_id}")
    
    def track_action(self, action_type, session_id=None, **extra_labels):
        """Track a custom action"""
        labels = {
            "action_type": action_type,
            "session_id": session_id or "unknown",
            "user": os.environ.get("USER", "unknown")
        }
        labels.update(extra_labels)
        self.action_counter.add(1, labels)
        print(f"✅ Tracked action: {action_type}")
    
    def track_timing(self, operation, duration, session_id=None):
        """Track operation timing"""
        labels = {
            "operation": operation,
            "session_id": session_id or "unknown"
        }
        self.timing_histogram.record(duration, labels)
        print(f"✅ Tracked timing: {operation} took {duration}s")

def main():
    """Example usage"""
    
    # Get session ID from environment or command line
    session_id = os.environ.get("CLAUDE_SESSION_ID", "test-session-123")
    
    if len(sys.argv) > 1:
        action = sys.argv[1]
        
        # Initialize sender
        sender = CustomMetricsSender()
        
        if action == "compact":
            # Track a compaction
            sender.track_compact(session_id)
            
        elif action == "action":
            # Track a custom action
            action_type = sys.argv[2] if len(sys.argv) > 2 else "unknown"
            sender.track_action(action_type, session_id)
            
        elif action == "timing":
            # Track timing
            operation = sys.argv[2] if len(sys.argv) > 2 else "operation"
            duration = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
            sender.track_timing(operation, duration, session_id)
            
        else:
            print(f"Unknown action: {action}")
            print("Usage: custom-metrics-sender.py [compact|action|timing] [args...]")
            
        # Keep running for a bit to ensure metrics are sent
        print("Sending metrics to OTEL collector...")
        time.sleep(2)
        
    else:
        print("Custom Metrics Sender")
        print("Usage: custom-metrics-sender.py [compact|action|timing] [args...]")
        print("")
        print("Examples:")
        print("  custom-metrics-sender.py compact")
        print("  custom-metrics-sender.py action 'file_save'")
        print("  custom-metrics-sender.py timing 'build' 45.2")

if __name__ == "__main__":
    main()