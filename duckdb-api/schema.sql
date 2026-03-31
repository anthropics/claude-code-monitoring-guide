CREATE TABLE IF NOT EXISTS lifecycle_events (
    event_type      VARCHAR NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    session_id      VARCHAR NOT NULL,
    source          VARCHAR,
    model           VARCHAR,
    cwd             VARCHAR,
    prompt_text     VARCHAR,
    detected_command VARCHAR,
    skill_name      VARCHAR,
    skill_args      VARCHAR,
    agent_id        VARCHAR,
    agent_type      VARCHAR,
    subagent_model  VARCHAR,
    agent_prompt    VARCHAR,
    transcript_path VARCHAR,
    last_message    VARCHAR
);
