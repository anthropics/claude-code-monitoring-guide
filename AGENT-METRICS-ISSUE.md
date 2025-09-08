# Agent Metrics Issue Analysis

## 🚨 Problem Statement

The Agent Analytics dashboard shows **historical task counts**, not **current active session data**. User reports 3 active windows for 1.5 hours, but dashboard shows disconnected historical metrics.

## 📊 Current Data vs Reality

### What User Has RIGHT NOW:
- **3 Claude windows open**
- **Running for 1.5 hours each**
- **Active agent sessions in progress**
- **5 Claude processes running** (verified with `ps aux`)

### What Dashboard Shows:
- **Total Agent Tasks: 7** (historical count)
- **Average Task Duration: No data**
- **Avg Sub-tools per Task: No data**  
- **Task Success Rate: No data**
- **Agent Types**: gt-restack-expert(3), general-purpose(2), pr-review-expert(1), pr-review-analyzer(1)

## 🔍 Data Analysis

### Current Metrics in Prometheus ✅
```bash
# Historical task completion counts:
claude_custom_agent_usage_total{agent_type="gt-restack-expert"} = 3
claude_custom_agent_usage_total{agent_type="general-purpose"} = 2  
claude_custom_agent_usage_total{agent_type="pr-review-expert"} = 1
claude_custom_agent_usage_total{agent_type="pr-review-analyzer"} = 1

# Total: 7 historical tasks (matches dashboard)
```

### What's Missing ❌
- **Active session tracking**: No metrics for currently running agents
- **Session duration**: No timing for how long current sessions have been active
- **Real-time status**: No indication of what's happening now vs what happened before

## 🎯 Fundamental Issue

**The dashboard shows "what happened" not "what's happening"**

### Historical vs Real-time Metrics:
- ✅ **Historical**: "How many times did we use gt-restack-expert?" (3 times)
- ❌ **Real-time**: "Is gt-restack-expert running now?" (unknown)
- ❌ **Duration**: "How long has the current session been running?" (unknown)
- ❌ **Status**: "Is the agent making progress or stuck?" (unknown)

## 💡 What Useful Agent Monitoring Would Look Like

### Current Session Tracking:
```bash
# Active agent sessions (what we need):
claude_active_agent_sessions{agent_type="gt-restack-expert", session_id="abc123"} 1
claude_session_duration_seconds{agent_type="gt-restack-expert", session_id="abc123"} 5400  # 1.5 hours
claude_session_status{agent_type="gt-restack-expert", session_id="abc123", status="running"} 1

# Progress tracking:
claude_agent_tools_used_current_session{agent_type="gt-restack-expert", session_id="abc123"} 15
claude_agent_last_activity_timestamp{agent_type="gt-restack-expert", session_id="abc123"} 1757250000
```

### Real-time Dashboard Panels:
- **Active Sessions Now**: 3 (not 7 historical tasks)
- **Longest Running Session**: 1.5 hours
- **Tools Used This Session**: 15 
- **Agent Status**: Working/Idle/Stuck
- **Current Task Progress**: "Analyzing codebase..." (status message)

## 🔧 Technical Requirements for Fix

### Metrics We Need to Capture:
1. **Session Start/End Events**: When agents begin/complete
2. **Heartbeat Metrics**: Periodic updates showing agent is still active  
3. **Progress Indicators**: What the agent is currently doing
4. **Resource Usage**: CPU/memory per active agent session
5. **Tool Invocation Tracking**: Real-time tool usage within session

### Hook Integration Points:
- **Agent Launch Hook**: Capture session start
- **Tool Use Hooks**: Track progress within session
- **Heartbeat Hook**: Periodic "still alive" signals
- **Session End Hook**: Mark completion with duration

## 📋 Current vs Needed Architecture

### Current (Broken):
```
Agent Task Completes → Hook → Pushgateway → Prometheus → Dashboard
                               ↓
                    Shows: "7 historical tasks"
                    Missing: "What's active now?"
```

### Needed (Working):
```
Agent Session Active → Heartbeat Hook → Pushgateway → Prometheus → Dashboard
       ↓                      ↓                          ↓              ↓
   Every 30s            Session metrics          Active tracking    Real-time view
   
Shows: "3 active sessions, running 1.5hrs each"
```

## 🎯 Action Required

### Immediate:
1. **Remove misleading agent dashboards** (like we did with Linear)
2. **Document this as another metrics architecture issue**
3. **Stop trying to fix display when data model is wrong**

### Medium-term:
1. **Design proper session tracking architecture**
2. **Implement heartbeat/progress metrics**
3. **Build dashboards after data is correct**

## 💭 Pattern Recognition

**Same issue as Linear multiplication problem:**
- We have some data capture working
- The captured data doesn't represent what users want to monitor
- Dashboard tweaks can't fix fundamental data model misalignment
- Need to fix metrics before visualization

**Core Learning**: Monitor systems should reflect **current state and activity**, not just **historical event counts**.

---

**Status**: Agent monitoring foundation exists but captures wrong data type
**Next**: Design session-based metrics architecture before building dashboards