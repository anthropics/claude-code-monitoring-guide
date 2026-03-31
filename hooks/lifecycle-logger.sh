#!/usr/bin/env bash
# hooks/lifecycle-logger.sh
#
# Claude Code hook script that captures lifecycle events and appends them
# as JSONL to data/lifecycle/events.jsonl.
#
# Receives hook JSON on stdin. Uses hook_event_name to determine event type.
# Dependencies: bash, jq (no DuckDB CLI required on host)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="${SCRIPT_DIR}/data/lifecycle"
JSONL_FILE="${DATA_DIR}/events.jsonl"

mkdir -p "$DATA_DIR"

# Read all of stdin (hook provides JSON)
INPUT_JSON="$(cat)"

EVENT_NAME=$(echo "$INPUT_JSON" | jq -r '.hook_event_name // empty')
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

case "$EVENT_NAME" in
  SessionStart)
    OUTPUT=$(echo "$INPUT_JSON" | jq -c --arg ts "$TIMESTAMP" '{
      event_type: "session_start",
      event_timestamp: $ts,
      session_id: .session_id,
      source: .source,
      model: .model,
      cwd: .cwd
    }')
    ;;
  UserPromptSubmit)
    OUTPUT=$(echo "$INPUT_JSON" | jq -c --arg ts "$TIMESTAMP" '{
      event_type: "user_prompt",
      event_timestamp: $ts,
      session_id: .session_id,
      prompt_text: (.prompt // "" | .[0:500]),
      detected_command: (
        if (.prompt // "" | test("^/[a-zA-Z]"))
        then (.prompt | split(" ")[0] | split("\n")[0])
        else null
        end
      )
    }')
    ;;
  PreToolUse)
    TOOL_NAME=$(echo "$INPUT_JSON" | jq -r '.tool_name // empty')
    case "$TOOL_NAME" in
      Skill)
        OUTPUT=$(echo "$INPUT_JSON" | jq -c --arg ts "$TIMESTAMP" '{
          event_type: "skill_invoke",
          event_timestamp: $ts,
          session_id: .session_id,
          skill_name: .tool_input.skill,
          skill_args: (.tool_input.args // null)
        }')
        ;;
      Agent)
        OUTPUT=$(echo "$INPUT_JSON" | jq -c --arg ts "$TIMESTAMP" '{
          event_type: "agent_invoke",
          event_timestamp: $ts,
          session_id: .session_id,
          agent_type: (.tool_input.subagent_type // "general-purpose"),
          subagent_model: (.tool_input.model // null),
          agent_prompt: (.tool_input.prompt // "" | .[0:500])
        }')
        ;;
      *)
        # Unexpected tool name for matched hook, skip
        exit 0
        ;;
    esac
    ;;
  SubagentStart)
    OUTPUT=$(echo "$INPUT_JSON" | jq -c --arg ts "$TIMESTAMP" '{
      event_type: "agent_start",
      event_timestamp: $ts,
      session_id: .session_id,
      agent_id: .agent_id,
      agent_type: .agent_type
    }')
    ;;
  SubagentStop)
    OUTPUT=$(echo "$INPUT_JSON" | jq -c --arg ts "$TIMESTAMP" '{
      event_type: "agent_stop",
      event_timestamp: $ts,
      session_id: .session_id,
      agent_id: .agent_id,
      agent_type: .agent_type,
      transcript_path: .agent_transcript_path
    }')
    ;;
  Stop)
    OUTPUT=$(echo "$INPUT_JSON" | jq -c --arg ts "$TIMESTAMP" '{
      event_type: "stop",
      event_timestamp: $ts,
      session_id: .session_id,
      last_message: (.last_assistant_message // "" | .[0:500])
    }')
    ;;
  SessionEnd)
    OUTPUT=$(echo "$INPUT_JSON" | jq -c --arg ts "$TIMESTAMP" '{
      event_type: "session_end",
      event_timestamp: $ts,
      session_id: .session_id,
      source: .source
    }')
    ;;
  *)
    # Unknown event, skip silently
    exit 0
    ;;
esac

# Atomic append: POSIX guarantees atomicity for writes < PIPE_BUF (4096 bytes on macOS)
echo "$OUTPUT" >> "$JSONL_FILE"
