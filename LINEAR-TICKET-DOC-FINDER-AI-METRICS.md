# Linear Ticket: AI Agent Metrics Integration - Doc-Finder Prototype

## 🎯 **Ticket Title**
**Extend doc-finder telemetry to integrate with Claude Code monitoring infrastructure**

## 📋 **Context & Why Doc-Finder**

We have a comprehensive Claude Code monitoring system tracking tool usage, bash commands, agents, MCP, and git operations. We've discovered 5+ AI agents in spacewalker that use LLMs but lack unified usage tracking.

**Why we picked doc-finder as the prototype:**
- ✅ Already has working `telemetry_manager.py` with LLM metrics
- ✅ Already captures token usage from OpenRouter API responses  
- ✅ Already has cost estimation logic
- ✅ Most complete existing implementation
- ✅ Lower risk prototype vs starting from scratch

**Our monitoring infrastructure:**
- Prometheus + Pushgateway + Grafana stack (ports 7100-7102)
- Breakthrough timestamp-based counter system for proper metric accumulation
- 5 production dashboards already working
- Hook system captures all Claude Code tool usage automatically

## 🎯 **Goal**

Create a working prototype that:
1. **Extends your existing telemetry** to send data to our monitoring stack
2. **Establishes patterns** we can copy to other AI agents (git-info, actions)
3. **Captures session/user correlation** for usage analytics
4. **Demonstrates unified AI agent dashboards**

## 📊 **Required Data Points**

Extend your current telemetry to capture:

**Core Metrics** (you already have some):
- `ai_agent_usage_total` - Counter of AI agent executions
- `ai_agent_tokens_total` - Token usage (input/output if available)
- `ai_agent_cost_usd_total` - Estimated cost in USD
- `ai_agent_duration_seconds` - Execution time

**Labels** (critical for correlation):
- `agent_name` - "doc-finder" 
- `model` - LLM model used ("llama-3.1-8b-instruct", etc.)
- `session_id` - Claude Code session (see correlation section)
- `user_id` - User identifier (see correlation section)
- `operation` - "search", "index", "analyze", etc.
- `success` - "true"/"false" for error tracking

## 🎯 **Session/User Correlation - LIGHTWEIGHT HELPER APPROACH**

**✅ The Solution:** Optional session detection helper that preserves your existing API

**Architecture: Keep OpenRouter + Add Optional Session Detection**
- ✅ **Non-breaking**: Your OpenRouter code stays unchanged
- ✅ **Optional integration**: 3-line addition for session correlation  
- ✅ **Graceful failure**: Works with/without Claude Code available
- ✅ **Unified monitoring**: Session correlation when possible, metrics always

**Implementation Pattern:**
```python
# Your existing OpenRouter call (UNCHANGED)
response = openrouter_client.post(...)
tokens = response.json().get('usage', {}).get('total_tokens', 0)

# NEW: Optional 3-line addition for monitoring
from claude_session_detector import send_agent_metrics
send_agent_metrics("doc-finder", "search", duration_ms, tokens, cost, model)
```

## 🏗️ **Technical Integration - LIGHTWEIGHT HELPER APPROACH**

**RECOMMENDED: Keep OpenRouter + Add Session Detection Helper**

**Your Current Implementation (KEEP THIS):**
```python
# In llm_integration.py - NO CHANGES TO CORE LOGIC
response = client.post(
    f"{self.base_url}/chat/completions",
    headers={"Authorization": f"Bearer {self.api_key}"},
    json=payload
)
usage = response.json().get('usage', {})
tokens_used = usage.get('total_tokens', 0)
estimated_cost = tokens_used * 0.000002

# Your existing telemetry (KEEP THIS)
if self.telemetry_manager:
    self.telemetry_manager.update_llm_metrics(
        tokens_used=tokens_used,
        cost_usd=estimated_cost,
        model=self.model
    )
```

**NEW: Add 3-Line Session Detection Helper**
```python
# Add this import at the top
from claude_session_detector import send_agent_metrics

# Add these 3 lines after your existing telemetry
send_agent_metrics(
    agent_name="doc-finder",
    operation="document_search",  # or "analyze", "summarize", etc.
    duration_ms=int((time.time() - start_time) * 1000),
    token_count=tokens_used,  # Total tokens (required)
    
    # OPTIONAL: Token breakdown (if your API provides it)
    input_tokens=usage.get('prompt_tokens', 0),      # Input tokens if available
    output_tokens=usage.get('completion_tokens', 0), # Output tokens if available
    
    cost_usd=estimated_cost,
    model=self.model,
    success=response.status_code == 200
)
```

**✅ Benefits of Helper Approach:**
- **Minimal Changes**: Only 3 lines added to existing code
- **Keep Your API**: OpenRouter integration stays unchanged
- **Non-Breaking**: Works with/without Claude Code running
- **Optional**: Can be disabled/removed without affecting functionality
- **Session Correlation**: Automatic when Claude Code available

## 🤔 **Token Detail Question for You**

**What we already know you have:**
- ✅ **Total tokens**: Your telemetry shows `usage.total_tokens`
- ✅ **Cost calculation**: You already calculate costs per model
- ✅ **Model tracking**: You know which models you're using

**What we'd love to have (if your OpenRouter API provides it):**
- ❓ **Input tokens**: Does OpenRouter response include `prompt_tokens` or `input_tokens`?
- ❓ **Output tokens**: Does OpenRouter response include `completion_tokens` or `output_tokens`?

**Why we want this:**
- Dashboard shows "doc-finder used 892 total tokens (650 input + 242 output)"
- Better cost analysis (input vs output often have different pricing)
- More detailed usage analytics

**If you can't get input/output breakdown:** No problem! Just total tokens works fine.

## 📈 **Success Criteria**

**Phase 1: Helper Integration**
- [ ] Add claude_session_detector helper to doc-finder (3-line change)
- [ ] Verify OpenRouter code remains unchanged and working
- [ ] Session correlation working when Claude Code is available
- [ ] Graceful degradation when Claude Code not available

**Phase 2: Metrics and Dashboard**
- [ ] Metrics appear in Prometheus at http://localhost:7100
- [ ] Data shows in our Grafana dashboards at http://localhost:7102
- [ ] New "AI Agents" dashboard panel shows doc-finder usage
- [ ] Session correlation visible: same session_id in Claude Code + doc-finder metrics

**Phase 3: Pattern Documentation**
- [ ] Helper integration pattern documented for other agents
- [ ] Integration guide created for easy adoption by git-info, actions, etc.
- [ ] Unified AI agent monitoring dashboard showing all agents

## 🤝 **Collaboration Approach - LIGHTWEIGHT HELPER INTEGRATION**

**What we need from you:**
1. **Current OpenRouter implementation walkthrough** - How your existing API calls work
2. **Helper integration assessment** - Where to add the 3-line session detection helper
3. **Testing collaboration** - Help verify session correlation works with your existing telemetry
4. **Prototype implementation** - Add helper without changing core OpenRouter logic

**What we'll provide:**
- `claude_session_detector.py` helper library (ready to use)
- Access to our monitoring stack for testing (ports 7100-7102)
- Complete integration guide with examples
- Dashboard creation showing doc-finder in unified AI agent panel
- Pattern documentation for scaling to other agents

**🎯 Major Advantages**: 
- **Minimal risk**: Only 3 lines added to existing code
- **Keep existing architecture**: OpenRouter API calls unchanged
- **Optional dependency**: Can be removed without breaking anything
- **Automatic correlation**: Session detection when Claude Code available

## 🧪 **Testing Strategy - HELPER INTEGRATION**

**Prerequisites:**
1. **Optional**: Install Claude Code CLI: `npm install -g @anthropic-ai/claude-code` (for session correlation)
2. **Required**: Copy `claude_session_detector.py` to doc-finder repository
3. **Required**: Add `claude-code-sdk` to requirements.txt (gracefully fails if not installed)

**Development Testing:**
1. **Standalone Test**: Run doc-finder without Claude Code (should work normally)
2. **Helper Integration Test**: Add 3-line helper, verify metrics sent to pushgateway
3. **Session Detection Test**: Run doc-finder with Claude Code available, verify session_id captured
4. **Metrics Flow Test**: `curl http://localhost:7101/metrics | grep ai_agent`
5. **Dashboard Test**: View new AI agent panel in Grafana

**Session Correlation Validation:**
1. **Without Claude Code**: Run doc-finder standalone, verify metrics with `session_id="no-session"`
2. **With Claude Code**: 
   - Start Claude Code session: `claude`
   - Use some Claude Code tools
   - Run doc-finder in same terminal  
   - Verify same `session_id` in both Claude Code and doc-finder metrics
3. **Dashboard Correlation**: Confirm linked usage visible in monitoring dashboard

## 📚 **Reference Materials**

**Our Current System:**
- Main monitoring repo: `/Users/chadwalters/source/work/claude-code-monitoring-guide/`
- Hook system: `production-tool-hook.sh` (shows timestamp pattern)
- Pushgateway integration examples
- 5 working dashboards for reference

**Your Current System:**
- Telemetry manager: `scripts/doc-finder/src/core/telemetry.py`
- LLM integration: `scripts/doc-finder/src/ai/llm_integration.py`
- Cost engine: Already implemented

## 🎯 **Deliverables - UPDATED for SDK Approach**

1. **SDK Migration Analysis** - Assessment of OpenRouter → Claude Code SDK migration
2. **Prototype Implementation** - Working doc-finder with SDK integration + monitoring
3. **Session Correlation Validation** - Demonstrate automatic session correlation working
4. **API Key Elimination** - Proof that separate API keys are no longer needed
5. **Pattern Documentation** - SDK integration guide for other AI agents  
6. **Dashboard Integration** - Doc-finder usage appears in unified AI agent dashboard

**📋 Success Metric**: Same `session_id` visible in both Claude Code tool metrics and doc-finder AI agent metrics, proving unified session tracking.

## 💡 **Future Vision**

Once doc-finder prototype works, we'll extend the pattern to:
- `git-info` (Claude-based commit messages, PR analysis) - highest usage
- `actions` (GitHub Actions failure analysis) - limited usage
- Other AI agents as they're developed

This creates unified AI agent monitoring across all development tools.

---

**Priority:** High  
**Estimate:** 1-2 sprints depending on session correlation complexity  
**Dependencies:** Access to Claude Code monitoring infrastructure  
**Success Metric:** Working AI agent dashboard showing doc-finder usage correlated with Claude Code sessions