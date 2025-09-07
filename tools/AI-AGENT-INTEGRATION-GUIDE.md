# AI Agent Session Detection Integration Guide

## 🎯 **Goal: Lightweight, Optional Session Correlation**

Add session tracking to existing AI agents **without breaking changes** or forcing API migration.

## 🏗️ **Architecture: Keep Your APIs + Add Session Detection**

```
┌─────────────────────────────────────────────────┐
│ EXISTING AI AGENT (no changes to core logic)   │
├─────────────────────────────────────────────────┤
│ • doc-finder: OpenRouter API calls             │
│ • git-info: Anthropic API calls               │ 
│ • actions: GitHub Actions analysis            │
└─────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────┐
│ NEW: claude_session_detector.py (OPTIONAL)     │
├─────────────────────────────────────────────────┤
│ • Detects if Claude Code is running            │
│ • Gets session_id if available                 │
│ • Sends metrics with session correlation       │
│ • Fails silently if Claude Code not available  │
└─────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────┐
│ EXISTING MONITORING STACK (unchanged)          │
├─────────────────────────────────────────────────┤
│ • Pushgateway (7101) receives metrics          │
│ • Prometheus (7100) stores time-series         │
│ • Grafana (7102) shows unified dashboard       │
└─────────────────────────────────────────────────┘
```

## 📦 **Integration Steps**

### **1. Add Helper to Repository**

```bash
# Add to your AI agent's requirements
echo "claude-code-sdk>=1.0.0" >> requirements.txt  # Optional dependency
pip install -r requirements.txt
```

### **2. Minimal Code Changes**

**Before (existing code works unchanged):**
```python
# doc-finder's existing LLM call
response = openrouter_client.post(...)
usage = response.json().get('usage', {})
self.telemetry_manager.update_llm_metrics(tokens=usage.get('total_tokens'))
```

**After (add 3 lines for session correlation):**
```python
# doc-finder's existing LLM call (UNCHANGED)
response = openrouter_client.post(...)
usage = response.json().get('usage', {})
self.telemetry_manager.update_llm_metrics(tokens=usage.get('total_tokens'))

# NEW: Optional session correlation 
from claude_session_detector import send_agent_metrics
send_agent_metrics(
    agent_name="doc-finder", 
    operation="search", 
    duration_ms=duration_ms,
    token_count=tokens,  # Total tokens (required)
    input_tokens=input_tokens,   # Optional if API provides it
    output_tokens=output_tokens,  # Optional if API provides it
    cost_usd=cost,
    model=model
)
# ☝️ This automatically detects session_id if Claude Code is running
```

## 🔧 **Integration Examples**

### **Doc-Finder (OpenRouter API)**

```python
# In llm_integration.py - MINIMAL CHANGES
import time
from claude_session_detector import send_agent_metrics  # NEW LINE

class OpenRouterClient:
    def _make_request(self, prompt: str, system_prompt: str = None):
        start_time = time.time()
        
        # EXISTING CODE (unchanged)
        response = client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        usage = response.json().get('usage', {})
        tokens_used = usage.get('total_tokens', 0)
        estimated_cost = tokens_used * 0.000002
        
        # EXISTING telemetry (unchanged)
        if self.telemetry_manager:
            self.telemetry_manager.update_llm_metrics(
                tokens_used=tokens_used,
                cost_usd=estimated_cost,
                model=self.model
            )
        
        # NEW: Session correlation (3 lines)
        send_agent_metrics(
            agent_name="doc-finder",
            operation="document_search", 
            duration_ms=duration_ms,
            token_count=tokens_used,
            cost_usd=estimated_cost,
            model=self.model,
            success=response.status_code == 200
        )
        
        return response  # Rest unchanged
```

### **Git-Info (Anthropic API)**

```python
# In git_info_manager.py - MINIMAL CHANGES  
from claude_session_detector import send_agent_metrics  # NEW LINE

class GitInfoManager:
    def _get_ai_response(self, prompt: str, model: str):
        start_time = time.time()
        
        # EXISTING Anthropic API call (unchanged)
        client = Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        tokens = response.usage.input_tokens + response.usage.output_tokens
        cost = self._calculate_cost(tokens, model)
        
        # NEW: Session correlation (3 lines)
        send_agent_metrics(
            agent_name="git-info",
            operation="commit_analysis",
            duration_ms=duration_ms, 
            token_count=tokens,
            cost_usd=cost,
            model=model
        )
        
        return response.content[0].text  # Rest unchanged
```

## 🚦 **Graceful Degradation**

**Key Feature: Non-breaking behavior**

```python
# If Claude Code not available:
session_info = get_claude_session_info()  
# Returns None, metrics sent with session_id="no-session"

# If Claude Code IS available:
session_info = get_claude_session_info()
# Returns ClaudeSessionInfo with actual session_id for correlation

# Metrics always sent regardless - correlation just better when Claude Code available
```

## 📊 **Expected Dashboard Results**

### **Without Session Correlation (current state)**
```
AI Agent Usage:
- doc-finder: 45 uses, unknown sessions  
- git-info: 23 uses, unknown sessions
- actions: 12 uses, unknown sessions
```

### **With Session Correlation (after integration)**  
```
AI Agent Usage:
- doc-finder: 45 uses, 8 Claude Code sessions + 37 standalone
- git-info: 23 uses, 15 Claude Code sessions + 8 standalone  
- actions: 12 uses, 3 Claude Code sessions + 9 standalone

Session Cross-Reference:
- Session abc123: Claude Code tools + doc-finder search + git-info analysis
- Session def456: Claude Code tools + doc-finder search
- Session ghi789: Claude Code tools only (no AI agents used)
```

## ✅ **Benefits of This Approach**

### **For AI Agent Developers:**
- ✅ **Minimal code changes** (3 lines per integration point)
- ✅ **Keep existing APIs** (OpenRouter, Anthropic, etc.)
- ✅ **Non-breaking** (works with/without Claude Code)
- ✅ **Optional dependency** (pip install only if you want metrics)

### **For Users:**
- ✅ **No setup required** for basic AI agent usage
- ✅ **Automatic correlation** if running Claude Code
- ✅ **Unified monitoring** of all development tools
- ✅ **Cost visibility** across all AI usage

### **For Monitoring:**
- ✅ **Session correlation** when possible
- ✅ **Unified dashboard** showing Claude Code + AI agents
- ✅ **Cost tracking** across all AI tools
- ✅ **Usage analytics** by session, user, time

## 🎯 **Implementation Priority**

### **Phase 1: Proof of Concept**
1. **Doc-finder integration** - Has existing telemetry, good test case
2. **Verify session detection** - Test session_id correlation
3. **Dashboard update** - Add AI agents panel

### **Phase 2: Scale to Other Agents**  
1. **Git-info integration** - Highest usage agent
2. **Actions integration** - Lower usage but completes picture
3. **Pattern documentation** - Guide for future agents

### **Phase 3: Advanced Features**
1. **Cost optimization insights** - Which agents most/least cost-effective
2. **Usage pattern analysis** - When are AI agents used vs Claude Code directly
3. **Model performance comparison** - Track success rates by model

---

**💡 Key Insight**: This approach respects existing AI agent architectures while adding optional monitoring capabilities. It's **additive, not disruptive** - exactly what's needed for broad adoption across the spacewalker repository.