#!/usr/bin/env python3
"""
Claude Code Session Detector
A lightweight helper for AI agents to detect Claude Code session info

Usage in existing AI agents:
    from claude_session_detector import get_claude_session_info
    
    # Your existing LLM call (OpenRouter, Anthropic, etc.)
    response = your_existing_api_call(prompt)
    
    # Optional session detection + metrics
    session_info = get_claude_session_info()
    if session_info:
        send_metrics_to_monitoring(session_info, your_metrics)
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class ClaudeSessionInfo:
    """Session information detected from Claude Code"""
    session_id: str
    working_directory: str
    model: Optional[str] = None
    user_context: Optional[str] = None
    available_tools: Optional[list] = None

class ClaudeSessionDetector:
    """Lightweight Claude Code session detector"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self._session_cache = None
        self._cache_timeout = 60  # Cache for 60 seconds
        self._last_detection = 0
        
    async def detect_session(self) -> Optional[ClaudeSessionInfo]:
        """
        Detect current Claude Code session using minimal SDK query
        Returns None if Claude Code not available (non-breaking)
        """
        import time
        
        # Use cached session info if recent
        if (self._session_cache and 
            time.time() - self._last_detection < self._cache_timeout):
            return self._session_cache
            
        try:
            # Try to import Claude Code SDK
            from claude_code_sdk import query, ClaudeCodeOptions, CLINotFoundError
            
            # Minimal query just to get session context
            options = ClaudeCodeOptions(
                max_turns=1,
                allowed_tools=[]  # No tools needed, just session detection
            )
            
            # Super minimal query to avoid any actual work
            async for message in query(
                prompt=f"[{self.agent_name}] session detection", 
                options=options
            ):
                # Extract session info from message metadata
                # NOTE: This depends on the actual message structure
                # which may need investigation
                if hasattr(message, 'session_id'):
                    session_info = ClaudeSessionInfo(
                        session_id=message.session_id,
                        working_directory=getattr(message, 'cwd', ''),
                        model=getattr(message, 'model', None),
                        available_tools=getattr(message, 'tools', None)
                    )
                    
                    self._session_cache = session_info
                    self._last_detection = time.time()
                    return session_info
                break
                
        except (ImportError, CLINotFoundError, Exception) as e:
            # Claude Code not available or not working - fail silently
            logging.debug(f"Claude Code session detection failed: {e}")
            return None
            
        return None

# Simple synchronous wrapper for easier integration
def get_claude_session_info(agent_name: str = "ai-agent") -> Optional[ClaudeSessionInfo]:
    """
    Simple function to get Claude Code session info
    Returns None if not available (non-breaking)
    """
    detector = ClaudeSessionDetector(agent_name)
    try:
        return asyncio.run(detector.detect_session())
    except Exception as e:
        logging.debug(f"Session detection failed: {e}")
        return None

def send_agent_metrics(
    agent_name: str,
    operation: str,
    duration_ms: int,
    token_count: int = 0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_usd: float = 0.0,
    model: str = "unknown",
    success: bool = True,
    pushgateway_url: str = "http://localhost:7101"
) -> bool:
    """
    Send AI agent metrics to monitoring stack
    Automatically includes session info if available
    """
    session_info = get_claude_session_info(agent_name)
    
    # Build metrics with optional session correlation
    session_id = session_info.session_id if session_info else "no-session"
    
    import requests
    import time
    timestamp_id = int(time.time() * 1000)
    
    try:
        url = f"{pushgateway_url}/metrics/job/ai_agents/agent/{agent_name}/session/{session_id}/ts/{timestamp_id}"
        
        metrics_parts = [
            f"""# TYPE ai_agent_usage_total counter
ai_agent_usage_total{{agent_name="{agent_name}",operation="{operation}",model="{model}",success="{success}"}} 1

# TYPE ai_agent_duration_ms_total counter
ai_agent_duration_ms_total{{agent_name="{agent_name}",session_id="{session_id}"}} {duration_ms}

# TYPE ai_agent_cost_usd_total counter
ai_agent_cost_usd_total{{agent_name="{agent_name}",model="{model}"}} {cost_usd}"""
        ]
        
        # Add total tokens if provided
        if token_count > 0:
            metrics_parts.append(f"""
# TYPE ai_agent_tokens_total counter
ai_agent_tokens_total{{agent_name="{agent_name}",model="{model}"}} {token_count}""")
        
        # Add input tokens if provided  
        if input_tokens > 0:
            metrics_parts.append(f"""
# TYPE ai_agent_input_tokens_total counter
ai_agent_input_tokens_total{{agent_name="{agent_name}",model="{model}"}} {input_tokens}""")
        
        # Add output tokens if provided
        if output_tokens > 0:
            metrics_parts.append(f"""
# TYPE ai_agent_output_tokens_total counter
ai_agent_output_tokens_total{{agent_name="{agent_name}",model="{model}"}} {output_tokens}""")
        
        metrics = "\n".join(metrics_parts) + "\n"
        
        response = requests.post(url, data=metrics, headers={'Content-Type': 'text/plain'}, timeout=5)
        return response.status_code == 200
        
    except Exception as e:
        logging.debug(f"Failed to send metrics: {e}")
        return False

# Example integration patterns
class ExampleIntegration:
    """Examples of how existing AI agents would integrate"""
    
    def doc_finder_integration_example(self):
        """How doc-finder would integrate (keeps OpenRouter)"""
        
        # doc-finder's existing OpenRouter call
        import requests
        start_time = time.time()
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": "Bearer your-openrouter-key"},
            json={"model": "meta-llama/llama-3.1-8b-instruct", "messages": []}
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        usage = response.json().get('usage', {})
        total_tokens = usage.get('total_tokens', 0)
        input_tokens = usage.get('prompt_tokens', 0)  # OpenRouter uses prompt_tokens
        output_tokens = usage.get('completion_tokens', 0)  # OpenRouter uses completion_tokens
        
        # NEW: Optional metrics with session detection (supports input/output token breakdown)
        send_agent_metrics(
            agent_name="doc-finder",
            operation="search",
            duration_ms=duration_ms,
            token_count=total_tokens,  # Total tokens for compatibility
            input_tokens=input_tokens,  # Input tokens if available
            output_tokens=output_tokens,  # Output tokens if available
            cost_usd=total_tokens * 0.000002,  # OpenRouter cost estimation
            model="llama-3.1-8b",
            success=response.status_code == 200
        )
    
    def git_info_integration_example(self):
        """How git-info would integrate (keeps Anthropic API)"""
        
        # git-info's existing Anthropic call
        from anthropic import Anthropic
        import time
        
        client = Anthropic(api_key="your-anthropic-key")
        start_time = time.time()
        
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            messages=[{"role": "user", "content": "analyze commit"}]
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        total_tokens = input_tokens + output_tokens
        
        # NEW: Optional metrics with session detection (Anthropic provides input/output breakdown)
        send_agent_metrics(
            agent_name="git-info",
            operation="commit-analysis",
            duration_ms=duration_ms,
            token_count=total_tokens,  # Total tokens for compatibility
            input_tokens=input_tokens,  # Anthropic provides separate input tokens
            output_tokens=output_tokens,  # Anthropic provides separate output tokens
            cost_usd=0.003,  # Anthropic cost
            model="claude-3-sonnet",
            success=True
        )

if __name__ == "__main__":
    # Test session detection
    session_info = get_claude_session_info("test-agent")
    if session_info:
        print(f"✅ Claude Code session detected: {session_info.session_id}")
        print(f"Working directory: {session_info.working_directory}")
    else:
        print("❌ No Claude Code session detected (this is normal if not running in Claude)")